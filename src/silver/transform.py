from __future__ import annotations

import os
import re
import sys
import pandas as pd
import awswrangler as wr

# Assuming configuration is handled via your common config module
from src.common.config import config

DATASET = "desynpuf"
GLUE_BRONZE_DB = config.glue_database
GLUE_SILVER_DB = config.glue_silver_db_name  # Target database for Athena queries

CHRONIC_FLAGS = {
    "sp_alzhdmta": "alzheimers_or_dementia",
    "sp_chf": "heart_failure",
    "sp_chrnkidn": "chronic_kidney_disease",
    "sp_cncr": "cancer",
    "sp_copd": "copd",
    "sp_depressn": "depression",
    "sp_diabetes": "diabetes",
    "sp_ischmcht": "ischemic_heart_disease",
    "sp_osteoprs": "osteoporosis",
    "sp_ra_oa": "rheumatoid_or_osteoarthritis",
    "sp_strketia": "stroke_tia",
}

DATE_SUFFIX_RE = re.compile(r"_dt$")
DGNS_RE = re.compile(r"^icd9_dgns_cd_\d+$")

# ---------------------------------------------------------------------------
# Pure Pandas Transform Helpers
# ---------------------------------------------------------------------------
def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Convert YYYYMMDD (numeric/string) to real datetime for columns ending in _dt."""
    for c in [c for c in df.columns if DATE_SUFFIX_RE.search(c)]:
        df[c] = pd.to_datetime(df[c].astype(str), format="%Y%m%d", errors="coerce")
    return df


def cast_amounts(df: pd.DataFrame, extra: list[str] | None = None) -> pd.DataFrame:
    """Cast currency/numeric columns to float for efficient silver analytical layers."""
    cols = {c for c in df.columns if "amt" in c}
    cols.update(c for c in (extra or []) if c in df.columns)
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")
    return df


def decode_chronic_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Map string codes '1' and '2' into clean Booleans."""
    for raw, friendly in CHRONIC_FLAGS.items():
        if raw in df.columns:
            s = df[raw].astype(str).str.strip()
            df[f"has_{friendly}"] = s.map({"1": True, "2": False})
            df.drop(columns=[raw], inplace=True)
    return df


def unpivot_diagnoses(df: pd.DataFrame, claim_type: str) -> pd.DataFrame | None:
    """Explode wide ICD-9 columns vertically into (ids, claim_type, dgns_seq, icd9_code)."""
    dgns_cols = [c for c in df.columns if DGNS_RE.match(c)]
    id_cols = [c for c in ["desynpuf_id", "clm_id"] if c in df.columns]
    
    if "admtng_icd9_dgns_cd" in df.columns:
        dgns_cols.append("admtng_icd9_dgns_cd")
        
    if not dgns_cols or not id_cols:
        return None

    # Melt (unpivot) the wide table to long format
    melted = df.melt(id_vars=id_cols, value_vars=dgns_cols, var_name="raw_col", value_name="icd9_code")
    melted = melted.dropna(subset=["icd9_code"])
    melted["icd9_code"] = melted["icd9_code"].astype(str).str.strip()
    melted = melted[melted["icd9_code"] != ""]
    
    if melted.empty:
        return None

    # Extract sequence number (admitting maps to 0, otherwise trailing digits)
    melted["dgns_seq"] = melted["raw_col"].apply(
        lambda x: 0 if x == "admtng_icd9_dgns_cd" else int(x.split("_")[-1])
    )
    melted["claim_type"] = claim_type
    
    return melted[id_cols + ["claim_type", "dgns_seq", "icd9_code"]]


# ---------------------------------------------------------------------------
# Per-Entity Cleaning Core Loops
# ---------------------------------------------------------------------------
def clean_beneficiary(df: pd.DataFrame) -> pd.DataFrame:
    df = parse_dates(df)
    money = [c for c in df.columns if c.startswith(("medreimb_", "benres_", "pppymt_"))]
    df = cast_amounts(df, extra=money)
    df = decode_chronic_flags(df)
    if "bene_sex_ident_cd" in df.columns:
        df["sex"] = df["bene_sex_ident_cd"].astype(str).str.strip().map({"1": "M", "2": "F"})
    
    for c in [c for c in df.columns if c.endswith("_mons") or c == "plan_cvrg_mos_num"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype("int64")
        
    df["benefit_year"] = df["clm_id"].str.slice(0, 4) if "clm_id" in df.columns else "9999" # Fallback mapping
    return df.drop_duplicates(subset=["desynpuf_id", "benefit_year"])


def clean_claim(df: pd.DataFrame, entity: str) -> tuple[pd.DataFrame, pd.DataFrame | None]:
    diagnoses = unpivot_diagnoses(df, entity)
    df = parse_dates(df)
    df = cast_amounts(df, extra=["clm_utlztn_day_cnt"])
    
    # Drop wide code columns to keep the base tables clean
    wide_cols = [c for c in df.columns if DGNS_RE.match(c) or c in ("admtng_icd9_dgns_cd",)]
    df.drop(columns=wide_cols, inplace=True, errors="ignore")
    
    if "clm_id" in df.columns:
        df.drop_duplicates(subset=["clm_id"], inplace=True)
    return df, diagnoses


def clean_pde(df: pd.DataFrame) -> pd.DataFrame:
    df = parse_dates(df)
    df = cast_amounts(df)
    for c in ("qty_dspnsd_num", "days_suply_num"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")
    if "pde_id" in df.columns:
        df.drop_duplicates(subset=["pde_id"], inplace=True)
    return df

# ---------------------------------------------------------------------------
# S3 Streaming Orchestrator
# ---------------------------------------------------------------------------
def process_and_catalog_entity(entity: str, entity_type: str) -> pd.DataFrame | None:
    """Reads Bronze from S3 using catalog schema metadata, transforms, and saves to Silver."""
    print(f"\n Processing entity: '{entity}'...")
    
    try:
        # Stream the data in memory-safe chunks directly from Bronze S3 path via Catalog paths
        chunks = wr.athena.read_sql_query(
            sql=f'SELECT * FROM "{GLUE_BRONZE_DB}"."{entity}"',
            database=GLUE_BRONZE_DB,
            chunksize=100_000,
            s3_output= f"s3://{config.bucket}/athena-results/"  # <-- ADD THIS LINE
        )
    except Exception as e:
        print(f" [SKIP] Could not pull table '{entity}' from Glue database '{GLUE_BRONZE_DB}': {e}")
        return None

    silver_s3_path = f"s3://{config.bucket}/silver/{DATASET}/{entity}/"
    first_chunk = True
    all_diagnoses = []

    for chunk_df in chunks:
        if chunk_df.empty:
            continue
            
        # Router mapping to cleaner functions
        if entity_type == "beneficiary":
            cleaned_df = clean_beneficiary(chunk_df)
            dgns_df = None
        elif entity_type == "claim":
            cleaned_df, dgns_df = clean_claim(chunk_df, entity)
            if dgns_df is not None:
                all_diagnoses.append(dgns_df)
        elif entity_type == "pde":
            cleaned_df = clean_pde(chunk_df)
            dgns_df = None

        # Write clean data out to Silver S3 as compact Parquet, instantly syncing to the Silver Catalog
        wr.s3.to_parquet(
            df=cleaned_df,
            path=silver_s3_path,
            dataset=True,
            database=GLUE_SILVER_DB,
            table=f"silver_{entity}",
            mode="append" if not first_chunk else "overwrite"
        )
        first_chunk = False

    print(f" [SUCCESS] Table 'silver_{entity}' written to {silver_s3_path} and logged.")
    
    # Return accumulated diagnostic frames if any were extracted
    if all_diagnoses:
        return pd.concat(all_diagnoses, ignore_index=True)
    return None


def main() -> int:
    # Ensure the Silver database exists (idempotent)
    try:
        wr.catalog.create_database(name=GLUE_SILVER_DB, description="Cleaned transactional silver layer.", exist_ok=True)
    except Exception as e:
        print(f" [WARN] Could not ensure Glue database '{GLUE_SILVER_DB}': {e}")

    # 1. Process base layers
    process_and_catalog_entity("beneficiary", "beneficiary")
    process_and_catalog_entity("pde", "pde")

    # 2. Process claims layers & stack wide diagnostics
    claims_entities = ["inpatient", "outpatient", "carrier"]
    collected_dgns = []
    
    for entity in claims_entities:
        dgns_extracted = process_and_catalog_entity(entity, "claim")
        if dgns_extracted is not None:
            collected_dgns.append(dgns_extracted)

    # 3. Save unpivoted diagnoses out as its own structured relational entity
    if collected_dgns:
        print("\nSaving unpivoted healthcare claims diagnoses table...")
        final_dgns_df = pd.concat(collected_dgns, ignore_index=True)
        wr.s3.to_parquet(
            df=final_dgns_df,
            path=f"s3://{config.bucket}/silver/{DATASET}/claim_diagnoses/",
            dataset=True,
            database=GLUE_SILVER_DB,
            table="silver_claim_diagnoses",
            mode="overwrite"
        )
        print(" [SUCCESS] Relational table 'silver_claim_diagnoses' is now live in Athena.")
        
    return 0

if __name__ == "__main__":
    sys.exit(main())



    alright good i want to make a post on linkedin about the progress of this project, how i ceated the silver which is firstly   after ingesting the data into bronze folder in the s3 bucket and partitioned the files, created a database and catalog in aws glue and created a crawler which was provisioned using terraform also done by configuring the iam role policy with the environment vscode. then athena pick up from here which i was able to analyze the bronze table and coul query and see the data as it is, and roles and necessary transformations that needs to be done. I created the transformation silver layer through this step Locating: The code uses database names from a configuration module (config.glue_database) and dynamically inserts the table name (entity) into a standard SQL string.Extracting: awswrangler submits this SQL query to AWS Athena, which looks up the file locations in the Glue Data Catalog and streams the data back to the script in 100,000-row chunks.Transforming: Each chunk is modified in-memory using Pandas functions to clean dates, numbers, booleans, and tables.Loading: awswrangler converts the cleaned data chunks into Parquet files, writes them directly to the destination S3 path (silver_s3_path), and updates the target Glue Database (GLUE_SILVER_DB) so the new table is instantly queryable. these are what i noticed while querying the silver layer that needs transformation; Date Standardization (parse_dates), Numeric and Currency Casting (cast_amounts), Chronic Condition Indicator Mapping (decode_chronic_flags)
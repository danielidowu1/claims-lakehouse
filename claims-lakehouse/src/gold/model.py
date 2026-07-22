"""
Gold layer: build the analytics-ready star schema from silver.

Target model:
    fact_claims        - one row per claim line
    dim_beneficiary    - demographics, enrollment, chronic-condition flags
    dim_provider       - provider attributes
    dim_diagnosis      - ICD-10 lookup
    dim_date           - calendar dimension

Aggregate marts (the metrics defined in docs/objectives.md):
    - pbpm                        cost per beneficiary per month
    - spend_by_claim_type         inpatient / outpatient / carrier / drug
    - cost_concentration          top-10% share of total spend
    - admissions_per_1000
    - readmission_rate_30d
    - avg_length_of_stay
    - condition_prevalence
    - cost_by_condition_count
    - drug_spend_pmpm
    - cost_util_by_age_sex_region

Scaffold only — contributions welcome. Each mart above is a well-scoped PR.

Usage:
    python -m src.gold.model
"""
from __future__ import annotations

import sys

from src.common.config import config


def build() -> int:
    print("[gold] building star schema...")
    # TODO(contributors): read silver Parquet
    # TODO: construct dim_* tables with surrogate keys (incl. chronic-condition flags)
    # TODO: construct fact_claims referencing the dimensions
    # TODO: build the aggregate marts listed in the module docstring / docs/objectives.md
    # TODO: register tables in the Glue Data Catalog for Athena
    print(f"[gold] target: s3://{config.bucket}/{config.gold_prefix}/ (not yet implemented)")
    print("[gold] scaffold only — see TODOs and docs/objectives.md.")
    return 0


if __name__ == "__main__":
    sys.exit(build())

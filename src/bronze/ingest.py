from __future__ import annotations

import datetime as dt
import pathlib
import sys

import boto3
from boto3.s3.transfer import TransferConfig

# Assuming configuration is handled via your common config module
from src.common.config import config

DATASET = "desynpuf"

# THE INDUSTRY STANDARD ROUTER: Maps keywords in filenames to clean database table directories
FILE_ROUTES: dict[str, str] = {
    "beneficiary_summary": "beneficiary",
    "inpatient_claims": "inpatient",
    "outpatient_claims": "outpatient",
    "carrier_claims": "carrier",
    "prescription_drug_events": "pde",
}

def route_file_to_entity(filename: str) -> str | None:
    """Analyze filename to determine its matching database entity."""
    name_lower = filename.lower()
    for keyword, entity in FILE_ROUTES.items():
        if keyword in name_lower:
            return entity
    return None

def discover_files(raw_dir: str) -> list[pathlib.Path]:
    """Find all source data files sitting in the local raw directory."""
    root = pathlib.Path(raw_dir)
    if not root.exists():
        print(f"[bronze] raw dir '{raw_dir}' not found. Check local paths.")
        return []
    # Grabs all csv or txt data files across the directory tree
    files = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in {".csv", ".txt"}]
    return files

def upload(files: list[pathlib.Path], execution_date: str | None = None) -> None:
    """Process file collection and stream them into clean, structured S3 targets."""
    load_date = execution_date or dt.date.today().isoformat()

    # Optimized for handling large CMS healthcare claims files efficiently
    transfer_config = TransferConfig(
        multipart_threshold=1024 * 1024 * 100,  # 100 MB
        max_concurrency=10,
        multipart_chunksize=1024 * 1024 * 50,  # 50 MB
        use_threads=True,
    )

    s3 = boto3.client("s3", region_name=config.region)
    failed_files = []
    skipped_count = 0
    uploaded_count = 0
    
    print(f"\n Processing batch of {len(files)} files found locally...")

    for f in files:
        # 1. Dynamically find the proper folder destination
        entity_name = route_file_to_entity(f.name)
        
        # Guardrail: Prevent unknown file layouts from blending into your clean tables
        if not entity_name:
            print(f" [SKIP] Could not safely identify entity for: {f.name}")
            skipped_count += 1
            continue

        # 2. Structure the clean Hive-partitioned path: entity first, partition second!
        key = f"{config.bronze_prefix}/{DATASET}/{entity_name}/load_date={load_date}/{f.name}"
        print(f" Routing: {f.name} s3://{config.bucket}/{key}")

        try: 
            s3.upload_file(
                str(f),
                config.bucket,
                key,
                Config=transfer_config,
                ExtraArgs={"Metadata": {"source-file": f.name, "load-date": load_date}},
            )
            uploaded_count += 1
        except Exception as e:
            print(f" [ERROR] Failed uploading {f.name}: {e}")
            failed_files.append(f.name)

    print(f"\n Batch complete. Uploaded: {uploaded_count} | Skipped: {skipped_count} | Failures: {len(failed_files)}")

    if failed_files:
        sys.exit(1)

def main() -> int:
    files = discover_files(config.raw_dir)
    if not files:
        print("[bronze] No files discovered. Drop your files into your data/raw/ directory first.")
        return 1
    upload(files)
    return 0

if __name__ == "__main__":
    sys.exit(main())

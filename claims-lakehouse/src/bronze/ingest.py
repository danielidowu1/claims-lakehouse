"""
Bronze layer: land raw CMS synthetic claims files into S3 as-is,
tagged with load metadata (source file + load date partition).

Usage:
    python -m src.bronze.ingest

Reads local files from RAW_DATA_DIR (see data/raw/README.md for how to
fetch them) and uploads them under s3://<bucket>/bronze/<dataset>/load_date=YYYY-MM-DD/.
Nothing is transformed here — that's the whole point of bronze.
"""
from __future__ import annotations

import datetime as dt
import pathlib
import sys

import boto3

from boto3.s3.transfer import TransferConfig

from src.common.config import config

DATASET = "desynpuf"  # change to "rif" if using the Synthea/RIF dataset


def discover_files(raw_dir: str) -> list[pathlib.Path]:
    
    root = pathlib.Path(raw_dir)
    if not root.exists():
        print(f"[bronze] raw dir '{raw_dir}' not found. See data/raw/README.md.")
        return []
    files = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in {".csv", ".txt"}]
    return files


def upload(files: list[pathlib.Path], execution_date: str | None = None) -> None:
    

    # Ensure idempotency by allowing a locked-in date
    load_date = execution_date or dt.date.today().isoformat()

    # Optimize for large CMS files
    transfer_config = TransferConfig(
        multipart_threshold=1024 * 1024 * 100,  # 100 MB
        max_concurrency=10,
        multipart_chunksize=1024 * 1024 * 50,  # 50 MB
        use_threads=True,
    )

    s3 = boto3.client("s3", region_name=config.region)
    failed_files = []
    
    for f in files:
        key = f"{config.bronze_prefix}/{DATASET}/load_date={load_date}/{f.name}"
        print(f"[bronze] uploading {f.name} -> s3://{config.bucket}/{key}")

        # Handle network/upload errors gracefully
        try: 
            s3.upload_file(
                str(f),
                config.bucket,
                key,
                Config=transfer_config,
                ExtraArgs={"Metadata": {"source-file": f.name, "load-date": load_date}},
            )
        except Exception as e:
            print(f"[ERROR] failed to upload {f.name}: {e}")
            failed_files.append(f.name)

    if failed_files:
        print(f"[bronze] completed with failures. Failedfiles:{failed_files}")
        sys.exit(1)


def main() -> int:
    files = discover_files(config.raw_dir)
    if not files:
        print("[bronze] no files to ingest. Drop CMS files into data/raw/ first.")
        return 1
    upload(files)
    return 0


if __name__ == "__main__":
    sys.exit(main())

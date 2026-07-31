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

from src.common.config import config

DATASET = "desynpuf"  # change to "rif" if using the Synthea/RIF dataset


def discover_files(raw_dir: str) -> list[pathlib.Path]:
    root = pathlib.Path(raw_dir)
    if not root.exists():
        print(f"[bronze] raw dir '{raw_dir}' not found. See data/raw/README.md.")
        return []
    files = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in {".csv", ".txt"}]
    return files


def upload(files: list[pathlib.Path]) -> None:
    load_date = dt.date.today().isoformat()
    s3 = boto3.client("s3", region_name=config.region)
    for f in files:
        key = f"{config.bronze_prefix}/{DATASET}/load_date={load_date}/{f.name}"
        print(f"[bronze] uploading {f.name} -> s3://{config.bucket}/{key}")
        s3.upload_file(
            str(f),
            config.bucket,
            key,
            ExtraArgs={"Metadata": {"source-file": f.name, "load-date": load_date}},
        )
    print(f"[bronze] done. {len(files)} file(s) landed for load_date={load_date}.")


def main() -> int:
    files = discover_files(config.raw_dir)
    if not files:
        print("[bronze] no files to ingest. Drop CMS files into data/raw/ first.")
        return 1
    upload(files)
    return 0


if __name__ == "__main__":
    sys.exit(main())

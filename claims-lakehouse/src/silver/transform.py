"""
Silver layer: read raw bronze data, clean and conform it, write partitioned Parquet.

This is intentionally left as a guided scaffold — a great place for contributors
to jump in. Open a PR implementing any of the TODOs below.

Usage:
    python -m src.silver.transform
"""
from __future__ import annotations

import sys

from src.common.config import config


def transform() -> int:
    print("[silver] starting silver transforms...")

    # TODO(contributors): read bronze files (from S3 or local) into pandas/pyarrow
    # TODO: standardize column names and data types
    # TODO: parse dates, validate ICD / HCPCS codes
    # TODO: deduplicate claims (define the dedup key per claim type)
    # TODO: join claims to the beneficiary summary
    # TODO: write partitioned Parquet to s3://{bucket}/{silver}/...
    print(f"[silver] target: s3://{config.bucket}/{config.silver_prefix}/ (not yet implemented)")

    print("[silver] scaffold only — see TODOs. Contributions welcome!")
    return 0


if __name__ == "__main__":
    sys.exit(transform())

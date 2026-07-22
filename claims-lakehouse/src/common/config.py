"""Shared configuration, loaded from environment / .env."""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    region: str = os.getenv("AWS_REGION", "us-east-1")
    bucket: str = os.getenv("LAKE_BUCKET", "your-claims-lakehouse-bucket")
    glue_database: str = os.getenv("GLUE_DATABASE", "claims_lakehouse")
    raw_dir: str = os.getenv("RAW_DATA_DIR", "data/raw")

    # medallion prefixes within the bucket
    bronze_prefix: str = "bronze"
    silver_prefix: str = "silver"
    gold_prefix: str = "gold"


config = Config()

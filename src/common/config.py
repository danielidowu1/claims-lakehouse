"""Shared configuration, loaded from environment / .env."""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    region: str = os.getenv("AWS_REGION", "${AWS_REGION}")
    bucket: str = os.getenv("LAKE_BUCKET", "${LAKE_BUCKET}")
    glue_database: str = os.getenv("GLUE_DATABASE", "${GLUE_DATABASE}")
    glue_silver_db_name: str = os.getenv("GLUE_SILVER_DB_NAME", "${GLUE_SILVER_DB_NAME}")
    glue_gold_db_name: str = os.getenv("GLUE_GOLD_DB_NAME", "${GLUE_GOLD_DB_NAME}")
    raw_dir: str = os.getenv("RAW_DATA_DIR", "data/raw")

    # medallion prefixes within the bucket
    bronze_prefix: str = "bronze"
    silver_prefix: str = "silver"
    gold_prefix: str = "gold"


config = Config()

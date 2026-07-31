"""Smoke tests — keep CI green from day one, give contributors a template."""
from src.bronze import ingest
from src.common.config import config


def test_config_defaults_present():
    assert config.bronze_prefix == "bronze"
    assert config.silver_prefix == "silver"
    assert config.gold_prefix == "gold"


def test_discover_files_handles_missing_dir():
    # Should return an empty list, not raise, when the dir is absent.
    assert ingest.discover_files("does/not/exist") == []

.PHONY: help install lint test bronze silver gold

help:
	@echo "install  - install dependencies"
	@echo "lint     - run ruff"
	@echo "test     - run pytest"
	@echo "bronze   - run bronze ingestion"
	@echo "silver   - run silver transforms"
	@echo "gold     - run gold modeling"

install:
	pip install -r requirements.txt

lint:
	ruff check src tests

test:
	pytest -q

bronze:
	python -m src.bronze.ingest

silver:
	python -m src.silver.transform

gold:
	python -m src.gold.model

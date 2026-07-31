# Raw data (not committed)

Data files are **not** stored in git. Fetch them locally and drop them here.

## Default: CMS DE-SynPUF (start with sample 1)

1. Go to the [CMS DE-SynPUF page](https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-claims-synthetic-public-use-files/cms-2008-2010-data-entrepreneurs-synthetic-public-use-file-de-synpuf).
2. Download **Sample 1** files (Beneficiary Summary, Inpatient, Outpatient, Carrier, PDE).
3. Unzip and place the `.csv` files in this folder.

## Alternative: Synthea/RIF dataset

Download from the [CMS Synthetic Enrollment, FFS Claims & PDE collection](https://data.cms.gov/collection/synthetic-medicare-enrollment-fee-for-service-claims-and-prescription-drug-event)
and place the extracted files here.

Then run: `python -m src.bronze.ingest`

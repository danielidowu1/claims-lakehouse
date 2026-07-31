# Project Objectives

## Why explore this data?

Medicare claims data captures *who* received care, *what* was done, *when*, and
*how much it cost*. Even in synthetic form, it mirrors the structure of real
claims — so exploring it teaches the analytical questions payers, providers, and
health-policy teams actually ask. This project turns that raw claims data into an
analytics-ready model and answers the questions below.

## Analytical objectives (the questions the lakehouse answers)

1. **Cost & spend** — What is total and average reimbursement per beneficiary?
   How is spend distributed, and do a small share of beneficiaries drive most of
   the cost (the classic high-cost-patient pattern)?
2. **Utilization** — How many claims occur by type (inpatient, outpatient,
   carrier, prescription drug)? What are admission and visit frequencies?
3. **Clinical / diagnosis mix** — Which diagnoses (ICD codes) are most common?
   How prevalent are chronic conditions, and which conditions co-occur?
4. **Beneficiary demographics** — How do age, sex, and region relate to cost and
   utilization?
5. **Provider view** — How do cost and utilization vary across providers or
   facilities?
6. **Temporal trends** — How do claims and spend move over time (monthly /
   yearly), and is there seasonality?
7. **Prescription drugs** — What are the most frequent drugs and the biggest
   drivers of drug spend (PDE)?
8. **Data quality** — How complete and valid is the data? Where are missing
   values, invalid codes, or duplicate claims? (A bronze/silver objective.)

## Engineering objectives (what the project demonstrates)

- A working **medallion architecture** (Bronze → Silver → Gold) end to end.
- A **serverless, cost-controlled** AWS deployment that stays in the free tier.
- **Dimensional modeling** — a star schema fit for analytics.
- **CI/CD and version control** with GitHub Actions and Git.
- **Reproducibility** — raw data retained in bronze so any layer can be rebuilt.

## Target metrics (what the gold layer computes)

Turning the questions above into concrete, named measures the pipeline builds toward:

**Cost & spend**
- `pbpm` — cost per beneficiary per month
- `spend_by_claim_type` — inpatient vs outpatient vs carrier vs prescription drug
- `cost_concentration` — share of total spend from the top 10% of beneficiaries

**Utilization**
- `admissions_per_1000` beneficiaries
- `readmission_rate_30d` — 30-day readmission rate
- `avg_length_of_stay` — inpatient
- `visits_per_beneficiary_year` — outpatient / physician

**Chronic conditions & population health**
- `condition_prevalence` — % of beneficiaries per chronic-condition flag
- `multimorbidity_distribution` — number of conditions per beneficiary
- `cost_by_condition_count` — average spend as conditions accumulate

**Prescription drugs**
- `drugs_per_beneficiary` — polypharmacy
- `drug_spend_pmpm` — prescription cost per member per month

**Demographic & regional**
- `cost_util_by_age_sex_region` — cost and utilization cut by age band, sex, state

Each metric becomes an aggregate mart (table or view) over `fact_claims` + the
dimensions, so the dashboard reads fast and cheap from Athena.

## Deliverables

- Cleaned, conformed claims in the silver layer.
- A queryable star schema (`fact_claims` + `dim_*`) in the gold layer.
- Athena queries answering the objectives above.
- A Streamlit dashboard surfacing the headline metrics.

# Data Quality Checker

A CLI tool that validates a **data warehouse** built on a **Kimball dimensional
model** (star schema), running automated null, duplicate, referential
integrity, freshness, and schema drift checks — with infrastructure
provisioned as code and a CI/CD pipeline enforcing quality on every push.

## Architecture

```
Synthetic order data
        |
        v
DuckDB data warehouse (star schema: fact_orders + 4 dimension tables)
        |
        v
Python CLI runs quality checks (nulls, duplicates, referential
integrity, freshness, schema drift)
        |
        v
JSON report --> uploaded to AWS S3 (via boto3, LocalStack locally)
        |
        v
GitHub Actions CI/CD: lint + pytest + terraform validate on every push
```

Infrastructure (the S3 bucket that stores report artifacts) is provisioned
with **Terraform** using the official AWS provider — genuine
**Infrastructure as Code**, run locally against
[LocalStack](https://www.localstack.cloud/) (an AWS emulator) so the
project has zero cost and zero cloud account dependency. The Terraform
code is unchanged if pointed at a real AWS account later.

## Why these technology choices

| Concept | Implementation here |
|---|---|
| Data warehouse / dimensional modeling | DuckDB (OLAP engine) modeled as a Kimball star schema — one fact table (`fact_orders`), four dimensions (`dim_customer`, `dim_product`, `dim_date`, `dim_geography`) |
| AWS | `boto3` + S3, run against LocalStack for local development |
| Infrastructure as Code | Terraform (`hashicorp/aws` provider) provisioning the S3 bucket and versioning config |
| CI/CD | GitHub Actions — lint (`flake8`), test (`pytest`), and `terraform validate` run automatically on every push/PR |

## Project structure

```
data-quality-checker/
├── cli/
│   ├── main.py            # CLI entry point (load-sample-data, run)
│   └── upload_report.py   # Uploads JSON reports to S3
├── checks/
│   ├── null_check.py
│   ├── duplicate_check.py
│   ├── referential_integrity.py
│   ├── freshness_check.py
│   └── schema_drift.py
├── warehouse/
│   ├── schema.sql          # Kimball star schema DDL
│   └── duckdb_connector.py
├── data/
│   └── generate_sample_data.py   # Synthetic data generator (seeds real quality issues)
├── terraform/
│   └── main.tf             # S3 bucket, provisioned via Terraform against LocalStack
├── tests/
│   └── test_checks.py      # pytest suite, in-memory DuckDB fixtures
└── .github/workflows/
    └── ci.yml              # Lint + test + terraform validate on every push
```

## Running it locally

```bash
pip install -r requirements.txt

# 1. Load synthetic star-schema data into the warehouse
python -m cli.main load-sample-data

# 2. Run the full quality check suite
python -m cli.main run --table fact_orders
```

The sample data generator deliberately seeds a few real data quality
issues (a null quantity, an orphaned foreign key, a duplicate row) so the
checker has something genuine to catch rather than always passing.

### Uploading reports to S3 (optional, requires LocalStack running)

```bash
# Start LocalStack (requires Docker)
docker run -d -p 4566:4566 localstack/localstack

# Provision the S3 bucket
cd terraform && terraform init && terraform apply

# Generate and upload a report
python -m cli.main run --table fact_orders > report.json
python cli/upload_report.py report.json
```

### Running tests

```bash
pytest tests/ -v
```

## Checks implemented

- **Null checks** — configurable threshold per column
- **Duplicate detection** — key-based duplicate row detection
- **Referential integrity** — verifies every fact-table foreign key has a
  matching dimension row (catches orphaned rows that silently break joins)
- **Freshness** — flags data older than a configurable SLA
- **Schema drift** — detects columns added or removed since the last
  known-good snapshot

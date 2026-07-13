# Data Layer — C360 Data Loading

Downloads Customer 360 CSV data from Stardog's Knowledge Kit and loads it into Aurora PostgreSQL and Redshift Serverless.

## Data Split

| Database | Tables | Source CSVs |
|----------|--------|-------------|
| **Aurora PostgreSQL** | customer, address, credit_card, rewards_account | Operational/customer data |
| **Redshift Serverless** | purchase, product, category, vendor | Analytics/product data |

## Prerequisites

1. Infrastructure deployed (Unit 1): Aurora + Redshift + S3 accessible
2. Python 3.11+ with dependencies installed
3. AWS credentials configured (for Secrets Manager + S3 access)
4. Network access to Aurora (port 5432) and Redshift (port 5439)

## Setup

```bash
cd data/
pip install -r requirements.txt
```

## Environment Variables

```bash
# Aurora connection (or use Secrets Manager: c360/aurora/master)
export AURORA_HOST="c360-poc-aurora.cluster-xxx.us-east-1.rds.amazonaws.com"
export AURORA_PORT=5432
export AURORA_DATABASE=customer360_db
export AURORA_USERNAME=postgres
export AURORA_PASSWORD="<from-secrets-manager>"

# Redshift connection (or use Secrets Manager: c360/redshift/admin)
export REDSHIFT_HOST="c360-atscale-wg.652341767951.us-east-1.redshift-serverless.amazonaws.com"
export REDSHIFT_PORT=5439
export REDSHIFT_DATABASE=analytics_db
export REDSHIFT_USERNAME=admin
export REDSHIFT_PASSWORD="<from-secrets-manager>"

# S3 + IAM for Redshift COPY
export S3_BUCKET="c360-poc-data-652341767951-us-east-1"
export REDSHIFT_COPY_ROLE_ARN="arn:aws:iam::652341767951:role/c360-poc-redshift-s3-access"
```

## Run All Steps

```bash
cd data/scripts/
python load_all.py
```

## Run Steps Individually

```bash
# 1. Download CSVs from GitHub
python scripts/download_data.py

# 2. Load into Aurora
python scripts/load_aurora.py

# 3. Load into Redshift (uploads to S3 first, then COPY)
python scripts/load_redshift.py

# 4. Validate data integrity
python scripts/validate_data.py
```

## Verification

After loading, you can verify with direct SQL:

```bash
# Aurora
psql -h $AURORA_HOST -U postgres -d customer360_db -c "SELECT COUNT(*) FROM customer;"

# Redshift
psql -h $REDSHIFT_HOST -U admin -d analytics_db -p 5439 -c "SELECT COUNT(*) FROM purchase;"
```

## Data Source

CSV files from: https://github.com/stardog-union/knowledge-kits/tree/main/examples/c360/data

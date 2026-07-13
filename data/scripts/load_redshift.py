#!/usr/bin/env python3
"""Load C360 product/purchase data into Amazon Redshift Serverless."""

import os
import json
from pathlib import Path

import boto3
import psycopg2


def get_redshift_credentials() -> dict:
    """Retrieve Redshift credentials from Secrets Manager."""
    secret_name = os.environ.get("REDSHIFT_SECRET_NAME", "c360/redshift/admin")
    client = boto3.client("secretsmanager", region_name="us-east-1")
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response["SecretString"])


def get_redshift_connection():
    """Create connection to Redshift Serverless."""
    # Try environment variables first
    host = os.environ.get("REDSHIFT_HOST")
    if host:
        return psycopg2.connect(
            host=host,
            port=int(os.environ.get("REDSHIFT_PORT", 5439)),
            dbname=os.environ.get("REDSHIFT_DATABASE", "analytics_db"),
            user=os.environ.get("REDSHIFT_USERNAME", "admin"),
            password=os.environ.get("REDSHIFT_PASSWORD"),
            sslmode="require",
        )

    # Use Secrets Manager
    creds = get_redshift_credentials()
    workgroup = os.environ.get("REDSHIFT_WORKGROUP", "c360-atscale-wg")
    host = os.environ.get(
        "REDSHIFT_HOST",
        f"{workgroup}.652341767951.us-east-1.redshift-serverless.amazonaws.com",
    )
    return psycopg2.connect(
        host=host,
        port=5439,
        dbname=os.environ.get("REDSHIFT_DATABASE", "analytics_db"),
        user=creds["username"],
        password=creds["password"],
        sslmode="require",
    )


def upload_csvs_to_s3(csv_dir: str, bucket: str, prefix: str = "staging") -> None:
    """Upload CSV files to S3 for Redshift COPY."""
    s3 = boto3.client("s3", region_name="us-east-1")
    csv_path = Path(csv_dir)

    files = ["purchase.csv", "product.csv", "category.csv", "vendor.csv"]

    print(f"Uploading CSVs to s3://{bucket}/{prefix}/")
    for filename in files:
        file_path = csv_path / filename
        if not file_path.exists():
            print(f"  ✗ {filename} not found")
            continue

        s3_key = f"{prefix}/{filename}"
        s3.upload_file(str(file_path), bucket, s3_key)
        print(f"  ✓ {filename} → s3://{bucket}/{s3_key}")


def create_schema(conn) -> None:
    """Execute Redshift DDL to create tables."""
    ddl_path = Path(__file__).parent / "redshift_ddl.sql"
    ddl = ddl_path.read_text()

    with conn.cursor() as cur:
        cur.execute(ddl)
    conn.commit()
    print("✓ Redshift schema created (4 tables)")


def load_table_from_s3(conn, table_name: str, bucket: str, s3_key: str, iam_role: str) -> int:
    """Load a single table using Redshift COPY from S3."""
    copy_sql = f"""
    COPY {table_name}
    FROM 's3://{bucket}/{s3_key}'
    IAM_ROLE '{iam_role}'
    CSV
    IGNOREHEADER 1
    DATEFORMAT 'auto'
    TIMEFORMAT 'auto'
    REGION 'us-east-1';
    """

    with conn.cursor() as cur:
        # Truncate first (idempotent)
        cur.execute(f"TRUNCATE TABLE {table_name}")
        cur.execute(copy_sql)
    conn.commit()

    # Get row count
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cur.fetchone()[0]

    return count


def load_redshift_data(csv_dir: str = None) -> None:
    """Upload CSVs to S3 and COPY into Redshift."""
    if csv_dir is None:
        csv_dir = os.path.join(os.path.dirname(__file__), "..", "csv")

    # Configuration
    bucket = os.environ.get("S3_BUCKET", "c360-poc-data-652341767951-us-east-1")
    iam_role = os.environ.get("REDSHIFT_COPY_ROLE_ARN")

    if not iam_role:
        print("ERROR: REDSHIFT_COPY_ROLE_ARN environment variable required")
        print("  Set to the ARN of the IAM role attached to Redshift for S3 access")
        print("  Example: arn:aws:iam::652341767951:role/c360-poc-redshift-s3-access")
        return

    # Step 1: Upload CSVs to S3
    upload_csvs_to_s3(csv_dir, bucket)

    # Step 2: Connect to Redshift
    print("\nConnecting to Redshift Serverless...")
    conn = get_redshift_connection()

    try:
        # Step 3: Create schema
        create_schema(conn)

        # Step 4: COPY data from S3
        tables = [
            ("category", f"staging/category.csv"),
            ("vendor", f"staging/vendor.csv"),
            ("product", f"staging/product.csv"),
            ("purchase", f"staging/purchase.csv"),
        ]

        print("\nLoading data into Redshift:")
        print("-" * 50)
        total_rows = 0
        for table_name, s3_key in tables:
            count = load_table_from_s3(conn, table_name, bucket, s3_key, iam_role)
            total_rows += count
            print(f"  ✓ {table_name}: {count} rows loaded")

        print("-" * 50)
        print(f"✓ Redshift loading complete: {total_rows} total rows across 4 tables")

    finally:
        conn.close()


if __name__ == "__main__":
    load_redshift_data()

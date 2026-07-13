#!/usr/bin/env python3
"""Load C360 customer data into Aurora PostgreSQL."""

import os
import json
import csv
from pathlib import Path

import boto3
import psycopg2


def get_aurora_credentials() -> dict:
    """Retrieve Aurora credentials from Secrets Manager."""
    secret_arn = os.environ.get("AURORA_SECRET_ARN")
    if not secret_arn:
        # Fallback: lookup by name
        secret_name = "c360/aurora/master"
        client = boto3.client("secretsmanager", region_name="us-east-1")
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response["SecretString"])

    client = boto3.client("secretsmanager", region_name="us-east-1")
    response = client.get_secret_value(SecretId=secret_arn)
    return json.loads(response["SecretString"])


def get_aurora_connection():
    """Create PostgreSQL connection to Aurora."""
    # Try environment variables first (for local/direct use)
    host = os.environ.get("AURORA_HOST")
    if host:
        return psycopg2.connect(
            host=host,
            port=int(os.environ.get("AURORA_PORT", 5432)),
            dbname=os.environ.get("AURORA_DATABASE", "customer360_db"),
            user=os.environ.get("AURORA_USERNAME", "postgres"),
            password=os.environ.get("AURORA_PASSWORD"),
            sslmode="require",
        )

    # Use Secrets Manager
    creds = get_aurora_credentials()
    return psycopg2.connect(
        host=creds.get("host", os.environ.get("AURORA_HOST")),
        port=int(creds.get("port", 5432)),
        dbname=os.environ.get("AURORA_DATABASE", "customer360_db"),
        user=creds["username"],
        password=creds["password"],
        sslmode="require",
    )


def create_schema(conn) -> None:
    """Execute Aurora DDL to create tables."""
    ddl_path = Path(__file__).parent / "aurora_ddl.sql"
    ddl = ddl_path.read_text()

    with conn.cursor() as cur:
        cur.execute(ddl)
    conn.commit()
    print("✓ Aurora schema created (4 tables + indexes)")


def load_table(conn, table_name: str, csv_path: Path) -> int:
    """Load a single CSV file into Aurora table using COPY."""
    with conn.cursor() as cur:
        # Truncate first (idempotent)
        cur.execute(f"TRUNCATE TABLE {table_name} CASCADE")

        # Use COPY for fast loading
        with open(csv_path, "r") as f:
            # Skip header by using csv.reader to get columns
            reader = csv.reader(f)
            header = next(reader)
            columns = ", ".join(header)

            # Reset file pointer after header
            f.seek(0)
            next(f)  # skip header line

            cur.copy_expert(
                f"COPY {table_name} ({columns}) FROM STDIN WITH CSV",
                f,
            )

    conn.commit()

    # Get row count
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cur.fetchone()[0]

    return count


def load_aurora_data(csv_dir: str = None) -> None:
    """Load all customer data CSV files into Aurora."""
    if csv_dir is None:
        csv_dir = os.path.join(os.path.dirname(__file__), "..", "csv")

    csv_path = Path(csv_dir)

    # Tables to load (order matters for foreign keys)
    tables = [
        ("customer", "customer.csv"),
        ("address", "address.csv"),
        ("credit_card", "credit_card.csv"),
        ("rewards_account", "rewards_account.csv"),
    ]

    print("Connecting to Aurora PostgreSQL...")
    conn = get_aurora_connection()

    try:
        # Create schema
        create_schema(conn)

        # Load data
        print("\nLoading data into Aurora:")
        print("-" * 50)
        total_rows = 0
        for table_name, csv_file in tables:
            file_path = csv_path / csv_file
            if not file_path.exists():
                print(f"  ✗ {csv_file} not found at {file_path}")
                continue

            count = load_table(conn, table_name, file_path)
            total_rows += count
            print(f"  ✓ {table_name}: {count} rows loaded")

        print("-" * 50)
        print(f"✓ Aurora loading complete: {total_rows} total rows across 4 tables")

    finally:
        conn.close()


if __name__ == "__main__":
    load_aurora_data()

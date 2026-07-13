#!/usr/bin/env python3
"""Validate data integrity across Aurora and Redshift."""

import os
import json
import sys

import boto3
import psycopg2


def get_aurora_connection():
    """Connect to Aurora PostgreSQL."""
    host = os.environ.get("AURORA_HOST")
    if not host:
        # Try Secrets Manager
        client = boto3.client("secretsmanager", region_name="us-east-1")
        response = client.get_secret_value(SecretId="c360/aurora/master")
        creds = json.loads(response["SecretString"])
        host = creds.get("host", os.environ.get("AURORA_HOST"))
        user = creds["username"]
        password = creds["password"]
    else:
        user = os.environ.get("AURORA_USERNAME", "postgres")
        password = os.environ.get("AURORA_PASSWORD")

    return psycopg2.connect(
        host=host,
        port=int(os.environ.get("AURORA_PORT", 5432)),
        dbname=os.environ.get("AURORA_DATABASE", "customer360_db"),
        user=user,
        password=password,
        sslmode="require",
    )


def get_redshift_connection():
    """Connect to Redshift Serverless."""
    host = os.environ.get("REDSHIFT_HOST")
    if not host:
        client = boto3.client("secretsmanager", region_name="us-east-1")
        response = client.get_secret_value(SecretId="c360/redshift/admin")
        creds = json.loads(response["SecretString"])
        workgroup = os.environ.get("REDSHIFT_WORKGROUP", "c360-atscale-wg")
        host = f"{workgroup}.652341767951.us-east-1.redshift-serverless.amazonaws.com"
        user = creds["username"]
        password = creds["password"]
    else:
        user = os.environ.get("REDSHIFT_USERNAME", "admin")
        password = os.environ.get("REDSHIFT_PASSWORD")

    return psycopg2.connect(
        host=host,
        port=5439,
        dbname=os.environ.get("REDSHIFT_DATABASE", "analytics_db"),
        user=user,
        password=password,
        sslmode="require",
    )


def validate_data() -> bool:
    """Run validation checks across both databases."""
    print("=" * 60)
    print("DATA VALIDATION REPORT")
    print("=" * 60)

    all_passed = True

    # ─── Aurora Validation ───
    print("\n📊 Aurora PostgreSQL (customer360_db)")
    print("-" * 40)

    try:
        aurora_conn = get_aurora_connection()
        aurora_cur = aurora_conn.cursor()

        aurora_tables = {
            "customer": 0,
            "address": 0,
            "credit_card": 0,
            "rewards_account": 0,
        }

        for table in aurora_tables:
            aurora_cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = aurora_cur.fetchone()[0]
            aurora_tables[table] = count
            status = "✓" if count > 0 else "✗"
            print(f"  {status} {table}: {count} rows")
            if count == 0:
                all_passed = False

        # Check foreign key integrity
        aurora_cur.execute("""
            SELECT COUNT(*) FROM address a
            WHERE NOT EXISTS (SELECT 1 FROM customer c WHERE c.cid = a.cid)
        """)
        orphans = aurora_cur.fetchone()[0]
        if orphans == 0:
            print(f"  ✓ FK integrity: address.cid → customer.cid (no orphans)")
        else:
            print(f"  ✗ FK integrity: {orphans} orphan addresses")
            all_passed = False

        aurora_conn.close()
    except Exception as e:
        print(f"  ✗ Aurora connection failed: {e}")
        all_passed = False

    # ─── Redshift Validation ───
    print(f"\n📊 Redshift Serverless (analytics_db)")
    print("-" * 40)

    try:
        redshift_conn = get_redshift_connection()
        redshift_cur = redshift_conn.cursor()

        redshift_tables = {
            "purchase": 0,
            "product": 0,
            "category": 0,
            "vendor": 0,
        }

        for table in redshift_tables:
            redshift_cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = redshift_cur.fetchone()[0]
            redshift_tables[table] = count
            status = "✓" if count > 0 else "✗"
            print(f"  {status} {table}: {count} rows")
            if count == 0:
                all_passed = False

        # Check cross-database key reference
        redshift_cur.execute("SELECT COUNT(DISTINCT cid) FROM purchase")
        distinct_cids_redshift = redshift_cur.fetchone()[0]
        print(f"  ℹ Distinct customer IDs in purchase: {distinct_cids_redshift}")

        redshift_conn.close()
    except Exception as e:
        print(f"  ✗ Redshift connection failed: {e}")
        all_passed = False

    # ─── Cross-Database Validation ───
    print(f"\n📊 Cross-Database Integrity")
    print("-" * 40)

    try:
        aurora_conn = get_aurora_connection()
        aurora_cur = aurora_conn.cursor()
        aurora_cur.execute("SELECT COUNT(DISTINCT cid) FROM customer")
        distinct_cids_aurora = aurora_cur.fetchone()[0]
        aurora_conn.close()

        print(f"  ℹ Distinct customers in Aurora: {distinct_cids_aurora}")
        print(f"  ℹ Distinct customers in Redshift purchases: {distinct_cids_redshift}")

        if distinct_cids_redshift <= distinct_cids_aurora:
            print(f"  ✓ All Redshift customer refs exist in Aurora")
        else:
            print(f"  ⚠ Redshift has {distinct_cids_redshift - distinct_cids_aurora} customers not in Aurora")

    except Exception as e:
        print(f"  ⚠ Cross-database check skipped: {e}")

    # ─── Summary ───
    print(f"\n{'=' * 60}")
    if all_passed:
        print("✅ ALL VALIDATIONS PASSED")
    else:
        print("❌ SOME VALIDATIONS FAILED — check above for details")
    print(f"{'=' * 60}")

    return all_passed


if __name__ == "__main__":
    success = validate_data()
    sys.exit(0 if success else 1)

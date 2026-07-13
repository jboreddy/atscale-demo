#!/usr/bin/env python3
"""Configure AtScale data connections to Aurora and Redshift via REST API."""

import os
import json
import requests

# AtScale API configuration
ATSCALE_URL = os.environ.get("ATSCALE_URL", "http://localhost:10500")
ATSCALE_USER = os.environ.get("ATSCALE_USERNAME", "admin")
ATSCALE_PASS = os.environ.get("ATSCALE_PASSWORD", "admin")

# Database endpoints (from CDK outputs or env vars)
AURORA_HOST = os.environ.get("AURORA_HOST")
AURORA_PORT = int(os.environ.get("AURORA_PORT", 5432))
AURORA_DB = os.environ.get("AURORA_DATABASE", "customer360_db")
AURORA_USER = os.environ.get("AURORA_USERNAME", "postgres")
AURORA_PASS = os.environ.get("AURORA_PASSWORD")

REDSHIFT_HOST = os.environ.get("REDSHIFT_HOST")
REDSHIFT_PORT = int(os.environ.get("REDSHIFT_PORT", 5439))
REDSHIFT_DB = os.environ.get("REDSHIFT_DATABASE", "analytics_db")
REDSHIFT_USER = os.environ.get("REDSHIFT_USERNAME", "admin")
REDSHIFT_PASS = os.environ.get("REDSHIFT_PASSWORD")


def get_auth_token() -> str:
    """Authenticate with AtScale and get session token."""
    response = requests.post(
        f"{ATSCALE_URL}/api/1.0/auth/login",
        json={"username": ATSCALE_USER, "password": ATSCALE_PASS},
    )
    response.raise_for_status()
    return response.json().get("token", response.cookies.get("JSESSIONID"))


def create_connection(token: str, connection_config: dict) -> dict:
    """Create a data connection in AtScale."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    response = requests.post(
        f"{ATSCALE_URL}/api/1.0/org/connections",
        headers=headers,
        json=connection_config,
    )
    response.raise_for_status()
    return response.json()


def test_connection(token: str, connection_id: str) -> bool:
    """Test a data connection."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{ATSCALE_URL}/api/1.0/org/connections/{connection_id}/test",
        headers=headers,
    )
    return response.status_code == 200


def main():
    """Configure Aurora and Redshift connections."""
    print("═══════════════════════════════════════════════════")
    print("AtScale Data Connection Configuration")
    print("═══════════════════════════════════════════════════")

    # Validate required env vars
    required_vars = {
        "AURORA_HOST": AURORA_HOST,
        "AURORA_PASSWORD": AURORA_PASS,
        "REDSHIFT_HOST": REDSHIFT_HOST,
        "REDSHIFT_PASSWORD": REDSHIFT_PASS,
    }
    missing = [k for k, v in required_vars.items() if not v]
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        print("   Set these from CDK outputs or Secrets Manager")
        return

    # Authenticate
    print("\n📋 Authenticating with AtScale...")
    token = get_auth_token()
    print("  ✓ Authenticated")

    # Aurora Connection
    print("\n📋 Creating Aurora PostgreSQL connection...")
    aurora_config = {
        "name": "aurora_c360",
        "type": "postgresql",
        "host": AURORA_HOST,
        "port": AURORA_PORT,
        "database": AURORA_DB,
        "username": AURORA_USER,
        "password": AURORA_PASS,
        "ssl": True,
        "properties": {
            "description": "Aurora PostgreSQL - Customer operational data",
        },
    }

    try:
        result = create_connection(token, aurora_config)
        conn_id = result.get("id", "unknown")
        print(f"  ✓ Connection created: aurora_c360 (id: {conn_id})")

        if test_connection(token, conn_id):
            print("  ✓ Connection test: PASSED")
        else:
            print("  ⚠ Connection test: FAILED (check network/credentials)")
    except requests.HTTPError as e:
        if e.response.status_code == 409:
            print("  ℹ Connection 'aurora_c360' already exists")
        else:
            print(f"  ✗ Error: {e}")

    # Redshift Connection
    print("\n📋 Creating Redshift Serverless connection...")
    redshift_config = {
        "name": "redshift_c360",
        "type": "redshift",
        "host": REDSHIFT_HOST,
        "port": REDSHIFT_PORT,
        "database": REDSHIFT_DB,
        "username": REDSHIFT_USER,
        "password": REDSHIFT_PASS,
        "ssl": True,
        "properties": {
            "description": "Redshift Serverless - Product and purchase analytics",
        },
    }

    try:
        result = create_connection(token, redshift_config)
        conn_id = result.get("id", "unknown")
        print(f"  ✓ Connection created: redshift_c360 (id: {conn_id})")

        if test_connection(token, conn_id):
            print("  ✓ Connection test: PASSED")
        else:
            print("  ⚠ Connection test: FAILED (check network/credentials)")
    except requests.HTTPError as e:
        if e.response.status_code == 409:
            print("  ℹ Connection 'redshift_c360' already exists")
        else:
            print(f"  ✗ Error: {e}")

    print("\n═══════════════════════════════════════════════════")
    print("✅ Connection configuration complete!")
    print("   Next: Import Customer_360 model via Design Center")
    print("═══════════════════════════════════════════════════")


if __name__ == "__main__":
    main()

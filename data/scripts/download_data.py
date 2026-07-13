#!/usr/bin/env python3
"""Download C360 CSV files from Stardog Knowledge Kit GitHub repository."""

import os
import urllib.request
from pathlib import Path

# GitHub raw content base URL
GITHUB_BASE = (
    "https://raw.githubusercontent.com/stardog-union/knowledge-kits"
    "/main/examples/c360/data"
)

# CSV files to download
# Aurora tables (customer/operational data)
AURORA_FILES = [
    "customer.csv",
    "address.csv",
    "credit_card.csv",
    "rewards_account.csv",
]

# Redshift tables (product/purchase analytics data)
REDSHIFT_FILES = [
    "purchase.csv",
    "product.csv",
    "category.csv",
    "vendor.csv",
]

ALL_FILES = AURORA_FILES + REDSHIFT_FILES


def download_csvs(output_dir: str = None) -> None:
    """Download all C360 CSV files from GitHub."""
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), "..", "csv")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Downloading C360 CSV files to: {output_path.resolve()}")
    print(f"Source: {GITHUB_BASE}")
    print("-" * 60)

    for filename in ALL_FILES:
        url = f"{GITHUB_BASE}/{filename}"
        dest = output_path / filename

        print(f"  Downloading {filename}...", end=" ")
        try:
            urllib.request.urlretrieve(url, dest)
            # Count rows (excluding header)
            with open(dest) as f:
                row_count = sum(1 for _ in f) - 1
            print(f"✓ ({row_count} rows)")
        except Exception as e:
            print(f"✗ ERROR: {e}")
            raise

    print("-" * 60)
    print(f"✓ All {len(ALL_FILES)} files downloaded successfully.")


if __name__ == "__main__":
    download_csvs()

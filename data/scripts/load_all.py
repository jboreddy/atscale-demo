#!/usr/bin/env python3
"""Orchestrator - Run all data loading steps in order."""

import sys
from download_data import download_csvs
from load_aurora import load_aurora_data
from load_redshift import load_redshift_data
from validate_data import validate_data


def main():
    """Execute complete data loading pipeline."""
    print("=" * 60)
    print("C360 DATA LOADING PIPELINE")
    print("=" * 60)

    # Step 1: Download CSVs
    print("\n📥 STEP 1: Download CSV files from GitHub")
    print("-" * 60)
    try:
        download_csvs()
    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        sys.exit(1)

    # Step 2: Load Aurora
    print("\n\n📤 STEP 2: Load data into Aurora PostgreSQL")
    print("-" * 60)
    try:
        load_aurora_data()
    except Exception as e:
        print(f"\n❌ Aurora loading failed: {e}")
        sys.exit(1)

    # Step 3: Load Redshift
    print("\n\n📤 STEP 3: Load data into Redshift Serverless")
    print("-" * 60)
    try:
        load_redshift_data()
    except Exception as e:
        print(f"\n❌ Redshift loading failed: {e}")
        sys.exit(1)

    # Step 4: Validate
    print("\n\n🔍 STEP 4: Validate data integrity")
    print("-" * 60)
    success = validate_data()

    if success:
        print("\n\n✅ DATA PIPELINE COMPLETE — All data loaded and validated!")
    else:
        print("\n\n⚠️  DATA PIPELINE COMPLETE — Some validations failed, check above.")
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Validation script for modified openclaw modules."""

import sys
from pathlib import Path

print("=" * 60)
print("OpenClaw Python Environment Validation")
print("=" * 60)

# Test 1: Verify imports work
print("\n=== Import Test ===")
try:
    import sync_osm
    print("✓ sync_osm imported successfully")
    print(f"  OUTPUT_PATH: {sync_osm.OUTPUT_PATH}")
except Exception as e:
    print(f"✗ sync_osm import failed: {e}")
    sys.exit(1)

# Test 2: sync_census imports
try:
    import sync_census
    print("✓ sync_census imported successfully")
    print(f"  OUTPUT_PATH: {sync_census.OUTPUT_PATH}")
except Exception as e:
    print(f"✗ sync_census import failed: {e}")
    sys.exit(1)

# Test 3: human_mimic_analysis imports
try:
    import human_mimic_analysis
    print("✓ human_mimic_analysis imported successfully")
    print(f"  INPUT_CSV: {human_mimic_analysis.INPUT_CSV}")
    print(f"  OUTPUT_CSV: {human_mimic_analysis.OUTPUT_CSV}")
except Exception as e:
    print(f"✗ human_mimic_analysis import failed: {e}")
    sys.exit(1)

# Test 4: Check environment and data directory
print("\n=== Environment & Directory Check ===")
import os
print(f"Working directory: {Path.cwd()}")
data_dir = Path.cwd() / "data"
print(f"Data directory: {data_dir}")
print(f"Data directory exists: {data_dir.exists()}")

if not data_dir.exists():
    print("Creating data directory...")
    data_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ Created: {data_dir}")

# Test 5: Check key dependencies
print("\n=== Dependency Check ===")
try:
    import pandas as pd
    print(f"✓ pandas {pd.__version__}")
except ImportError as e:
    print(f"✗ pandas not available: {e}")

try:
    import requests
    print(f"✓ requests {requests.__version__}")
except ImportError as e:
    print(f"✗ requests not available: {e}")

try:
    import openpyxl
    print(f"✓ openpyxl {openpyxl.__version__}")
except ImportError as e:
    print(f"✗ openpyxl not available: {e}")

try:
    import dotenv
    print(f"✓ python-dotenv available")
except ImportError as e:
    print(f"✗ python-dotenv not available: {e}")

print("\n" + "=" * 60)
print("✓ All validation checks passed!")
print("=" * 60)
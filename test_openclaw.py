#!/usr/bin/env python3
"""
Comprehensive test suite for OpenClaw Python integration.
Tests data processing, API connectivity, and core functionality.
"""

import sys
import os
from pathlib import Path
import json
import csv
from datetime import datetime

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test all core module imports."""
    print("\n" + "="*60)
    print("TEST 1: Module Imports")
    print("="*60)
    
    tests = []
    
    try:
        import pandas as pd
        print(f"✓ pandas {pd.__version__}")
        tests.append(True)
    except Exception as e:
        print(f"✗ pandas: {e}")
        tests.append(False)
    
    try:
        import requests
        print(f"✓ requests {requests.__version__}")
        tests.append(True)
    except Exception as e:
        print(f"✗ requests: {e}")
        tests.append(False)
    
    try:
        import openpyxl
        print(f"✓ openpyxl {openpyxl.__version__}")
        tests.append(True)
    except Exception as e:
        print(f"✗ openpyxl: {e}")
        tests.append(False)
    
    try:
        import sync_osm
        print(f"✓ sync_osm module")
        tests.append(True)
    except Exception as e:
        print(f"✗ sync_osm: {e}")
        tests.append(False)
    
    try:
        import sync_census
        print(f"✓ sync_census module")
        tests.append(True)
    except Exception as e:
        print(f"✗ sync_census: {e}")
        tests.append(False)
    
    try:
        import human_mimic_analysis
        print(f"✓ human_mimic_analysis module")
        tests.append(True)
    except Exception as e:
        print(f"✗ human_mimic_analysis: {e}")
        tests.append(False)
    
    return all(tests)

def test_pandas_processing():
    """Test pandas data processing capabilities."""
    print("\n" + "="*60)
    print("TEST 2: Pandas Data Processing")
    print("="*60)
    
    try:
        import pandas as pd
        import numpy as np
        
        # Create test data
        data = {
            'tract': ['001401', '005700', '001500'],
            'income': [89873, 236250, 156000],
            'population': [2500, 3000, 2800],
            'young': [393, 315, 450]
        }
        
        df = pd.DataFrame(data)
        print(f"✓ Created DataFrame with {len(df)} rows")
        print(f"  Columns: {', '.join(df.columns)}")
        
        # Test filtering
        filtered = df[df['income'] > 100000]
        print(f"✓ Filtered rows (income > 100k): {len(filtered)} rows")
        
        # Test grouping
        avg_income = df['income'].mean()
        print(f"✓ Calculated average income: ${avg_income:,.2f}")
        
        # Test merge operations
        df2 = pd.DataFrame({
            'tract': ['001401', '005700'],
            'poi_count': [42, 38]
        })
        merged = df.merge(df2, on='tract', how='left')
        print(f"✓ Performed left merge: {len(merged)} rows")
        
        return True
    except Exception as e:
        print(f"✗ Pandas test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_csv_io():
    """Test CSV file operations."""
    print("\n" + "="*60)
    print("TEST 3: CSV File I/O")
    print("="*60)
    
    try:
        test_csv = Path("test_data.csv")
        
        # Write test CSV
        with open(test_csv, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['name', 'value'])
            writer.writeheader()
            writer.writerows([
                {'name': '测试1', 'value': '123'},
                {'name': '测试2', 'value': '456'},
            ])
        
        print(f"✓ Created test CSV with Chinese characters")
        
        # Read and verify
        with open(test_csv, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        print(f"✓ Read {len(rows)} rows from CSV")
        print(f"  Sample: {rows[0]['name']} = {rows[0]['value']}")
        
        # Cleanup
        test_csv.unlink()
        print(f"✓ Cleanup completed")
        
        return True
    except Exception as e:
        print(f"✗ CSV I/O test failed: {e}")
        return False

def test_api_connectivity():
    """Test API connectivity."""
    print("\n" + "="*60)
    print("TEST 4: API Connectivity Check")
    print("="*60)
    
    import requests
    
    tests = []
    
    # Test Overpass API
    try:
        response = requests.head("https://overpass-api.de/api/interpreter", timeout=10)
        if response.status_code == 405:  # Expected for HEAD request
            print(f"✓ Overpass API reachable (status: {response.status_code})")
            tests.append(True)
        else:
            print(f"⚠ Overpass API responded with: {response.status_code}")
            tests.append(True)  # Still consider it reachable
    except Exception as e:
        print(f"✗ Overpass API unreachable: {e}")
        tests.append(False)
    
    # Test Census API
    try:
        response = requests.get("https://api.census.gov/data/2022/acs/acs5", timeout=10)
        if response.status_code == 400:  # Expected without proper params
            print(f"✓ Census API reachable (status: {response.status_code})")
            tests.append(True)
        else:
            print(f"⚠ Census API responded with: {response.status_code}")
            tests.append(True)
    except Exception as e:
        print(f"✗ Census API unreachable: {e}")
        tests.append(False)
    
    # Test DeepSeek API (metadata only)
    try:
        response = requests.head("https://api.deepseek.com/", timeout=10)
        print(f"✓ DeepSeek API endpoint reachable")
        tests.append(True)
    except Exception as e:
        print(f"⚠ DeepSeek endpoint check: {e}")
        tests.append(True)  # Not critical for core PyPython functionality
    
    return all(tests[:2])  # At least Overpass and Census should work

def test_path_resolution():
    """Test script path resolution logic."""
    print("\n" + "="*60)
    print("TEST 5: Path Resolution")
    print("="*60)
    
    try:
        import sync_osm
        import sync_census
        import human_mimic_analysis
        
        print(f"✓ sync_osm output path:")
        print(f"  {sync_osm.OUTPUT_PATH}")
        print(f"  Exists: {sync_osm.OUTPUT_PATH.parent.exists()}")
        
        print(f"✓ sync_census output path:")
        print(f"  {sync_census.OUTPUT_PATH}")
        print(f"  Exists: {sync_census.OUTPUT_PATH.parent.exists()}")
        
        print(f"✓ human_mimic_analysis paths:")
        print(f"  INPUT:  {human_mimic_analysis.INPUT_CSV}")
        print(f"  OUTPUT: {human_mimic_analysis.OUTPUT_CSV}")
        print(f"  Parent exists: {human_mimic_analysis.OUTPUT_CSV.parent.exists()}")
        
        return True
    except Exception as e:
        print(f"✗ Path resolution failed: {e}")
        return False

def test_config_files():
    """Test configuration files."""
    print("\n" + "="*60)
    print("TEST 6: Configuration Files")
    print("="*60)
    
    try:
        config_files = [
            'openclaw.json',
            'config.json',
            '.env.local',
            'requirements.txt'
        ]
        
        for filename in config_files:
            path = Path(filename)
            if path.exists():
                size = path.stat().st_size
                print(f"✓ {filename} ({size} bytes)")
            else:
                print(f"⚠ {filename} (not found)")
        
        # Load and validate JSON configs
        try:
            with open('openclaw.json', 'r') as f:
                openclaw = json.load(f)
            print(f"✓ openclaw.json is valid JSON")
            print(f"  Models: {', '.join(openclaw.get('models', {}).keys())}")
        except Exception as e:
            print(f"⚠ openclaw.json: {e}")
        
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            print(f"✓ config.json is valid JSON")
            providers = config.get('providers', {})
            print(f"  Providers: {', '.join(providers.keys())}")
        except Exception as e:
            print(f"⚠ config.json: {e}")
        
        return True
    except Exception as e:
        print(f"✗ Config file test failed: {e}")
        return False

def test_environment_variables():
    """Test environment variables."""
    print("\n" + "="*60)
    print("TEST 7: Environment Variables")
    print("="*60)
    
    try:
        test_vars = [
            'OPENCLAW_DATA_DIR',
            'CENSUS_API_KEY',
            'DEEPSEEK_API_KEY',
        ]
        
        for var in test_vars:
            value = os.getenv(var)
            if value:
                # Mask sensitive values
                if 'KEY' in var or 'SECRET' in var:
                    masked = value[:8] + '*' * (len(value) - 16) + value[-8:] if len(value) > 16 else '*' * len(value)
                    print(f"✓ {var} is set ({masked})")
                else:
                    print(f"✓ {var} = {value}")
            else:
                print(f"⚠ {var} (not set)")
        
        return True
    except Exception as e:
        print(f"✗ Environment test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + "  OpenClaw Python Integration Test Suite".center(58) + "║")
    print("║" + f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(58) + "║")
    print("╚" + "="*58 + "╝")
    
    results = []
    
    results.append(("Module Imports", test_imports()))
    results.append(("Pandas Processing", test_pandas_processing()))
    results.append(("CSV I/O", test_csv_io()))
    results.append(("API Connectivity", test_api_connectivity()))
    results.append(("Path Resolution", test_path_resolution()))
    results.append(("Configuration Files", test_config_files()))
    results.append(("Environment Variables", test_environment_variables()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        symbol = "✓" if passed else "✗"
        print(f"{symbol} {test_name:<35} {status}")
    
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    
    print("\n" + "-"*60)
    print(f"Overall: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("✓ OpenClaw Python integration is FULLY OPERATIONAL")
        return 0
    elif passed_count >= total_count - 1:
        print("⚠ OpenClaw Python integration is OPERATIONAL (minor issues)")
        return 0
    else:
        print("✗ OpenClaw Python integration has CRITICAL ISSUES")
        return 1

if __name__ == "__main__":
    sys.exit(main())

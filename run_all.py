#!/usr/bin/env python3
"""
Quick runner script for OpenClaw data processing.
Run this to execute all data synchronization tasks in sequence.
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# Color codes for output
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

def print_header(text):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text:^60}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

def print_success(text):
    print(f"{GREEN}[OK] {text}{RESET}")

def print_error(text):
    print(f"{RED}[ERROR] {text}{RESET}")

def print_info(text):
    print(f"{YELLOW}[INFO] {text}{RESET}")

def run_script(name, script_path, args=None):
    """Run a Python script and return exit code."""
    print_header(f"Running: {name}")
    
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)
    
    print_info(f"Command: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(cmd, check=False)
        if result.returncode == 0:
            print_success(f"{name} completed successfully")
            return True
        else:
            print_error(f"{name} failed with exit code {result.returncode}")
            return False
    except Exception as e:
        print_error(f"Failed to run {name}: {e}")
        return False

def main():
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print_header("OpenClaw Data Processing Runner")
    print_info(f"Project root: {project_root}")
    print_info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Ensure data directory exists
    data_dir = project_root / "data"
    if not data_dir.exists():
        print_info(f"Creating data directory: {data_dir}")
        data_dir.mkdir(parents=True, exist_ok=True)
    
    # Check environment
    census_key = os.getenv("CENSUS_API_KEY")
    if not census_key:
        print_error("CENSUS_API_KEY not set in environment")
        print_info("Set with: $env:CENSUS_API_KEY='your_key'")
        print_info("Get key from: https://api.census.gov/data/key_signup.html")
        print_info("Skipping Census sync...")
    
    tasks = []
    
    # Task 1: Validate environment
    print_header("Validating Environment")
    if run_script("validate_env", project_root / "validate_env.py"):
        tasks.append(("Validate", True))
    else:
        tasks.append(("Validate", False))
        print_error("Environment validation failed. Exiting.")
        return 1
    
    # Task 2: Sync OSM data
    if run_script("OSM Sync", project_root / "sync_osm.py"):
        tasks.append(("OSM Sync", True))
    else:
        tasks.append(("OSM Sync", False))
    
    # Task 3: Sync Census data (optional if no key)
    if census_key:
        args = ["--api-key", census_key]
        if run_script("Census Sync", project_root / "sync_census.py", args):
            tasks.append(("Census Sync", True))
        else:
            tasks.append(("Census Sync", False))
    else:
        print_info("Skipping Census Sync (no CENSUS_API_KEY)")
    
    # Task 4: Human mimic analysis (only if demographics exist)
    demographics_file = data_dir / "manhattan_demographics.csv"
    if demographics_file.exists():
        if run_script("Analysis", project_root / "human_mimic_analysis.py"):
            tasks.append(("Analysis", True))
        else:
            tasks.append(("Analysis", False))
    else:
        print_info(f"Skipping Analysis (demographics not found: {demographics_file})")
    
    # Summary
    print_header("Execution Summary")
    for task_name, success in tasks:
        status = f"{GREEN}PASS{RESET}" if success else f"{RED}FAIL{RESET}"
        print(f"  {task_name:<20} {status}")
    
    success_count = sum(1 for _, s in tasks if s)
    total_count = len(tasks)
    
    print()
    if success_count == total_count:
        print_success(f"All tasks completed successfully ({success_count}/{total_count})")
        print_info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return 0
    else:
        print_error(f"Some tasks failed ({success_count}/{total_count} passed)")
        print_info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

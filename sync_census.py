import argparse
import csv
import os
from pathlib import Path

import requests

CENSUS_YEAR = "2022"
CENSUS_API_BASE = f"https://api.census.gov/data/{CENSUS_YEAR}/acs/acs5"

# Determine output path based on environment or fallback
_project_root = Path(__file__).parent
_env_data_dir = os.getenv("OPENCLAW_DATA_DIR")
if _env_data_dir:
    OUTPUT_PATH = Path(_env_data_dir) / "manhattan_demographics.csv"
else:
    OUTPUT_PATH = _project_root / "data" / "manhattan_demographics.csv"
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

VARS = [
    "B19013_001E",
    "B01003_001E",
    "B01001_003E",
    "B01001_004E",
    "B01001_005E",
    "B01001_006E",
    "B01001_027E",
    "B01001_028E",
    "B01001_029E",
    "B01001_030E",
]

STATE = "36"  # New York
COUNTY = "061"  # New York County (Manhattan)


def build_url(api_key: str) -> str:
    params = {
        "get": ",".join(VARS),
        "for": "tract:*",
        "in": f"state:{STATE}+county:{COUNTY}",
        "key": api_key,
    }
    return CENSUS_API_BASE + "?" + "&".join(f"{k}={v}" for k, v in params.items())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync Census data for Manhattan tracts.")
    parser.add_argument("--api-key", help="US Census API key. Can also be set with CENSUS_API_KEY.")
    parser.add_argument("--year", default=CENSUS_YEAR, help="ACS year to request (default: 2022).")
    parser.add_argument("--output", default=str(OUTPUT_PATH), help="Output CSV path.")
    return parser.parse_args()


def fetch_data(api_key: str, year: str) -> list:
    url = f"https://api.census.gov/data/{year}/acs/acs5"
    params = {
        "get": ",".join(VARS),
        "for": "tract:*",
        "in": f"state:{STATE}+county:{COUNTY}",
        "key": api_key,
    }
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def normalize_row(row: list, headers: list) -> dict:
    return dict(zip(headers, row))


def compute_target_young_population(row: dict) -> int:
    keys = [
        "B01001_003E",
        "B01001_004E",
        "B01001_005E",
        "B01001_006E",
        "B01001_027E",
        "B01001_028E",
        "B01001_029E",
        "B01001_030E",
    ]
    total = 0
    for key in keys:
        value = row.get(key, "0")
        try:
            total += int(value)
        except ValueError:
            total += 0
    return total


def save_csv(rows: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "state",
        "county",
        "tract",
        "B19013_001E",
        "B01003_001E",
        "target_young_population",
    ]
    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "state": row["state"],
                "county": row["county"],
                "tract": row["tract"],
                "B19013_001E": row.get("B19013_001E", ""),
                "B01003_001E": row.get("B01003_001E", ""),
                "target_young_population": row["target_young_population"],
            })


def main() -> None:
    args = parse_args()
    api_key = args.api_key or os.getenv("CENSUS_API_KEY")
    if not api_key:
        raise SystemExit("请提供 US Census API key，使用 --api-key 或设置环境变量 CENSUS_API_KEY。")

    print(f"Using Census year: {args.year}")
    data = fetch_data(api_key, args.year)
    headers = data[0]
    rows = [normalize_row(row, headers) for row in data[1:]]
    for row in rows:
        row["target_young_population"] = compute_target_young_population(row)

    output_path = Path(args.output)
    save_csv(rows, output_path)
    print(f"Saved {len(rows)} tract records to {output_path}")


if __name__ == "__main__":
    main()

import json
from pathlib import Path

import pandas as pd
from geopy.distance import geodesic

BASE_DIR = Path(r"F:\Program Files\QGIS 3.44.9")
RADIUS_M = 500.0

SUBWAY_PATH = BASE_DIR / "tianhe_subway.csv"
OFFICE_CSV_PATH = BASE_DIR / "office_points.csv"
OFFICE_GEOJSON_PATH = BASE_DIR / "Tianhe_Office_GCJ02.geojson"
COFFEE_CSV_PATH = BASE_DIR / "coffee_poi.csv"
COFFEE_GEOJSON_PATH = BASE_DIR / "Tianhe_Coffee.geojson"
OUTPUT_XLSX = BASE_DIR / "subway_potential_ranking.xlsx"


def pick_col(df: pd.DataFrame, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None


def normalize_to_100(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce").fillna(0.0)
    min_v = float(s.min())
    max_v = float(s.max())
    if max_v == min_v:
        if max_v == 0:
            return pd.Series([0.0] * len(s), index=s.index)
        return pd.Series([100.0] * len(s), index=s.index)
    return (s - min_v) / (max_v - min_v) * 100.0


def load_points_from_csv(path: Path, name_fallback="POI"):
    df = pd.read_csv(path, encoding="utf-8-sig")
    lng_col = pick_col(df, ["longitude", "lon", "lng", "x"])
    lat_col = pick_col(df, ["latitude", "lat", "y"])
    name_col = pick_col(df, ["name", "名称", "station", "站点"])

    if lng_col is None or lat_col is None:
        raise ValueError(f"CSV 缺少经纬度列: {path}")

    if name_col is None:
        df["_name"] = [f"{name_fallback}_{i+1}" for i in range(len(df))]
        name_col = "_name"

    out = pd.DataFrame(
        {
            "name": df[name_col].astype(str),
            "longitude": pd.to_numeric(df[lng_col], errors="coerce"),
            "latitude": pd.to_numeric(df[lat_col], errors="coerce"),
        }
    ).dropna(subset=["longitude", "latitude"])

    return out


def load_points_from_geojson(path: Path, name_fallback="POI"):
    with path.open("r", encoding="utf-8") as f:
        gj = json.load(f)

    rows = []
    for i, ft in enumerate(gj.get("features", []), start=1):
        geom = ft.get("geometry", {})
        if geom.get("type") != "Point":
            continue
        coords = geom.get("coordinates", [])
        if not isinstance(coords, list) or len(coords) < 2:
            continue
        props = ft.get("properties", {})
        name = str(props.get("name", f"{name_fallback}_{i}"))
        try:
            lng = float(coords[0])
            lat = float(coords[1])
        except (TypeError, ValueError):
            continue
        rows.append({"name": name, "longitude": lng, "latitude": lat})

    return pd.DataFrame(rows)


def load_subway_points(path: Path):
    subway = load_points_from_csv(path, name_fallback="subway")
    subway["name"] = subway["name"].str.replace(r"\s*[（(]地铁站[）)]\s*", "", regex=True).str.strip()
    return subway


def load_office_points():
    if OFFICE_CSV_PATH.exists():
        return load_points_from_csv(OFFICE_CSV_PATH, name_fallback="office")
    if OFFICE_GEOJSON_PATH.exists():
        return load_points_from_geojson(OFFICE_GEOJSON_PATH, name_fallback="office")
    raise FileNotFoundError("未找到写字楼数据（office_points.csv 或 Tianhe_Office_GCJ02.geojson）")


def load_coffee_points():
    if COFFEE_CSV_PATH.exists():
        return load_points_from_csv(COFFEE_CSV_PATH, name_fallback="coffee")
    if COFFEE_GEOJSON_PATH.exists():
        return load_points_from_geojson(COFFEE_GEOJSON_PATH, name_fallback="coffee")
    raise FileNotFoundError("未找到咖啡馆数据（coffee_poi.csv 或 Tianhe_Coffee.geojson）")


def count_within_radius(center_lat, center_lng, points_df: pd.DataFrame, radius_m: float):
    cnt = 0
    for _, row in points_df.iterrows():
        d = geodesic((center_lat, center_lng), (float(row["latitude"]), float(row["longitude"]))).meters
        if d <= radius_m:
            cnt += 1
    return cnt


def main():
    if not SUBWAY_PATH.exists():
        raise FileNotFoundError(f"缺少地铁站文件: {SUBWAY_PATH}")

    subway_df = load_subway_points(SUBWAY_PATH)
    office_df = load_office_points()
    coffee_df = load_coffee_points()

    records = []
    for _, s in subway_df.iterrows():
        station_name = str(s["name"])
        lng = float(s["longitude"])
        lat = float(s["latitude"])

        office_count = count_within_radius(lat, lng, office_df, RADIUS_M)
        coffee_count = count_within_radius(lat, lng, coffee_df, RADIUS_M)

        records.append(
            {
                "站点名称": station_name,
                "周边写字楼数": office_count,
                "周边咖啡馆数": coffee_count,
            }
        )

    result_df = pd.DataFrame(records)
    result_df["Demand"] = normalize_to_100(result_df["周边写字楼数"])
    result_df["Competition"] = normalize_to_100(result_df["周边咖啡馆数"])
    result_df["综合得分"] = result_df["Demand"] * 0.7 - result_df["Competition"] * 0.3

    result_df = result_df.sort_values("综合得分", ascending=False).reset_index(drop=True)
    result_df.insert(0, "排名", range(1, len(result_df) + 1))

    output_cols = ["排名", "站点名称", "周边写字楼数", "周边咖啡馆数", "综合得分"]
    result_df[output_cols].to_excel(OUTPUT_XLSX, index=False)

    print("=== Top 10 地铁站入驻潜力 ===")
    print(result_df[output_cols].head(10).to_string(index=False))
    print(f"\n已输出: {OUTPUT_XLSX}")


if __name__ == "__main__":
    main()

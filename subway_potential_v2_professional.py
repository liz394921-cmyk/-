import json
import re
from pathlib import Path

import pandas as pd
from geopy.distance import geodesic

BASE_DIR = Path(r"F:\Program Files\QGIS 3.44.9")
RADIUS_M = 500.0

SUBWAY_PATH = BASE_DIR / "tianhe_subway.csv"
V1_RANK_PATH = BASE_DIR / "subway_potential_ranking.xlsx"
OUTPUT_XLSX = BASE_DIR / "subway_v2_professional_ranking.xlsx"

OFFICE_CSV_PATH = BASE_DIR / "office_points.csv"
OFFICE_GEOJSON_PATH = BASE_DIR / "Tianhe_Office_GCJ02.geojson"
COFFEE_CSV_PATH = BASE_DIR / "coffee_poi.csv"
COFFEE_GEOJSON_PATH = BASE_DIR / "Tianhe_Coffee.geojson"
MALL_CSV_PATH = BASE_DIR / "tianhe_mall.csv"
MALL_GEOJSON_PATH = BASE_DIR / "tianhe_mall.geojson"

# 说明：当前 tianhe_subway.csv 不含线路字段。为满足“换乘站>1线路”逻辑，
# 使用天河区已知换乘站名单作为可解释替代。
TRANSFER_STATIONS = {
    "体育西路", "珠江新城", "车陂南", "广州东站", "燕塘", "天河客运站",
    "林和西", "员村", "黄村", "天河公园",
}


def clean_station_name(name: str) -> str:
    return re.sub(r"\s*[（(]地铁站[）)]\s*", "", str(name)).strip()


def pick_col(df: pd.DataFrame, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None


def normalize_0_100(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce").fillna(0.0)
    min_v = float(s.min())
    max_v = float(s.max())
    if max_v == min_v:
        if max_v == 0:
            return pd.Series([0.0] * len(s), index=s.index)
        return pd.Series([100.0] * len(s), index=s.index)
    return (s - min_v) / (max_v - min_v) * 100.0


def load_points_csv(path: Path, name_fallback: str):
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


def load_points_geojson(path: Path, name_fallback: str):
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
        try:
            lng = float(coords[0])
            lat = float(coords[1])
        except (TypeError, ValueError):
            continue
        name = str(ft.get("properties", {}).get("name", f"{name_fallback}_{i}"))
        rows.append({"name": name, "longitude": lng, "latitude": lat})

    return pd.DataFrame(rows)


def load_subway():
    if not SUBWAY_PATH.exists():
        raise FileNotFoundError(f"缺少地铁站数据: {SUBWAY_PATH}")
    df = load_points_csv(SUBWAY_PATH, "subway")
    df["station"] = df["name"].map(clean_station_name)
    return df[["station", "longitude", "latitude"]]


def load_office():
    if OFFICE_CSV_PATH.exists():
        return load_points_csv(OFFICE_CSV_PATH, "office")
    if OFFICE_GEOJSON_PATH.exists():
        return load_points_geojson(OFFICE_GEOJSON_PATH, "office")
    raise FileNotFoundError("未找到写字楼数据（office_points.csv 或 Tianhe_Office_GCJ02.geojson）")


def load_coffee():
    if COFFEE_CSV_PATH.exists():
        return load_points_csv(COFFEE_CSV_PATH, "coffee")
    if COFFEE_GEOJSON_PATH.exists():
        return load_points_geojson(COFFEE_GEOJSON_PATH, "coffee")
    raise FileNotFoundError("未找到咖啡馆数据（coffee_poi.csv 或 Tianhe_Coffee.geojson）")


def load_mall():
    if MALL_CSV_PATH.exists():
        return load_points_csv(MALL_CSV_PATH, "mall")
    if MALL_GEOJSON_PATH.exists():
        return load_points_geojson(MALL_GEOJSON_PATH, "mall")
    raise FileNotFoundError("未找到购物中心数据（tianhe_mall.csv 或 tianhe_mall.geojson）")


def count_within_radius(center_lat: float, center_lng: float, points_df: pd.DataFrame, radius_m: float):
    cnt = 0
    for _, row in points_df.iterrows():
        d = geodesic((center_lat, center_lng), (float(row["latitude"]), float(row["longitude"]))).meters
        if d <= radius_m:
            cnt += 1
    return cnt


def load_v1_rank():
    if not V1_RANK_PATH.exists():
        return pd.DataFrame(columns=["station", "old_rank"])

    v1 = pd.read_excel(V1_RANK_PATH)
    station_col = None
    rank_col = None
    for c in ["站点名称", "站点", "name"]:
        if c in v1.columns:
            station_col = c
            break
    for c in ["排名", "rank"]:
        if c in v1.columns:
            rank_col = c
            break

    if station_col is None or rank_col is None:
        return pd.DataFrame(columns=["station", "old_rank"])

    out = pd.DataFrame(
        {
            "station": v1[station_col].astype(str).map(clean_station_name),
            "old_rank": pd.to_numeric(v1[rank_col], errors="coerce"),
        }
    ).dropna(subset=["old_rank"])

    out["old_rank"] = out["old_rank"].astype(int)
    return out


def main():
    subway = load_subway()
    office = load_office()
    coffee = load_coffee()
    mall = load_mall()

    records = []
    for _, s in subway.iterrows():
        station = str(s["station"])
        lng = float(s["longitude"])
        lat = float(s["latitude"])

        office_cnt = count_within_radius(lat, lng, office, RADIUS_M)
        coffee_cnt = count_within_radius(lat, lng, coffee, RADIUS_M)
        mall_cnt = count_within_radius(lat, lng, mall, RADIUS_M)

        is_transfer = station in TRANSFER_STATIONS

        records.append(
            {
                "站点": station,
                "写字楼数": office_cnt,
                "咖啡店数": coffee_cnt,
                "购物中心数": mall_cnt,
                "是否换乘": "是" if is_transfer else "否",
                "transfer_raw": 1 if is_transfer else 0,
            }
        )

    df = pd.DataFrame(records)

    df["Office_Score"] = normalize_0_100(df["写字楼数"])
    df["Coffee_Score"] = normalize_0_100(df["咖啡店数"])
    df["Mall_Score"] = normalize_0_100(df["购物中心数"])
    df["Transfer_Bonus"] = normalize_0_100(df["transfer_raw"])

    df["V2 综合得分"] = (
        df["Office_Score"] * 0.5
        - df["Coffee_Score"] * 0.2
        + df["Mall_Score"] * 0.2
        + df["Transfer_Bonus"] * 0.1
    )

    df = df.sort_values("V2 综合得分", ascending=False).reset_index(drop=True)
    df.insert(0, "排名", range(1, len(df) + 1))

    out_cols = ["排名", "站点", "写字楼数", "咖啡店数", "购物中心数", "是否换乘", "V2 综合得分"]
    df[out_cols].to_excel(OUTPUT_XLSX, index=False)

    # 与V1对比，找出排名上升最快的黑马
    v1 = load_v1_rank()
    compare = df[["站点", "排名"]].rename(columns={"排名": "new_rank"}).merge(v1, left_on="站点", right_on="station", how="left")
    compare = compare.drop(columns=["station"]) if "station" in compare.columns else compare
    compare["rank_up"] = compare["old_rank"] - compare["new_rank"]
    blackhorse = compare.dropna(subset=["rank_up"]).sort_values("rank_up", ascending=False).head(5)

    print("=== V2 Top 10 站点 ===")
    print(df[out_cols].head(10).to_string(index=False))

    print("\n=== V2 排名上升最快潜力黑马（相对V1）===")
    if len(blackhorse) == 0:
        print("未找到可对比的V1排名数据。")
    else:
        for _, r in blackhorse.iterrows():
            print(f"{r['站点']}: V1第{int(r['old_rank'])} -> V2第{int(r['new_rank'])}, 上升{int(r['rank_up'])}位")

    print(f"\n已输出: {OUTPUT_XLSX}")
    print("注: tianhe_subway.csv 不含线路字段，换乘判定基于天河已知换乘站名单。")


if __name__ == "__main__":
    main()

import csv
import json
import math
import os
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# Determine output path based on environment or fallback
_project_root = Path(__file__).parent
_env_data_dir = os.getenv("OPENCLAW_DATA_DIR")
if _env_data_dir:
    OUTPUT_PATH = Path(_env_data_dir) / "manhattan_poi.csv"
else:
    # Try container path first, then fallback to project data directory
    container_path = Path("/workspace/data/manhattan_poi.csv")
    if container_path.parent.exists():
        OUTPUT_PATH = container_path
    else:
        OUTPUT_PATH = _project_root / "data" / "manhattan_poi.csv"
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
}

# Manhattan approximate bounding box
BBOX = {
    "south": 40.7000,
    "west": -74.0210,
    "north": 40.8800,
    "east": -73.9100,
}

QUERIES = [
    'node["amenity"="cafe"]({south},{west},{north},{east});',
    'way["amenity"="cafe"]({south},{west},{north},{east});',
    'relation["amenity"="cafe"]({south},{west},{north},{east});',
    'node["amenity"="subway_entrance"]({south},{west},{north},{east});',
    'way["amenity"="subway_entrance"]({south},{west},{north},{east});',
    'relation["amenity"="subway_entrance"]({south},{west},{north},{east});',
    'node["railway"="subway_entrance"]({south},{west},{north},{east});',
    'way["railway"="subway_entrance"]({south},{west},{north},{east});',
    'relation["railway"="subway_entrance"]({south},{west},{north},{east});',
    'node["station"="subway"]({south},{west},{north},{east});',
    'way["station"="subway"]({south},{west},{north},{east});',
    'relation["station"="subway"]({south},{west},{north},{east});',
    'node["building"="office"]({south},{west},{north},{east});',
    'way["building"="office"]({south},{west},{north},{east});',
    'relation["building"="office"]({south},{west},{north},{east});',
    'node["office"]({south},{west},{north},{east});',
    'way["office"]({south},{west},{north},{east});',
    'relation["office"]({south},{west},{north},{east});',
]


def build_query(bbox: dict) -> str:
    query_parts = [q.format(**bbox) for q in QUERIES]
    query = "[out:json][timeout:120];(" + "".join(query_parts) + ");out center qt;"
    return query


def fetch_overpass(bbox: dict) -> dict:
    query = build_query(bbox).encode("utf-8")
    req = urllib.request.Request(OVERPASS_URL, data=query, headers=HEADERS, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            text = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            raise RuntimeError("429 Too Many Requests")
        raise
    return json.loads(text)


def split_bbox(bbox: dict, rows: int = 2, cols: int = 2) -> list[dict]:
    lat_step = (bbox["north"] - bbox["south"]) / rows
    lon_step = (bbox["east"] - bbox["west"]) / cols
    boxes = []
    for i in range(rows):
        for j in range(cols):
            boxes.append({
                "south": bbox["south"] + lat_step * i,
                "north": bbox["south"] + lat_step * (i + 1),
                "west": bbox["west"] + lon_step * j,
                "east": bbox["west"] + lon_step * (j + 1),
            })
    return boxes


def extract_elements(data: dict) -> list[dict]:
    elements = []
    seen = set()
    for element in data.get("elements", []):
        tags = element.get("tags", {})
        if not tags:
            continue
        key = (element.get("type"), element.get("id"))
        if key in seen:
            continue
        seen.add(key)

        if element["type"] == "node":
            lat = element.get("lat")
            lon = element.get("lon")
        else:
            center = element.get("center") or element.get("bounds")
            lat = center.get("lat") if center else None
            lon = center.get("lon") if center else None

        if lat is None or lon is None:
            continue

        element_type = None
        if tags.get("amenity") == "cafe":
            element_type = "cafe"
        elif tags.get("amenity") == "subway_entrance" or tags.get("railway") == "subway_entrance" or tags.get("station") == "subway":
            element_type = "subway_entrance"
        elif tags.get("building") == "office" or tags.get("office"):
            element_type = "office"
        else:
            continue

        elements.append({
            "name": tags.get("name", ""),
            "lon": lon,
            "lat": lat,
            "type": element_type,
        })
    return elements


def save_csv(results: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "lon", "lat", "type"])
        writer.writeheader()
        for item in results:
            writer.writerow(item)


def main() -> None:
    print("开始抓取 OSM POI 数据，范围：纽约县 Manhattan")
    try:
        data = fetch_overpass(BBOX)
        print(f"首次查询返回 {len(data.get('elements', []))} 个元素")
    except RuntimeError as exc:
        print(f"遇到 429 需要分块抓取：{exc}")
        data = {"elements": []}
        boxes = split_bbox(BBOX, rows=3, cols=3)
        for idx, box in enumerate(boxes, 1):
            print(f"分块抓取 {idx}/{len(boxes)}: {box}")
            time.sleep(random.uniform(2, 3))
            try:
                chunk = fetch_overpass(box)
                elements = chunk.get("elements", [])
                print(f"  返回 {len(elements)} 个元素")
                data["elements"].extend(elements)
            except Exception as e:
                print(f"  分块 {idx} 抓取失败：{e}")
                continue
    else:
        if len(data.get("elements", [])) > 50000:
            print("首次查询结果过大，改为分块抓取")
            data = {"elements": []}
            boxes = split_bbox(BBOX, rows=3, cols=3)
            for idx, box in enumerate(boxes, 1):
                print(f"分块抓取 {idx}/{len(boxes)}: {box}")
                time.sleep(random.uniform(2, 3))
                try:
                    chunk = fetch_overpass(box)
                    data["elements"].extend(chunk.get("elements", []))
                except Exception as e:
                    print(f"  分块 {idx} 抓取失败：{e}")
                    continue

    results = extract_elements(data)
    print(f"提取最终 POI 数量：{len(results)}")

    if len(results) < 50:
        print("当前抽取点位少于 50 个，尝试备用标签二次抽取")
        fallback_queries = [
            'node["public_transport"="station"]({south},{west},{north},{east});',
            'way["public_transport"="station"]({south},{west},{north},{east});',
            'relation["public_transport"="station"]({south},{west},{north},{east});',
            'node["railway"="station"]({south},{west},{north},{east});',
            'way["railway"="station"]({south},{west},{north},{east});',
            'relation["railway"="station"]({south},{west},{north},{east});',
        ]
        backup_query = "[out:json][timeout:120];(" + "".join(q.format(**BBOX) for q in fallback_queries) + ");out center qt;"
        try:
            response = requests.post(OVERPASS_URL, data=backup_query, headers=HEADERS, timeout=180)
            response.raise_for_status()
            backup_data = response.json()
            backup_results = extract_elements(backup_data)
            print(f"备用标签抽取结果数量：{len(backup_results)}")
            if len(backup_results) > len(results):
                results = backup_results
                print("已使用备用标签结果替换初次抽取结果。")
            else:
                print("备用标签结果未优于初次抽取结果，保留原结果。")
        except Exception as e:
            print(f"备用标签抽取失败：{e}")

    save_csv(results, OUTPUT_PATH)
    print(f"保存完成：{OUTPUT_PATH}")
    print("请确认容器内路径 /home/node/.openclaw/data/manhattan_poi.csv 是否可见。")


if __name__ == "__main__":
    main()

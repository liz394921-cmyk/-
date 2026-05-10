import csv
import os
import random
import time
from dataclasses import dataclass
from pathlib import Path

# Determine data paths based on environment with fallback
_project_root = Path(__file__).parent
_env_data_dir = os.getenv("OPENCLAW_DATA_DIR")

if _env_data_dir:
    # Use environment variable if set
    DATA_DIR = Path(_env_data_dir)
    INPUT_CSV = DATA_DIR / "manhattan_demographics.csv"
    OUTPUT_CSV = DATA_DIR / "golden_selection_v1.csv"
else:
    # Try container path first, then fallback to project data directory
    container_input = Path("/home/node/.openclaw/data/manhattan_demographics.csv")
    if container_input.parent.exists():
        INPUT_CSV = container_input
        OUTPUT_CSV = Path("/home/node/.openclaw/data/golden_selection_v1.csv")
    else:
        # Use project data directory
        INPUT_CSV = _project_root / "data" / "manhattan_demographics.csv"
        OUTPUT_CSV = _project_root / "data" / "golden_selection_v1.csv"
        OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

@dataclass
class TractRecord:
    state: str
    county: str
    tract: str
    income: int
    population: int
    target_young_population: int


def read_records(path: Path) -> list[TractRecord]:
    records = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                income = int(row["B19013_001E"])
            except ValueError:
                continue
            try:
                population = int(row["B01003_001E"])
                target_young = int(row["target_young_population"])
            except ValueError:
                continue
            records.append(
                TractRecord(
                    state=row["state"],
                    county=row["county"],
                    tract=row["tract"],
                    income=income,
                    population=population,
                    target_young_population=target_young,
                )
            )
    return records


def sample_random(records: list[TractRecord], count: int = 5) -> list[TractRecord]:
    if len(records) <= count:
        return records[:]
    return random.sample(records, count)


def filter_middle_upper(records: list[TractRecord]) -> list[TractRecord]:
    filtered = []
    for record in records:
        if record.income == -666666666:
            print(f"[皱眉] 跳过异常收入记录：tract={record.tract}, income={record.income}")
            continue
        if 80000 <= record.income <= 150000:
            filtered.append(record)
    return filtered


def save_selection(path: Path, records: list[TractRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "state",
            "county",
            "tract",
            "B19013_001E",
            "B01003_001E",
            "target_young_population",
        ])
        for r in records:
            writer.writerow([
                r.state,
                r.county,
                r.tract,
                r.income,
                r.population,
                r.target_young_population,
            ])


def main() -> None:
    print("[步骤1] Human-Mimicry: 读取本地 Census 数据，并随机采样 5 个街区。")
    records = read_records(INPUT_CSV)
    total_count = len(records)
    print(f"共读取 {total_count} 条有效记录。")
    random.seed(42)
    sample = sample_random(records, 5)
    for rec in sample:
        remark = "这里的收入水平确实很高。" if rec.income > 100000 else "这里的收入水平看起来比较稳健。"
        print(f"随机浏览：tract={rec.tract}, income={rec.income}, young={rec.target_young_population} -> {remark}")
    time.sleep(random.uniform(2, 3))

    print("[步骤2] Segmenting：筛选出收入 8 万到 15 万美元之间的街区。")
    filtered = filter_middle_upper(records)
    print(f"筛选后得到 {len(filtered)} 个中产及以上街区。")
    time.sleep(random.uniform(2, 3))

    print("[步骤3] Targeting：从中产区中挑选 target_young_population 最高的前 10 个街区。")
    selected = sorted(filtered, key=lambda r: r.target_young_population, reverse=True)[:10]
    print("前 10 个黄金街区：")
    for idx, rec in enumerate(selected, 1):
        print(f"{idx}. tract={rec.tract}, income={rec.income}, young={rec.target_young_population}")
    time.sleep(random.uniform(2, 3))

    avg_income = sum(r.income for r in records if r.income != -666666666) / len([r for r in records if r.income != -666666666])
    avg_young = sum(r.target_young_population for r in records) / total_count
    selected_avg_income = sum(r.income for r in selected) / len(selected) if selected else 0
    selected_avg_young = sum(r.target_young_population for r in selected) / len(selected) if selected else 0

    print("[汇总] 黄金选址与总体平均对比：")
    print(f"总体平均收入：{avg_income:.2f}，黄金选址平均收入：{selected_avg_income:.2f}")
    print(f"总体平均年轻人口：{avg_young:.2f}，黄金选址平均年轻人口：{selected_avg_young:.2f}")

    print(f"正在保存黄金选址结果到 {OUTPUT_CSV}")
    save_selection(OUTPUT_CSV, selected)
    print("保存完成。")


if __name__ == '__main__':
    main()

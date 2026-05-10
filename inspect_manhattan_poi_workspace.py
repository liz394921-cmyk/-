import csv
from collections import Counter
from pathlib import Path

path = Path('/workspace/data/manhattan_poi.csv')
with path.open('r', encoding='utf-8-sig', newline='') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

counts = Counter(r.get('type', '').strip() for r in rows)
out_of_range = []
for i, r in enumerate(rows, 1):
    try:
        lat = float(r.get('lat', ''))
        lon = float(r.get('lon', ''))
    except Exception:
        out_of_range.append((i, r.get('name', ''), r.get('lat', ''), r.get('lon', ''), 'invalid'))
        continue
    if not (-74.02 <= lon <= -73.90 and 40.70 <= lat <= 40.88):
        out_of_range.append((i, r.get('name', ''), lat, lon, 'out'))

print('HEADERS: [name, lon, lat, type]')
print('TOTAL_ROWS:', len(rows))
print('TYPE_COUNTS:', dict(counts))
print('OUT_OF_RANGE_COUNT:', len(out_of_range))
if out_of_range:
    print('OUT_OF_RANGE_SAMPLES:')
    for item in out_of_range[:10]:
        print(item)

cafes = [r for r in rows if r.get('type', '').strip() == 'cafe']
subs = [r for r in rows if r.get('type', '').strip() == 'subway_entrance']
print('SAMPLE_CAFE1:', cafes[0] if cafes else 'NONE')
print('SAMPLE_CAFE2:', cafes[1] if len(cafes) > 1 else 'NONE')
print('SAMPLE_SUBWAY:', subs[0] if subs else 'NONE')

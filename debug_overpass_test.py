import requests

query = '[out:json][timeout:120];(node["railway"="subway_entrance"](40.7,-74.021,40.88,-73.91););out center qt;'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Accept': 'application/json',
}
resp = requests.post('https://overpass-api.de/api/interpreter', data=query, headers=headers, timeout=120)
resp.raise_for_status()
print('status', resp.status_code)
print('count', len(resp.json().get('elements', [])))
for i, el in enumerate(resp.json().get('elements', [])[:10], 1):
    print(i, el.get('type'), el.get('id'), el.get('tags', {}))

import requests, json

url = "http://127.0.0.1:8000/query-items"
payload = {
    "user_id": "1",
    "query": "mental healthcare privilege",
    "top_k": 3,
    # "from_timestamp": 1600000000,
    # "platform": "tiktok",
}
r = requests.post(url, json=payload)
print(r.status_code)
print(json.dumps(r.json(), indent=2, ensure_ascii=False))

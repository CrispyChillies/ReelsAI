import requests
import json
from apify_client import ApifyClient

# =================== THÔNG SỐ ===================
APIFY_TOKEN = 'apify_api_O9utrfdHHQynT83hW0sGydxQ3DVX4s33av3b'
BEARER_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzYzNTMyNjc1LCJpYXQiOjE3NjM0NDYyNzUsImp0aSI6IjFhODc4ZjEyYzhjMDRmNGNiZjFiN2EwYzhlNGM0M2NlIiwidXNlcl9pZCI6IjYifQ.00GOgdeZlixujIiJ7VvG39cuquP86s42xWbLHtPBgNI'

ACTOR_ID = "clockworks/tiktok-scraper"
# Danh sách các industry_id
INDUSTRY_IDS = ["10000000000", "15000000000", "29000000000", "13000000000", "27000000000", "22000000000", "12000000000", "14000000000", "25000000000", "21000000000", "18000000000", "26000000000", "23000000000", "19000000000", "28000000000", "17000000000", "11000000000"]

client = ApifyClient(APIFY_TOKEN)
print(" Apify Client đã khởi tạo thành công.")

headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
top_hashtags = []
for industry_id in INDUSTRY_IDS:
    api_url = f"http://127.0.0.1:8000/api/top-hashtags/?industry_id={industry_id}"
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, list) or not data:
            raise ValueError(f"API trả về dữ liệu không hợp lệ cho industry_id {industry_id}")

        # Thêm hashtags từ industry_id hiện tại
        top_hashtags.extend([h["hashtag"] for h in data[:3]])
        print(f"\n=== TOP 3 HASHTAG cho industry_id {industry_id} ===")
        for i, tag in enumerate(data[:3], 1):
            print(f"{i}. #{tag['hashtag']}")

    except Exception as e:
        print(f"Lỗi khi lấy hashtags từ API cho industry_id {industry_id}:", e)
        continue

run_input = {
    "excludePinnedPosts": False,
    "hashtags": top_hashtags,
    "resultsPerPage": 5,
    "scrapeRelatedVideos": False,
    "shouldDownloadAvatars": True,
    "shouldDownloadCovers": True,
    "shouldDownloadMusicCovers": True,
    "shouldDownloadSlideshowImages": True,
    "shouldDownloadSubtitles": True,
    "shouldDownloadVideos": True
}

# =================== Chạy Actor ===================
print("\n⏳ Đang chạy Actor TikTok Scraper...")
run = client.actor(ACTOR_ID).call(run_input=run_input)
print(f"Run ID: {run['id']} -> Trạng thái cuối: {run['status']}")

# =================== Lấy dataset trả về ===================
dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items
print(f" Đã lấy {len(dataset_items)} items từ dataset.")

# =================== Lưu nguyên dữ liệu vào JSON ===================
with open("tiktok_videos_full.json", "w", encoding="utf-8") as f:
    json.dump(dataset_items, f, ensure_ascii=False, indent=4)

print("\n Toàn bộ dữ liệu từ Apify đã được lưu vào 'tiktok_videos_full.json'.")

from apify_client import ApifyClient
import os
from dotenv import load_dotenv

load_dotenv()

# Thay bằng API Token của bạn
APIFY_TOKEN = os.getenv("APIFY_TOKEN")


def fetch_tiktok_videos(keywords: list, max_items: int = 5):
    client = ApifyClient(APIFY_TOKEN)

    # --- SỬA LỖI TẠI ĐÂY ---
    # Actor yêu cầu key là "searchQueries" thay vì "search"
    run_input = {
        "searchQueries": keywords,  # ĐÃ SỬA
        "resultsPerPage": max_items,
        "proxyConfiguration": {"useApifyProxy": True},
        # Tắt bớt các thứ không cần thiết để chạy nhanh hơn
        "shouldDownloadCovers": False,
        "shouldDownloadSlideshowImages": False,
        "shouldDownloadVideos": True,
        "searchSection": "/video",  # Chỉ định tìm video (tránh tìm user)
    }

    print(f"🚀 Đang gửi yêu cầu tới Apify cho keywords: {keywords}...")

    try:
        run = client.actor("clockworks/tiktok-scraper").call(run_input=run_input)
    except Exception as e:
        print(f"❌ Lỗi khi gọi Apify: {e}")
        return []

    if not run:
        print("❌ Không khởi tạo được Run.")
        return []

    # Lấy kết quả từ dataset
    dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items
    print(dataset_items[0])

    cleaned_data = []
    for item in dataset_items:
        try:
            # Cấu trúc item trả về có thể thay đổi tùy video, nên dùng .get() an toàn
            video_url = item.get("webVideoUrl")
            media_url = item.get("videoMeta", {}).get("downloadAddr")

            # Nếu không có video url thì bỏ qua
            if not video_url:
                continue

            video_info = {
                "platform": "tiktok",
                "id": item.get("id"),
                "desc": item.get("text", ""),
                "author": item.get("authorMeta", {}).get("name", "Unknown"),
                "video_url": video_url,
                "duration": item.get("videoMeta", {}).get("duration", 0),
                # Lấy hashtag an toàn hơn
                "hashtags": (
                    [tag.get("name") for tag in item.get("hashtags", [])]
                    if item.get("hashtags")
                    else []
                ),
                "mediaUrls": media_url,  # Thêm trường mediaUrls để tải video nhanh hơn
            }
            cleaned_data.append(video_info)
        except Exception as e:
            continue  # Bỏ qua item lỗi

    print(f"✅ Đã tìm thấy {len(cleaned_data)} videos.")
    print(cleaned_data)
    return cleaned_data


# --- TEST THỬ ---
if __name__ == "__main__":
    # Giả sử user quan tâm đến AI và Python
    results = fetch_tiktok_videos(
        keywords=["ai tutorial", "python coding"], max_items=3
    )

    for vid in results:
        print(f"[-] {vid['author']}: {vid['desc'][:50]}... | Link: {vid['video_url']}")

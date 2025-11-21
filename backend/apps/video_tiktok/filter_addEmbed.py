import asyncio
import httpx
import json
import os

# oembed
async def fetch_oembed(url):
    api = f"https://www.tiktok.com/oembed?url={url}"
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(api, timeout=10)
        if r.status_code == 200:
            return r.json().get("html")
        return None
    except:
        return None

async def extract_video_info(item):
    hashtags = ",".join([h["name"] for h in item.get("hashtags", [])])

    web_url = item.get("webVideoUrl")
    embed = await fetch_oembed(web_url) if web_url else None

    return {
        "id": item.get("id"),
        "text": item.get("text"),
        "author_username": item.get("authorMeta", {}).get("name"),
        "author_profile_url": item.get("authorMeta", {}).get("profileUrl"),
        "webVideoUrl": web_url,
        "mediaUrls": ",".join(item.get("mediaUrls", [])),
        "diggCount": item.get("diggCount"),
        "shareCount": item.get("shareCount"),
        "playCount": item.get("playCount"),
        "collectCount": item.get("collectCount"),
        "commentCount": item.get("commentCount"),
        "hashtags": hashtags,
        "embed_code": embed
    }

async def process_json(input_file="input.json", output_file="output.json"):

    if not os.path.exists(input_file):
        print(f"Không tìm thấy file: {input_file}")
        return

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        data = [data]

    results = []
    for item in data:
        filtered = await extract_video_info(item)
        results.append(filtered)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

    print(f"Đã tạo file JSON: {output_file}")


asyncio.run(process_json("tiktok_videos_full.json", "tiktok_videos_embedded.json"))

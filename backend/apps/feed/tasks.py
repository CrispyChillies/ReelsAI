# feeds/tasks.py
from celery import shared_task
from .models import PersonalFeed, SocialPost, FeedItem

# Import các class utils của bạn (đảm bảo bạn đã copy file vào folder feeds/utils/)
from .utils.planner import BonsaiPlanner
from .utils.sourcer import BonsaiSourcer
from .utils.curator import BonsaiCurator
from .utils.tiktok_ingestion import fetch_tiktok_videos
from .utils.video_processor import VideoPreprocessor
from .utils.ai_engine import GeminiEngine
import os
import requests


@shared_task(name="update_feed_task")
def update_feed_task(feed_id):
    """
    Task này sẽ được RabbitMQ phân phối cho Worker.
    """
    try:
        feed = PersonalFeed.objects.get(id=feed_id)
    except PersonalFeed.DoesNotExist:
        return "Feed not found"

    print(f"🐇 RabbitMQ Worker: Đang xử lý feed {feed.title} ({feed.platform})...")

    # 1. PLANNING (Nếu cần refresh lại plan)
    planner = BonsaiPlanner()
    if not feed.search_queries:  # Chỉ generate nếu chưa có
        plan = planner.generate_plan(feed.user_intent)
        if plan:
            feed.search_queries = plan.get("search_queries", [])
            feed.include_criteria = plan.get("include_criteria", "")
            feed.exclude_criteria = plan.get("exclude_criteria", "")
            feed.save()

    criteria = {
        "include_criteria": feed.include_criteria,
        "exclude_criteria": feed.exclude_criteria,
    }

    # 2. PROCESSING (Rẽ nhánh)
    if feed.platform == "bluesky":
        _process_bluesky(feed, criteria)
    elif feed.platform == "tiktok":
        _process_tiktok(feed, criteria)

    return f"✅ Finished updating feed {feed_id}"


def fetch_tiktok_oembed_sync(url):
    """
    Gọi TikTok OEmbed API để lấy mã HTML hiển thị video.
    """
    if not url:
        return None

    api = f"https://www.tiktok.com/oembed?url={url}"
    try:
        # Timeout 5s để không làm treo worker quá lâu
        r = requests.get(api, timeout=5)
        if r.status_code == 200:
            return r.json().get("html")
        else:
            print(f"⚠️ OEmbed Error {r.status_code} for {url}")
    except Exception as e:
        print(f"⚠️ OEmbed Exception: {e}")
    return None


def _process_bluesky(feed, criteria):
    sourcer = BonsaiSourcer()
    curator = BonsaiCurator()

    for query in feed.search_queries:
        # Gọi sourcer (đảm bảo sourcer.py đã được update để trả về key 'images')
        posts = sourcer.get_posts_by_query(query, limit=5)

        for p in posts:
            try:
                # --- 1. XỬ LÝ ẢNH ---
                # Kiểm tra nếu bài viết có danh sách ảnh, lấy cái đầu tiên làm thumbnail
                image_url = None
                if p.get("images") and len(p["images"]) > 0:
                    image_url = p["images"][0]

                # --- 2. LƯU CACHE (SocialPost) ---
                post_obj, _ = SocialPost.objects.update_or_create(
                    platform_id=p["uri"],
                    defaults={
                        "platform": "bluesky",
                        "author": p["author"],
                        "content": p["content"],
                        # Dùng .get() để an toàn nếu field bị thiếu
                        "like_count": p.get("like_count", 0),
                        "repost_count": p.get("repost_count", 0),
                        "reply_count": p.get("reply_count", 0),
                        # Lưu thời gian tạo bài gốc (quan trọng cho việc sort độ mới)
                        "created_at_source": p.get("created_at"),
                        # Lưu Link Ảnh
                        "thumbnail_url": image_url,
                        "source_link": p.get("post_url"),
                    },
                )

                # --- 3. AI CHẤM ĐIỂM (Curator) ---
                # Chỉ chấm điểm nếu bài này chưa có trong Feed hiện tại
                if not FeedItem.objects.filter(feed=feed, post=post_obj).exists():
                    rating = curator.rate_post(p["content"], criteria)

                    # Chỉ lưu bài đạt chuẩn (Score >= 4)
                    if rating["score"] >= 4:
                        FeedItem.objects.create(
                            feed=feed,
                            post=post_obj,
                            ai_score=rating["score"],
                            ai_reasoning=rating["reasoning"],
                            ai_summary=rating.get("summary", ""),
                        )

            except Exception as e:
                print(f"⚠️ Lỗi xử lý bài viết {p.get('uri')}: {e}")
                continue


def _process_tiktok(feed, criteria):
    video_processor = VideoPreprocessor()
    gemini = GeminiEngine()

    # Gọi Apify lấy link
    raw_videos = fetch_tiktok_videos(feed.search_queries, max_items=3)

    for vid in raw_videos:
        # Lưu Cache
        video_url = vid.get("video_url")
        embed_html = fetch_tiktok_oembed_sync(video_url)

        post_obj, _ = SocialPost.objects.update_or_create(
            platform_id=video_url,
            defaults={
                "platform": "tiktok",
                "author": vid["author"],
                "content": vid["desc"],  # Caption gốc
                "thumbnail_url": vid.get("author_avatar"),
                # Metrics tương tác
                "like_count": vid.get("like_count", 0),
                "repost_count": vid.get("repost_count", 0),
                "reply_count": vid.get("reply_count", 0),
                "created_at_source": vid.get("created_at"),
                "source_link": video_url,
                "embed_quote": embed_html,
            },
        )

        # AI Phân tích Video
        if not FeedItem.objects.filter(feed=feed, post=post_obj).exists():
            video_path = video_processor.download_video(vid)
            if video_path:
                # Gọi Gemini 1.5 Flash
                analysis = gemini.analyze_video(video_path, post_text=vid["desc"])

                # Dọn dẹp file
                try:
                    os.remove(video_path)
                except:
                    pass

                if analysis:
                    score = 8 if analysis.get("is_relevant_to_intent") else 2
                    if score >= 4:
                        FeedItem.objects.create(
                            feed=feed,
                            post=post_obj,
                            ai_score=score,
                            ai_reasoning=analysis.get("reasoning"),
                            ai_summary=analysis.get("transcript_summary"),
                        )

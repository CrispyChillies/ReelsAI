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


def _process_bluesky(feed, criteria):
    sourcer = BonsaiSourcer()
    curator = BonsaiCurator()

    for query in feed.search_queries:
        posts = sourcer.get_posts_by_query(query, limit=5)
        for p in posts:
            # Lưu vào Cache (SocialPost)
            post_obj, _ = SocialPost.objects.update_or_create(
                platform_id=p["uri"],
                defaults={
                    "platform": "bluesky",
                    "author": p["author"],
                    "content": p["content"],
                    "like_count": p["like_count"],
                    "repost_count": p["repost_count"],
                },
            )
            # AI Chấm điểm (Nếu chưa chấm)
            if not FeedItem.objects.filter(feed=feed, post=post_obj).exists():
                rating = curator.rate_post(p["content"], criteria)
                if rating["score"] >= 4:
                    FeedItem.objects.create(
                        feed=feed,
                        post=post_obj,
                        ai_score=rating["score"],
                        ai_reasoning=rating["reasoning"],
                    )


def _process_tiktok(feed, criteria):
    video_processor = VideoPreprocessor()
    gemini = GeminiEngine()

    # Gọi Apify lấy link
    raw_videos = fetch_tiktok_videos(feed.search_queries, max_items=3)

    for vid in raw_videos:
        # Lưu Cache
        post_obj, _ = SocialPost.objects.update_or_create(
            platform_id=vid["video_url"],
            defaults={
                "platform": "tiktok",
                "author": vid["author"],
                "content": vid["desc"],  # Caption gốc
                "media_url": vid.get("mediaUrls"),
                "thumbnail_url": vid.get(
                    "thumbnail_url"
                ),  # Cần sửa fetch_tiktok_videos trả về cái này
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

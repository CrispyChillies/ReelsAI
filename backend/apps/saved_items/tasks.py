import requests
import logging
import time
from celery import shared_task
from django.conf import settings
from .models import UserSavedItem

# Import model FeedItem để lấy dữ liệu AI Summary
from apps.feed.models import FeedItem

logger = logging.getLogger(__name__)


@shared_task(name="push_to_rag_task")
def push_to_rag_task(saved_item_id):
    """
    Task đồng bộ dữ liệu sang RAG.
    Logic: Ưu tiên lấy 'ai_summary' cho CẢ Bluesky Posts và TikTok Videos.
    """
    try:
        # 1. Lấy thông tin UserSavedItem và SocialPost liên quan
        saved_item = UserSavedItem.objects.select_related("post").get(id=saved_item_id)
        post = saved_item.post
        user = saved_item.user

        logger.info(
            f"🚀 Processing RAG for Saved Item {saved_item.id} (User {user.id})"
        )

        # 2. Tìm dữ liệu AI Analysis (FeedItem)
        # Một bài post có thể nằm trong nhiều feed, ta lấy bản ghi có điểm cao nhất (chất lượng nhất)
        feed_item = FeedItem.objects.filter(post=post).order_by("-ai_score").first()

        summary_text = ""

        # --- LOGIC HỢP NHẤT (UNIFIED LOGIC) ---
        if feed_item and feed_item.ai_summary:
            # Trường hợp lý tưởng: Cả Video và Post đều đã có AI tóm tắt
            summary_text = feed_item.ai_summary
            logger.info(f"✅ Using AI Summary (Source: {post.platform})")
        elif post.content:
            # Fallback: Nếu AI bị lỗi hoặc chưa chạy kịp, dùng nội dung gốc (Caption/Text)
            summary_text = post.content
            logger.warning(
                f"⚠️ AI Summary missing, falling back to raw content (Source: {post.platform})"
            )
        else:
            logger.error(
                "❌ No content available to index (Empty summary & Empty content)"
            )
            return

        # 3. Chuẩn bị Payload gửi sang RAG Service
        rag_payload = {
            "content_id": str(post.id),  # VARCHAR(64) - Dùng ID gốc (URL/URI)
            "content_url": str(post.platform_id),  # VARCHAR(256) - URL
            "user_id": str(user.id),  # VARCHAR(64)
            "platform": post.platform,  # VARCHAR(20) ('tiktok'/'bluesky')
            "summary": summary_text,  # VARCHAR(4000) - Nội dung text để embedding
            "timestamp": int(time.time()),  # INT64 - Unix Timestamp
            # Các trường phụ trợ (Milvus không lưu, nhưng API RAG có thể cần để log hoặc xử lý)
            "tags": saved_item.tags,
            "media_url": post.media_url,
        }

        # 4. Gửi API
        rag_api_url = settings.SERVICE_URLS.get("RAG_API_URL")
        if not rag_api_url:
            logger.error("❌ RAG_API_URL not configured in settings")
            return

        logger.info(f"📤 Sending to RAG: {rag_api_url}")

        response = requests.put(rag_api_url, json=rag_payload, timeout=30)

        # 5. Xử lý kết quả
        if response.status_code < 400:
            saved_item.is_rag_indexed = True
            saved_item.save()
            logger.info(f"✅ Successfully indexed to RAG. ID: {post.id}")
        else:
            logger.error(f"❌ RAG API Failed: {response.status_code} - {response.text}")

    except UserSavedItem.DoesNotExist:
        logger.error(f"❌ SavedItem {saved_item_id} does not exist")
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Network error calling RAG: {e}")
    except Exception as e:
        logger.exception(f"❌ Unexpected error in push_to_rag_task: {e}")

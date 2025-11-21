import time
import os

# Import Bluesky Modules
from sourcer import BonsaiSourcer
from planner import BonsaiPlanner
from curator import BonsaiCurator
from ranker import BonsaiRanker

# Import TikTok Modules
from tiktok_ingestion import fetch_tiktok_videos
from video_processor import VideoPreprocessor
from ai_engine import GeminiEngine  # File này chứa class GeminiEngine bạn đã sửa


def process_bluesky_flow(plan, sourcer, curator):
    """Quy trình xử lý Text Post từ Bluesky"""
    print("\n🔵 [MODE: BLUESKY POSTS] Đang kích hoạt...")
    raw_posts = []

    # 1. Sourcing
    print("   📡 Sourcing: Đang quét dữ liệu từ Bluesky...")
    for query in plan.get("search_queries", []):
        found_posts = sourcer.get_posts_by_query(query, limit=5)
        raw_posts.extend(found_posts)
        time.sleep(0.5)

    unique_posts = {p["uri"]: p for p in raw_posts}.values()
    print(f"   ✅ Tìm thấy {len(unique_posts)} bài viết thô.")

    # 2. Curating
    print("   ⚖️ Curating: AI Judge (Text) đang chấm điểm...")
    curated_posts = []
    criteria = {
        "include_criteria": plan.get("include_criteria"),
        "exclude_criteria": plan.get("exclude_criteria"),
    }

    for post in unique_posts:
        rating = curator.rate_post(post["content"], criteria)
        post["curator_score"] = rating["score"]
        post["curator_reason"] = rating["reasoning"]

        print(
            f"   📝 [{rating['score']}/10] {post['content'][:30]}... -> {rating['reasoning']}"
        )

        if rating["score"] >= 4:
            curated_posts.append(post)

    return curated_posts


def process_tiktok_flow(plan, video_processor, gemini_engine):
    """Quy trình xử lý Video từ TikTok"""
    print("\n🎵 [MODE: TIKTOK VIDEOS] Đang kích hoạt...")

    # 1. Sourcing (Apify)
    print(f"   📡 Sourcing: Đang gọi Apify để tìm video...")
    # Lấy danh sách từ khóa từ Planner
    keywords = plan.get("search_queries", [])
    # Gọi hàm từ tiktok_ingestion.py
    raw_videos = fetch_tiktok_videos(keywords, max_items=3)  # Demo nên để ít (3 video)

    processed_videos = []

    # 2. Processing & Curating (Gemini)
    print("   ⚖️ Curating: AI Judge (Multimodal) đang xem video...")

    for vid in raw_videos:
        print(f"\n   ▶️ Đang xử lý video: {vid['id']} ({vid['desc'][:30]}...)")

        # A. Download Video
        video_path = video_processor.download_video(vid)
        if not video_path:
            continue

        # B. Analyze with Gemini
        # Gemini trả về JSON: {transcript_summary, visual_description, is_relevant_to_intent, reasoning}
        analysis = gemini_engine.analyze_video(video_path, post_text=vid["desc"])

        if analysis:
            # C. Mapping Data (Chuẩn hóa dữ liệu để khớp với Ranker)
            # Chuyển đổi 'is_relevant' thành điểm số (Score)
            score = 8 if analysis.get("is_relevant_to_intent") else 2

            # Tạo object bài viết chuẩn
            processed_post = {
                "uri": vid["video_url"],  # Dùng Link Video làm ID
                "author": vid["author"],
                "content": f"[VIDEO SUMMARY] {analysis.get('transcript_summary', '')}",  # Nội dung là tóm tắt của AI
                "original_desc": vid["desc"],  # Lưu caption gốc để tham khảo
                "like_count": 0,  # Apify scraper đôi khi không trả về like, hoặc cần map field khác
                "repost_count": 0,
                "reply_count": 0,
                "created_at": "2025-01-01",  # Placeholder nếu không có date
                "curator_score": score,
                "curator_reason": analysis.get("reasoning"),
                "visual_desc": analysis.get(
                    "visual_description"
                ),  # Lưu thêm mô tả hình ảnh
            }

            print(f"      -> Điểm: {score}/10 | Lý do: {analysis.get('reasoning')}")

            # Lọc rác
            if score >= 4:
                processed_videos.append(processed_post)

            # Xóa file video tạm để tiết kiệm ổ cứng (Quan trọng!)
            try:
                os.remove(video_path)
            except:
                pass

    return processed_videos


def main():
    # --- 0. KHỞI TẠO HỆ THỐNG ---
    print("🌱 Đang khởi động hệ thống BONSAI...")

    # Common modules
    planner = BonsaiPlanner()
    ranker = BonsaiRanker()

    # Mode-specific modules (Lazy loading could be better but init here is fine)
    sourcer_bluesky = BonsaiSourcer()
    curator_text = BonsaiCurator()

    video_processor = VideoPreprocessor()
    gemini_engine = GeminiEngine()

    # --- INPUT ---
    print("\n🎛️ CHỌN CHẾ ĐỘ HOẠT ĐỘNG:")
    print("   [1] Posts (Bluesky - Text Focus)")
    print("   [2] Videos (TikTok - Multimodal Focus)")
    mode_choice = input("   > Nhập số (1 hoặc 2): ").strip()

    mode = "tiktok" if mode_choice == "2" else "bluesky"

    user_intent = input(
        "\n✍️ Nhập ý định của bạn (VD: I want to find xAI papers...): \n> "
    )
    if not user_intent:
        if mode == "bluesky":
            user_intent = "I want to find latest research papers about Explainable AI (xAI). No crypto."
        else:
            user_intent = "I want to find short tutorials explaining how Transformers work in AI. No dancing."
        print(f"(Dùng input mặc định: {user_intent})")

    # --- BƯỚC 1: PLANNING ---
    print("\n" + "=" * 40)
    print("1️⃣  PLANNING: Đang phân tích ý định...")
    plan = planner.generate_plan(user_intent)

    if not plan:
        print("❌ Lỗi: Không thể lập kế hoạch.")
        return

    print(f"   ✅ Từ khóa: {plan.get('search_queries')}")
    print(f"   ✅ Include: {plan.get('include_criteria')}")

    # --- BƯỚC 2 & 3: SOURCING & CURATING (Rẽ nhánh) ---
    print("\n" + "=" * 40)
    print(f"2️⃣ & 3️⃣ PROCESSING ({mode.upper()} MODE)...")

    final_candidates = []

    if mode == "bluesky":
        final_candidates = process_bluesky_flow(plan, sourcer_bluesky, curator_text)
    else:
        final_candidates = process_tiktok_flow(plan, video_processor, gemini_engine)

    print(f"\n   ✅ Thu được {len(final_candidates)} bài/video chất lượng.")

    # --- BƯỚC 4: RANKING ---
    print("\n" + "=" * 40)
    print("4️⃣  RANKING: Đang sắp xếp lại feed...")

    style = plan.get("ranking_preference", "balanced")
    final_feed = ranker.rank_posts(final_candidates, style=style)

    # --- OUTPUT ---
    print("\n" + "=" * 40)
    print(f"📱 YOUR PERSONALIZED FEED (Mode: {mode.upper()})")
    print("=" * 40)

    if not final_feed:
        print("📭 Feed trống!")
    else:
        for idx, post in enumerate(final_feed):
            print(f"\n[#{idx+1}] Điểm xếp hạng: {post['final_score']}")
            print(f"👤 Tác giả: {post['author']}")

            if mode == "tiktok":
                print(f"🎥 Nội dung AI Tóm tắt: {post['content']}")
                print(f"📝 Caption gốc: {post['original_desc']}")
            else:
                print(f"📄 Nội dung: {post['content']}")

            print(f"💡 xAI Insight: {post['curator_reason']}")
            print("-" * 20)


if __name__ == "__main__":
    main()

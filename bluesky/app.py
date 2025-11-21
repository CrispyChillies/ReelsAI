import streamlit as st
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
from ai_engine import GeminiEngine

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="BONSAI: xAI Social Feed", page_icon="🌱", layout="wide")

# --- CSS TÙY CHỈNH ---
st.markdown(
    """
<style>
    .xai-box {
        background-color: #1c3a2f;
        border-left: 5px solid #00cc66;
        padding: 10px;
        margin-top: 10px;
        border-radius: 5px;
        font-size: 0.9em;
    }
    .video-badge {
        background-color: #FE2C55;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.8em;
    }
    .bluesky-badge {
        background-color: #0085FF;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.8em;
    }
</style>app
""",
    unsafe_allow_html=True,
)

# --- SIDEBAR ---
st.sidebar.title("🌱 BONSAI Control")
st.sidebar.markdown("---")

# 1. Chọn Chế độ (Dual Mode)
mode = st.sidebar.radio(
    "Chọn nguồn dữ liệu:", ("Bluesky (Posts)", "TikTok (Videos)"), index=0
)

# 2. Input Ý định
default_text = ""
if mode == "Bluesky (Posts)":
    default_text = (
        "I want to find latest research papers about Explainable AI (xAI). No crypto."
    )
else:
    default_text = "I want to find short tutorials explaining how Transformers work in AI. No dancing."

user_intent = st.sidebar.text_area(
    "Nhập ý định của bạn:", value=default_text, height=100
)
ranking_style = st.sidebar.selectbox(
    "Phong cách xếp hạng:", ("balanced", "focused", "fresh", "trending")
)
generate_btn = st.sidebar.button("🚀 Tạo Feed Mới", type="primary")

# --- MAIN LOGIC ---
st.title("🌱 BONSAI: Intentional & Personalized Feed")

if "feed_data" not in st.session_state:
    st.session_state.feed_data = None

if generate_btn:
    # Init Modules
    planner = BonsaiPlanner()
    ranker = BonsaiRanker()

    with st.status("Đang xử lý hệ thống...", expanded=True) as status:
        # BƯỚC 1: PLANNING
        st.write("🧠 **Planner:** Đang phân tích ý định...")
        plan = planner.generate_plan(user_intent)
        if not plan:
            st.error("Lỗi Planner")
            st.stop()

        # Override style
        plan["ranking_preference"] = ranking_style
        st.write(f"✅ Keywords: `{plan.get('search_queries')}`")

        final_candidates = []

        # BƯỚC 2 & 3: SOURCING & CURATING (RẼ NHÁNH)
        if mode == "Bluesky (Posts)":
            st.write("🔵 **Mode:** Bluesky Processing...")
            sourcer = BonsaiSourcer()
            curator = BonsaiCurator()

            # Sourcing
            raw_posts = []
            for query in plan.get("search_queries", []):
                raw_posts.extend(sourcer.get_posts_by_query(query, limit=5))
            unique_posts = {p["uri"]: p for p in raw_posts}.values()

            # Curating
            progress_bar = st.progress(0)
            for idx, post in enumerate(unique_posts):
                rating = curator.rate_post(
                    post["content"],
                    {
                        "include_criteria": plan.get("include_criteria"),
                        "exclude_criteria": plan.get("exclude_criteria"),
                    },
                )
                post["curator_score"] = rating["score"]
                post["curator_reason"] = rating["reasoning"]
                if rating["score"] >= 4:
                    final_candidates.append(post)
                progress_bar.progress((idx + 1) / len(unique_posts))

        else:  # TikTok Mode
            st.write("🎵 **Mode:** TikTok Processing (Multimodal AI)...")
            video_processor = VideoPreprocessor()
            gemini_engine = GeminiEngine()

            # Sourcing (Apify)
            st.write("📡 Gọi Apify tìm video...")
            raw_videos = fetch_tiktok_videos(
                plan.get("search_queries", []), max_items=1
            )

            # Processing (Gemini)
            progress_bar = st.progress(0)
            for idx, vid in enumerate(raw_videos):
                st.write(f"▶️ Analyzing: {vid['desc'][:30]}...")
                video_path = video_processor.download_video(vid)
                if video_path:
                    analysis = gemini_engine.analyze_video(
                        video_path, post_text=vid["desc"]
                    )
                    if analysis:
                        score = 8 if analysis.get("is_relevant_to_intent") else 2
                        processed_post = {
                            "uri": vid["video_url"],
                            "author": vid["author"],
                            "content": f"**[AI SUMMARY]** {analysis.get('transcript_summary', '')}",
                            "original_desc": vid["desc"],
                            "created_at": "2025-01-01",  # Placeholder
                            "like_count": 0,
                            "repost_count": 0,
                            "reply_count": 0,
                            "curator_score": score,
                            "curator_reason": analysis.get("reasoning"),
                            "final_score": 0,  # Sẽ tính sau
                        }
                        if score >= 4:
                            final_candidates.append(processed_post)

                    # Cleanup
                    try:
                        os.remove(video_path)
                    except:
                        pass
                progress_bar.progress((idx + 1) / len(raw_videos))

        # BƯỚC 4: RANKING
        st.write(f"📊 **Ranker:** Sắp xếp {len(final_candidates)} kết quả...")
        final_feed = ranker.rank_posts(final_candidates, style=ranking_style)
        st.session_state.feed_data = final_feed
        st.session_state.current_mode = mode

        status.update(label="Hoàn tất!", state="complete", expanded=False)

# --- HIỂN THỊ KẾT QUẢ ---
if st.session_state.feed_data:
    current_mode = st.session_state.get("current_mode", mode)
    st.markdown(f"### Kết quả Feed ({current_mode})")

    for post in st.session_state.feed_data:
        with st.container():
            # Header
            c1, c2 = st.columns([0.85, 0.15])
            with c1:
                badge_class = (
                    "video-badge" if "TikTok" in current_mode else "bluesky-badge"
                )
                st.markdown(
                    f"<span class='{badge_class}'>@{post['author']}</span>",
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown(f"**Rank: {post['final_score']}**")

            # Content
            st.markdown(post["content"])

            # Nếu là TikTok, hiển thị thêm link video hoặc caption gốc
            if "TikTok" in current_mode:
                st.caption(f"📝 Caption gốc: {post.get('original_desc', '')}")
                st.link_button("Xem trên TikTok", post["uri"])

            # xAI Box
            st.markdown(
                f"""
            <div class='xai-box'>
                <b>💡 xAI Insight (Tại sao bạn thấy bài này?):</b><br>
                {post['curator_reason']}
            </div>
            """,
                unsafe_allow_html=True,
            )
            st.markdown("---")

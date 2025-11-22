from datetime import datetime


class BonsaiRanker:
    def __init__(self):
        # Định nghĩa trọng số cho các chế độ (Presets) [cite: 231]
        # Format: (Relevance, Recency, Popularity)
        self.presets = {
            "focused": (0.6, 0.2, 0.2),  # Ưu tiên độ khớp nội dung
            "fresh": (0.2, 0.7, 0.1),  # Ưu tiên tin mới nhất
            "trending": (0.1, 0.2, 0.7),  # Ưu tiên tin nhiều tương tác
            "balanced": (0.34, 0.33, 0.33),  # Cân bằng
        }

    def calculate_engagement(self, post):
        """Công thức: Likes + 3*Reposts + 2*Replies"""
        likes = post.get("like_count", 0)
        reposts = post.get("repost_count", 0)
        replies = post.get("reply_count", 0)
        return likes + (3 * reposts) + (2 * replies)

    def get_rank_map(self, posts, key_func, reverse=True):
        """Hàm phụ trợ: Trả về dictionary {post_id: rank_point}"""
        # Sắp xếp list
        sorted_posts = sorted(posts, key=key_func, reverse=reverse)
        # Gán điểm rank: Bài đứng nhất được N điểm, bài cuối được 1 điểm
        n = len(posts)
        rank_map = {}
        for idx, post in enumerate(sorted_posts):
            rank_map[post["uri"]] = n - idx
        return rank_map

    def rank_posts(self, posts, style="balanced"):
        """
        Thuật toán Weighted Borda Count [cite: 816, 820]
        """
        if not posts:
            return []

        # Lấy trọng số
        w_rel, w_rec, w_pop = self.presets.get(style, self.presets["balanced"])
        print(
            f"⚖️ Đang xếp hạng theo style '{style}': w_rel={w_rel}, w_rec={w_rec}, w_pop={w_pop}"
        )

        # 1. Tính Rank cho từng tiêu chí
        # Rank by Relevance (Điểm Curator chấm)
        rank_rel = self.get_rank_map(
            posts, key_func=lambda x: x.get("curator_score", 0)
        )

        # Rank by Recency (Thời gian tạo)
        rank_rec = self.get_rank_map(posts, key_func=lambda x: x.get("created_at", ""))

        # Rank by Popularity (Engagement Score)
        rank_pop = self.get_rank_map(
            posts, key_func=lambda x: self.calculate_engagement(x)
        )

        # 2. Tính điểm tổng hợp (Weighted Sum)
        ranked_posts = []
        for post in posts:
            uri = post["uri"]

            # Lấy điểm rank của bài post này ở từng tiêu chí
            r_rel = rank_rel.get(uri, 0)
            r_rec = rank_rec.get(uri, 0)
            r_pop = rank_pop.get(uri, 0)

            # Công thức Borda
            final_score = (w_rel * r_rel) + (w_rec * r_rec) + (w_pop * r_pop)

            # Lưu kết quả để hiển thị
            post["final_score"] = round(final_score, 2)
            post["debug_ranks"] = f"(Rel:{r_rel}, Rec:{r_rec}, Pop:{r_pop})"
            ranked_posts.append(post)

        # 3. Sắp xếp lại danh sách lần cuối theo Final Score
        return sorted(ranked_posts, key=lambda x: x["final_score"], reverse=True)


# --- PHẦN TEST CHẠY THỬ ---
if __name__ == "__main__":
    ranker = BonsaiRanker()

    # Giả lập dữ liệu output từ Curator (đã có điểm score)
    # Giả sử hiện tại là 2025-11-20
    mock_posts = [
        {
            "uri": "post1",
            "content": "Super Relevant but Old & Unpopular Research",
            "curator_score": 9,  # Rất liên quan
            "created_at": "2025-11-01",  # Cũ
            "like_count": 5,  # Ít like
            "repost_count": 1,
            "reply_count": 0,
        },
        {
            "uri": "post2",
            "content": "Irrelevant but Super Viral & New Crypto News",
            "curator_score": 1,  # Không liên quan
            "created_at": "2025-11-20",  # Mới tinh
            "like_count": 1000,  # Rất hot
            "repost_count": 500,
            "reply_count": 100,
        },
        {
            "uri": "post3",
            "content": "Moderately Relevant & Recent Research",
            "curator_score": 7,  # Khá liên quan
            "created_at": "2025-11-19",  # Khá mới
            "like_count": 50,  # Tương tác ổn
            "repost_count": 10,
            "reply_count": 5,
        },
    ]

    # Thử nghiệm 1: Chế độ 'FOCUSED' (Ưu tiên nội dung chuẩn)
    print("\n--- RANKING: FOCUSED ---")
    results = ranker.rank_posts(mock_posts, style="focused")
    for p in results:
        print(f"#{p['final_score']} | {p['content']} {p['debug_ranks']}")

    # Thử nghiệm 2: Chế độ 'TRENDING' (Ưu tiên tin hot)
    print("\n--- RANKING: TRENDING ---")
    results = ranker.rank_posts(mock_posts, style="trending")
    for p in results:
        print(f"#{p['final_score']} | {p['content']} {p['debug_ranks']}")

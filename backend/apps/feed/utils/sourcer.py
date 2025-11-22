import os
from dotenv import load_dotenv
from atproto import Client

# Load biến môi trường
load_dotenv()


class BonsaiSourcer:
    def __init__(self):
        self.client = Client()
        try:
            username = os.getenv("BSKY_USERNAME")
            password = os.getenv("BSKY_PASSWORD")
            if not username or not password:
                raise ValueError(
                    "Chưa cấu hình BSKY_USERNAME hoặc BSKY_PASSWORD trong file .env"
                )

            self.client.login(username, password)
            print(f"✅ Đã đăng nhập thành công vào Bluesky: {username}")
        except Exception as e:
            print(f"❌ Lỗi đăng nhập: {e}")
            self.client = None

    def get_posts_by_query(self, query, limit=10):
        if not self.client:
            return []
        print(f"🔎 Đang tìm kiếm bài viết với từ khóa: '{query}'...")
        try:
            data = self.client.app.bsky.feed.search_posts(
                params={"q": query, "limit": limit}
            )
            results = []

            for post in data.posts:
                # 1. Lấy Metrics (Nằm ở cấp ngoài cùng của Post View)
                # Lưu ý: 'post' ở đây là object PostView của thư viện atproto
                like_count = getattr(post, "like_count", 0)
                repost_count = getattr(post, "repost_count", 0)
                reply_count = getattr(post, "reply_count", 0)

                # 2. Logic Lấy Ảnh Thông Minh (Hỗ trợ cả bài thường và bài Quote)
                images = []

                # Kiểm tra 'embed' ở cấp ngoài cùng
                if hasattr(post, "embed") and post.embed:
                    embed = post.embed

                    # Trường hợp 1: Bài có ảnh trực tiếp (app.bsky.embed.images)
                    if hasattr(embed, "images") and embed.images:
                        for img in embed.images:
                            if hasattr(img, "fullsize"):
                                images.append(img.fullsize)

                    # Trường hợp 2: Bài Quote/RecordWithMedia (app.bsky.embed.recordWithMedia)
                    # Ảnh có thể nằm trong phần media đính kèm
                    elif hasattr(embed, "media") and hasattr(embed.media, "images"):
                        for img in embed.media.images:
                            if hasattr(img, "fullsize"):
                                images.append(img.fullsize)

                    # Trường hợp 3 (Hiếm): Ảnh nằm sâu trong bài được quote (ít khi cần lấy cái này làm thumbnail chính)
                rkey = post.uri.split("/")[-1]
                post_url = f"https://bsky.app/profile/{post.author.handle}/post/{rkey}"

                results.append(
                    {
                        "type": "search_result",
                        "author": post.author.handle,
                        "content": post.record.text,
                        "images": images,  # List các link ảnh tìm được
                        "created_at": post.record.created_at,
                        "like_count": like_count,
                        "repost_count": repost_count,
                        "reply_count": reply_count,
                        "uri": post.uri,
                        "cid": post.cid,
                        "post_url": post_url,  # <--- THÊM TRƯỜNG NÀY
                    }
                )
            return results
        except Exception as e:
            print(f"Lỗi khi search: {e}")
            return []

    def get_posts_by_author(self, author_handle, limit=10):
        """
        Lấy bài post từ một user cụ thể
        """
        if not self.client:
            return []

        print(f"👤 Đang lấy feed từ tác giả: {author_handle}...")
        try:
            # Gọi API get_author_feed
            data = self.client.get_author_feed(actor=author_handle, limit=limit)

            results = []
            for feed_view in data.feed:
                post = feed_view.post

                # --- LOGIC MỚI: LẤY ẢNH ---
                images = []
                if hasattr(post, "embed") and hasattr(post.embed, "images"):
                    if post.embed.images:
                        for img in post.embed.images:
                            if hasattr(img, "fullsize"):
                                images.append(img.fullsize)
                # --------------------------

                results.append(
                    {
                        "type": "author_feed",
                        "author": post.author.handle,
                        "content": post.record.text,
                        "images": images,  # <--- Thêm trường này
                        "created_at": post.record.created_at,
                        "like_count": post.like_count or 0,
                        "repost_count": post.repost_count or 0,
                        "reply_count": post.reply_count or 0,
                        "uri": post.uri,
                        "cid": post.cid,
                    }
                )
            return results
        except Exception as e:
            print(f"Lỗi khi lấy author feed: {e}")
            return []


# --- PHẦN TEST CHẠY THỬ ---
if __name__ == "__main__":
    sourcer = BonsaiSourcer()

    # Test: Tìm bài viết có khả năng có ảnh (ví dụ: Art, Cat, Dog)
    posts = sourcer.get_posts_by_query("Explainable AI, Transformers", limit=5)
    print("\n--- KẾT QUẢ SEARCH ---")
    for p in posts:
        with open("bluesky_test_output.txt", "a", encoding="utf-8") as f:
            f.write(str(p) + "\n")
        has_img = "📸 CÓ ẢNH" if p["images"] else "📄 Text only"
        print(f"[{p['author']}] ({has_img}): {p['content'][:30]}...")
        if p["images"]:
            print(f"   Link ảnh: {p['images'][0]}")

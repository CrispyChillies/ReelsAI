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
        """
        Tìm kiếm bài post theo từ khóa (tương ứng với Search trong bài báo)
        """
        if not self.client:
            return []

        print(f"🔎 Đang tìm kiếm bài viết với từ khóa: '{query}'...")
        try:
            # Gọi API search_posts của Bluesky
            data = self.client.app.bsky.feed.search_posts(
                params={"q": query, "limit": limit}
            )

            # Trích xuất dữ liệu cần thiết
            results = []
            for post in data.posts:
                results.append(
                    {
                        "type": "search_result",
                        "author": post.author.handle,
                        "content": post.record.text,
                        "created_at": post.record.created_at,
                        "like_count": post.like_count or 0,
                        "repost_count": post.repost_count or 0,
                        "reply_count": post.reply_count or 0,
                        "uri": post.uri,  # ID định danh bài viết
                        "cid": post.cid,  # Content ID
                    }
                )
            return results
        except Exception as e:
            print(f"Lỗi khi search: {e}")
            return []

    def get_posts_by_author(self, author_handle, limit=10):
        """
        Lấy bài post từ một user cụ thể (tương ứng với Accounts you follow)
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
                results.append(
                    {
                        "type": "author_feed",
                        "author": post.author.handle,
                        "content": post.record.text,
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

    # Test 1: Tìm bài viết về xAI
    posts = sourcer.get_posts_by_query("Explainable AI", limit=3)
    print("\n--- KẾT QUẢ SEARCH ---")
    for p in posts:
        print(f"[{p['author']}]: {p['content'][:50]}... (Likes: {p['like_count']})")

    # Test 2: Lấy bài từ Yann LeCun (hoặc thay bằng user khác)
    # author_posts = sourcer.get_posts_by_author("yannlecun.bsky.social", limit=3)
    # print("\n--- KẾT QUẢ AUTHOR ---")
    # for p in author_posts:
    #     print(f"[{p['author']}]: {p['content'][:50]}...")

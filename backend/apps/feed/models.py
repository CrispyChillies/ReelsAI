# feeds/models.py
from django.db import models
from django.contrib.auth.models import User


class PersonalFeed(models.Model):
    """Cấu hình Feed của người dùng (Planner Output)"""

    PLATFORM_CHOICES = [("bluesky", "Bluesky"), ("tiktok", "TikTok")]
    RANKING_CHOICES = [
        ("balanced", "Balanced"),
        ("focused", "Focused"),
        ("fresh", "Fresh"),
        ("trending", "Trending"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="feeds")
    title = models.CharField(max_length=200)
    user_intent = models.TextField(help_text="Prompt gốc của user")

    # Supabase (Postgres) hỗ trợ JSONField rất tốt
    search_queries = models.JSONField(default=list)
    include_criteria = models.TextField(blank=True, default="")
    exclude_criteria = models.TextField(blank=True, default="")

    platform = models.CharField(
        max_length=20, choices=PLATFORM_CHOICES, default="bluesky"
    )
    ranking_style = models.CharField(
        max_length=20, choices=RANKING_CHOICES, default="balanced"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class SocialPost(models.Model):
    """Kho dữ liệu bài viết thô (Cache)"""

    platform_id = models.CharField(max_length=500, unique=True, db_index=True)
    platform = models.CharField(max_length=20, choices=PersonalFeed.PLATFORM_CHOICES)
    author = models.CharField(max_length=100)
    content = models.TextField()  # Caption hoặc Post Text

    media_url = models.URLField(max_length=500, null=True, blank=True)
    thumbnail_url = models.URLField(max_length=500, null=True, blank=True)
    source_link = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        help_text="Link post for user to click to view",
    )
    embed_quote = models.TextField(
        null=True, blank=True, help_text="HTML Embed of TikTok"
    )

    # Metadata phục vụ Ranking
    like_count = models.IntegerField(default=0)
    repost_count = models.IntegerField(default=0)
    reply_count = models.IntegerField(default=0)
    created_at_source = models.DateTimeField(null=True, blank=True)
    fetched_at = models.DateTimeField(auto_now_add=True)


class FeedItem(models.Model):
    """Kết quả đã được AI Curate"""

    feed = models.ForeignKey(
        PersonalFeed, on_delete=models.CASCADE, related_name="items"
    )
    post = models.ForeignKey(SocialPost, on_delete=models.CASCADE)

    ai_score = models.FloatField()
    ai_reasoning = models.TextField()
    ai_summary = models.TextField(null=True, blank=True)  # Tóm tắt video

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("feed", "post")  # 1 bài chỉ xuất hiện 1 lần trong 1 feed
        ordering = ["-ai_score"]

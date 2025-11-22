from django.db import models
from django.contrib.auth.models import User
from apps.feed.models import SocialPost  # Import từ app feeds (Cross-app relationship)


class UserSavedItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="saved_items")

    # Liên kết sang bảng SocialPost ở app feeds
    post = models.ForeignKey(SocialPost, on_delete=models.CASCADE)

    is_favorite = models.BooleanField(default=True)
    tags = models.JSONField(default=list, blank=True)
    user_notes = models.TextField(blank=True, null=True)

    is_rag_indexed = models.BooleanField(default=False)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "post")
        ordering = ["-saved_at"]

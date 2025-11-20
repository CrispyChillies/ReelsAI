from django.db import models


# Nếu bạn dùng Supabase thì không cần model này
# Nhưng tốt nhất nên có để Django admin quản lý
class UserSavedItem(models.Model):
    user_id = models.IntegerField()
    content_id = models.IntegerField()
    saved_at = models.DateTimeField(auto_now_add=True)
    tags = models.JSONField(default=list, blank=True)
    rating = models.IntegerField(default=4)
    is_favorite = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "user_saved_items"
        unique_together = ["user_id", "content_id"]

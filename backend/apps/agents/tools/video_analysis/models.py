from django.db import models
from django.contrib.auth.models import User


class VideoAnalysis(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    video_file = models.FileField(upload_to="videos/")
    transcript = models.TextField(blank=True)
    detected_language = models.CharField(max_length=50, blank=True)
    summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Video Analysis {self.pk} by {self.user.username}"

    class Meta:
        app_label = "video_analysis"
        ordering = ["-created_at"]
        db_table = "video_analysis"

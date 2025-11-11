from django.contrib import admin
from .models import VideoAnalysis


@admin.register(VideoAnalysis)
class VideoAnalysisAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "detected_language", "created_at"]
    list_filter = ["detected_language", "created_at"]
    search_fields = ["user__username", "transcript", "summary"]
    readonly_fields = ["created_at"]

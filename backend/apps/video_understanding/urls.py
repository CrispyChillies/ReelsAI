from django.urls import path
from .views import summarize_video_view

urlpatterns = [
    path("summarize", summarize_video_view, name="video_summarize"),
]

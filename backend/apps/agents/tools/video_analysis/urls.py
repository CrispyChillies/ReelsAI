from django.urls import path
from .views import VideoCaptioningView, VideoAnalysisHistoryView

urlpatterns = [
    path("analyze/", VideoCaptioningView.as_view(), name="video-analyze"),
    path("history/", VideoAnalysisHistoryView.as_view(), name="video-history"),
]

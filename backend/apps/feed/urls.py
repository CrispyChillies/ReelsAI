from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BlueskyFeedViewSet, TikTokFeedViewSet

router = DefaultRouter()

# 1. API cho Bluesky -> /api/posts/
router.register(r"posts", BlueskyFeedViewSet, basename="bluesky-feed")

# 2. API cho TikTok -> /api/videos/
router.register(r"videos", TikTokFeedViewSet, basename="tiktok-feed")

urlpatterns = [
    path("", include(router.urls)),
]

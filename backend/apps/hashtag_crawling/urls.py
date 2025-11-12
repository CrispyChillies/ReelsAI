from django.urls import path
from apps.hashtag_crawling.views import GetTopHashtagsView

urlpatterns = [
    path('top-hashtags/', GetTopHashtagsView.as_view(), name='get_top_hashtags'),
]

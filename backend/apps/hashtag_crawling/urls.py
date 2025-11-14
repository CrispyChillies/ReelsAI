from django.urls import path
from apps.hashtag_crawling.views import GetTopHashtagsView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # API đăng nhập (lấy JWT token)
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # API lấy top hashtags
    path('top-hashtags/', GetTopHashtagsView.as_view(), name='get_top_hashtags'),
]

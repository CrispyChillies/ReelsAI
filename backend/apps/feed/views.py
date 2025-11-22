from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
    OpenApiResponse,
)

from .models import PersonalFeed, FeedItem
from .serializers import PersonalFeedSerializer, FeedItemSerializer
from .tasks import update_feed_task


class BaseFeedViewSet(viewsets.ModelViewSet):
    """
    Class cha chứa logic chung.
    """

    serializer_class = PersonalFeedSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @extend_schema(
        summary="Kích hoạt Crawl (Refresh)",
        description="API này sẽ đẩy một task vào RabbitMQ để worker chạy ngầm. Trả về Task ID ngay lập tức.",
        request=None,  # Báo cho Swagger biết không cần gửi body
        responses={
            202: OpenApiResponse(description="Task đã được queued thành công"),
            404: OpenApiResponse(description="Feed không tồn tại"),
        },
    )
    @action(detail=True, methods=["post"])
    def refresh(self, request, pk=None):
        feed = self.get_object()
        task = update_feed_task.delay(feed.id)
        return Response(
            {
                "status": "queued",
                "task_id": task.id,
                "message": f"Đang crawl dữ liệu cho {feed.title}...",
            },
            status=status.HTTP_202_ACCEPTED,
        )

    @extend_schema(
        summary="Lấy danh sách bài viết (Items)",
        description="Lấy các bài viết đã được AI chấm điểm và lọc xong từ Database.",
        responses={200: FeedItemSerializer(many=True)},
    )
    @action(detail=True, methods=["get"])
    def items(self, request, pk=None):
        feed = self.get_object()
        items = (
            FeedItem.objects.filter(feed=feed)
            .select_related("post")
            .order_by("-ai_score")
        )
        serializer = FeedItemSerializer(items, many=True)
        return Response(serializer.data)


# --- API RIÊNG CHO BLUESKY (POSTS) ---
@extend_schema(tags=["Bluesky Posts"])  # Gom nhóm trong Swagger
class BlueskyFeedViewSet(BaseFeedViewSet):
    queryset = PersonalFeed.objects.filter(platform="bluesky")

    @extend_schema(
        summary="Tạo Feed theo dõi Bluesky",
        description="Tạo cấu hình để AI tự động tìm bài viết (Text) trên Bluesky.",
        examples=[
            OpenApiExample(
                "Ví dụ xAI",
                summary="Tìm kiếm bài nghiên cứu xAI",
                description="Cấu hình để tìm các bài research paper về Explainable AI.",
                value={
                    "title": "xAI Research Papers",
                    "user_intent": "I want to read latest research papers about Explainable AI (xAI) and Interpretability. No crypto content.",
                    "ranking_style": "balanced",
                },
                request_only=True,  # Chỉ hiện ở chiều request
            )
        ],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, platform="bluesky")


# --- API RIÊNG CHO TIKTOK (VIDEOS) ---
@extend_schema(tags=["TikTok Videos"])  # Gom nhóm trong Swagger
class TikTokFeedViewSet(BaseFeedViewSet):
    queryset = PersonalFeed.objects.filter(platform="tiktok")

    @extend_schema(
        summary="Tạo Feed theo dõi TikTok",
        description="Tạo cấu hình để AI tự động tìm và phân tích nội dung Video trên TikTok.",
        examples=[
            OpenApiExample(
                "Ví dụ AI Tutorial",
                summary="Tìm video dạy học AI",
                description="Cấu hình để tìm các video ngắn giải thích kiến thức AI.",
                value={
                    "title": "AI Transformers Tutorials",
                    "user_intent": "I want short tutorials explaining how Transformer models work. No dancing or lip-syncing.",
                    "ranking_style": "trending",
                },
                request_only=True,
            )
        ],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, platform="tiktok")

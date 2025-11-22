from rest_framework import serializers
from .models import PersonalFeed, SocialPost, FeedItem


class SocialPostSerializer(serializers.ModelSerializer):
    """
    Chuyển đổi thông tin bài viết gốc (Bluesky/TikTok).
    Serializer này sẽ được lồng (nest) vào trong FeedItemSerializer.
    """

    class Meta:
        model = SocialPost
        fields = [
            "id",
            "platform_id",
            "platform",
            "author",
            "content",
            "media_url",
            "thumbnail_url",
            "source_link",
            "embed_quote",
            "like_count",
            "repost_count",
            "fetched_at",
        ]
        read_only_fields = (
            fields  # Dữ liệu này do Crawler tạo ra, user không sửa trực tiếp
        )


class FeedItemSerializer(serializers.ModelSerializer):
    """
    Serializer quan trọng nhất để hiển thị Newsfeed.
    Nó chứa thông tin chấm điểm của AI và lồng ghép nội dung bài viết gốc.
    """

    # Nested Serializer: Hiển thị chi tiết bài post thay vì chỉ hiện ID
    post = SocialPostSerializer(read_only=True)

    class Meta:
        model = FeedItem
        fields = [
            "id",
            "post",  # Object bài viết đầy đủ
            "ai_score",
            "ai_reasoning",
            "ai_summary",
            "created_at",
        ]


class PersonalFeedSerializer(serializers.ModelSerializer):
    """
    Dùng để Tạo mới (Create) và Xem cấu hình (Retrieve) Feed.
    """

    # Tính toán số lượng bài viết hiện có trong feed (Optional but helpful)
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = PersonalFeed
        fields = [
            "id",
            "title",
            "user_intent",
            "search_queries",  # JSON Field (Supabase hỗ trợ tốt)
            "include_criteria",
            "exclude_criteria",
            "platform",
            "ranking_style",
            "items_count",
            "created_at",
        ]

        # Các trường này do hệ thống (Planner) tự tạo, user không cần nhập khi POST
        read_only_fields = [
            "search_queries",
            "include_criteria",
            "exclude_criteria",
            "created_at",
            "user",
        ]

    def get_items_count(self, obj):
        """Trả về số lượng bài viết đã curate trong feed này"""
        return obj.items.count()

    def create(self, validated_data):
        """
        Logic tùy chỉnh khi tạo feed (nếu cần).
        Hiện tại logic gán User đã nằm trong Views (perform_create),
        nên ở đây giữ mặc định là ổn.
        """
        return super().create(validated_data)

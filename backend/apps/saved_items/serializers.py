from rest_framework import serializers
from .models import UserSavedItem
from apps.feed.models import SocialPost


class SaveItemRequestSerializer(serializers.Serializer):
    social_post_id = serializers.IntegerField()
    tags = serializers.ListField(
        child=serializers.CharField(), required=False, default=[]
    )
    notes = serializers.CharField(required=False, allow_blank=True)


class SaveItemResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    message = serializers.CharField()
    saved_id = serializers.IntegerField()


class SocialPostSerializer(serializers.ModelSerializer):
    """
    Serializer chi tiết cho bài viết gốc từ bảng feed_socialpost
    """

    class Meta:
        model = SocialPost
        fields = [
            "id",
            "platform",
            "author",
            "content",
            "media_url",
            "thumbnail_url",
            "like_count",
            "repost_count",
            "reply_count",
            "source_link",
            "created_at_source",
            "fetched_at",
        ]


class SavedItemSerializer(serializers.ModelSerializer):
    """
    Serializer để hiển thị các mục đã lưu của người dùng kèm thông tin bài viết.
    """

    # Nested serializer để hiển thị chi tiết bài viết thay vì chỉ ID
    post = SocialPostSerializer(read_only=True)

    class Meta:
        model = UserSavedItem
        fields = [
            "id",
            "post",
            "is_favorite",
            "tags",
            "user_notes",
            "is_rag_indexed",
            "saved_at",
        ]

from rest_framework import serializers


class VideoSummarizeRequestSerializer(serializers.Serializer):
    """Request serializer for video summarization"""

    video_url = serializers.URLField(
        required=False, allow_null=True, help_text="URL to video file"
    )
    video_file = serializers.FileField(
        required=False, allow_null=True, help_text="Upload video file directly"
    )

    def validate(self, attrs):
        """Ensure at least one of video_url or video_file is provided"""
        if not attrs.get("video_url") and not attrs.get("video_file"):
            raise serializers.ValidationError(
                "Either 'video_url' or 'video_file' must be provided."
            )
        if attrs.get("video_url") and attrs.get("video_file"):
            raise serializers.ValidationError(
                "Provide either 'video_url' or 'video_file', not both."
            )
        return attrs


class VideoSummarizeResponseSerializer(serializers.Serializer):
    """Response serializer for video summarization"""

    summary = serializers.CharField()
    status = serializers.CharField(default="success")
    error = serializers.CharField(required=False, allow_null=True)

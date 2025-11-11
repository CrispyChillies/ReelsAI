from rest_framework import serializers
from .models import VideoAnalysis


class VideoUploadSerializer(serializers.Serializer):
    video_file = serializers.FileField()


class VideoAnalysisSerializer(serializers.ModelSerializer):
    video_url = serializers.SerializerMethodField()

    class Meta:
        model = VideoAnalysis
        fields = [
            "id",
            "video_url",
            "transcript",
            "detected_language",
            "summary",
            "created_at",
        ]

    def get_video_url(self, obj):
        request = self.context.get("request")
        if obj.video_file and request:
            return request.build_absolute_uri(obj.video_file.url)
        return None


class VideoAnalysisResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    transcript = serializers.CharField()
    detected_language = serializers.CharField()
    summary = serializers.CharField()
    video_url = serializers.URLField()
    created_at = serializers.DateTimeField()


class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField()

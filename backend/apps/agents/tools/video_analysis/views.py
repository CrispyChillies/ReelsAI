from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiExample
import logging

from .models import VideoAnalysis
from .serializers import (
    VideoUploadSerializer,
    VideoAnalysisResponseSerializer,
    ErrorResponseSerializer,
    VideoAnalysisSerializer,
)
from .services import VideoCaptioningService

logger = logging.getLogger(__name__)


class VideoCaptioningView(APIView):
    """
    Upload and analyze video content to generate transcript and summary.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Video Analysis"],
        summary="Analyze video content",
        description="Upload a video file to get transcript and summary using OpenAI Whisper and GPT.",
        request=VideoUploadSerializer,
        responses={
            200: VideoAnalysisResponseSerializer,
            400: ErrorResponseSerializer,
        },
    )
    def post(self, request):
        serializer = VideoUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        video_file = serializer.validated_data["video_file"]

        try:
            # Create video analysis record
            video_analysis = VideoAnalysis.objects.create(
                user=request.user, video_file=video_file
            )

            # Process video
            captioning_service = VideoCaptioningService()
            result = captioning_service.transcribe_and_summarize(video_file)

            # Update the record with results
            video_analysis.transcript = result["transcript"]
            video_analysis.detected_language = result["detected_language"]
            video_analysis.summary = result["summary"]
            video_analysis.save()

            # Return response
            response_data = {
                "id": video_analysis.pk,
                "transcript": video_analysis.transcript,
                "detected_language": video_analysis.detected_language,
                "summary": video_analysis.summary,
                "video_url": request.build_absolute_uri(video_analysis.video_file.url),
                "created_at": video_analysis.created_at,
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Video analysis error: {str(e)}")
            if "video_analysis" in locals():
                video_analysis.delete()
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class VideoAnalysisHistoryView(APIView):
    """
    Get user's video analysis history.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Video Analysis"],
        summary="Get video analysis history",
        description="Retrieve all video analyses for the authenticated user.",
        responses={200: VideoAnalysisSerializer(many=True)},
    )
    def get(self, request):
        analyses = VideoAnalysis.objects.filter(user=request.user)
        serializer = VideoAnalysisSerializer(
            analyses, many=True, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

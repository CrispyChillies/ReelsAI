import os
import tempfile
import requests
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiExample

from .serializers import (
    VideoSummarizeRequestSerializer,
    VideoSummarizeResponseSerializer,
)
from .video_understanding import summarize_video


SUMMARIZE_REQUEST_EXAMPLE = OpenApiExample(
    "VideoSummarizeExample",
    value={
        "video_url": "https://example.com/video.mp4",
    },
    request_only=True,
)


@extend_schema(
    request=VideoSummarizeRequestSerializer,
    responses={
        200: VideoSummarizeResponseSerializer,
        400: VideoSummarizeResponseSerializer,
        503: VideoSummarizeResponseSerializer,
        500: VideoSummarizeResponseSerializer,
    },
    examples=[SUMMARIZE_REQUEST_EXAMPLE],
    description="Summarize video content using Gemini AI. Provide either a video URL or upload a video file (max 20MB).",
)
@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def summarize_video_view(request):
    """
    API endpoint to summarize video content.

    Accepts either:
    - video_url: URL to download the video from
    - video_file: Direct file upload (multipart/form-data)

    Returns a Vietnamese summary of the video content.
    """
    serializer = VideoSummarizeRequestSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            {"status": "error", "error": serializer.errors, "summary": None},
            status=status.HTTP_400_BAD_REQUEST,
        )

    validated_data = serializer.validated_data
    temp_video_path = None

    try:
        # Handle video_file upload
        if validated_data.get("video_file"):
            video_file = validated_data["video_file"]

            # Check file size (20MB limit)
            if video_file.size > 20 * 1024 * 1024:
                return Response(
                    {
                        "status": "error",
                        "error": "Video file must be less than 20MB",
                        "summary": None,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                for chunk in video_file.chunks():
                    tmp.write(chunk)
                temp_video_path = tmp.name

        # Handle video_url download
        elif validated_data.get("video_url"):
            video_url = validated_data["video_url"]

            try:
                response = requests.get(video_url, stream=True, timeout=30)
                response.raise_for_status()

                # Check content length
                content_length = int(response.headers.get("content-length", 0))
                if content_length > 20 * 1024 * 1024:
                    return Response(
                        {
                            "status": "error",
                            "error": "Video at URL must be less than 20MB",
                            "summary": None,
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Download to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                    for chunk in response.iter_content(chunk_size=8192):
                        tmp.write(chunk)
                    temp_video_path = tmp.name

            except requests.RequestException as e:
                return Response(
                    {
                        "status": "error",
                        "error": f"Failed to download video: {str(e)}",
                        "summary": None,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Call summarization function with retry logic (3 attempts by default)
        summary_result = summarize_video(temp_video_path, max_retries=3)

        # Check if result is an error message
        if summary_result.startswith("Error") or summary_result.startswith(
            "No valid response"
        ):
            # Check if it's an overload error - return 503 instead of 500
            if "overloaded" in summary_result.lower() or "503" in summary_result:
                return Response(
                    {"status": "error", "error": summary_result, "summary": None},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            return Response(
                {"status": "error", "error": summary_result, "summary": None},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"status": "success", "summary": summary_result, "error": None},
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        return Response(
            {
                "status": "error",
                "error": f"Unexpected error: {str(e)}",
                "summary": None,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    finally:
        # Clean up temp file
        if temp_video_path and os.path.exists(temp_video_path):
            try:
                os.unlink(temp_video_path)
            except Exception:
                pass

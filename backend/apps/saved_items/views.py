from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiExample
from datetime import datetime, timezone
from django.conf import settings
from supabase import create_client, Client
import logging

from .serializers import SaveItemRequestSerializer, SaveItemResponseSerializer
from .queue_producer import publish_video_job

logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

SAVE_ITEM_EXAMPLE = OpenApiExample(
    "SaveItemExample",
    value={
        "user_id": 1,
        "content_id": 6952571625178975493,
    },
    request_only=True,
)


@extend_schema(
    request=SaveItemRequestSerializer,
    responses={
        201: SaveItemResponseSerializer,
        400: SaveItemResponseSerializer,
        500: SaveItemResponseSerializer,
    },
    examples=[SAVE_ITEM_EXAMPLE],
    description="Save a video item for a user and queue it for processing (summary + RAG + KG)",
)
@api_view(["POST"])
def save_item_view(request):
    """
    API endpoint to save a video item for a user.

    Flow:
    1. Validate input
    2. Save to user_saved_items table in Supabase
    3. Publish job to RabbitMQ queue for async processing

    Returns:
        201: Item saved and job queued successfully
        400: Invalid request data
        500: Database or queue error
    """
    serializer = SaveItemRequestSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            {
                "status": "error",
                "message": "Invalid request data",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    user_id = serializer.validated_data["user_id"]
    content_id = serializer.validated_data["content_id"]

    try:
        # Step 1: Save to Supabase
        logger.info(f"➡️ Saving item: user={user_id}, content={content_id}")

        saved_at_string = datetime.now(timezone.utc).isoformat()
        data_to_insert = {
            "user_id": user_id,
            "content_id": content_id,
            "saved_at": saved_at_string,
            "tags": [],
            "rating": 4,
            "is_favorite": True,
            "notes": "",
        }

        result = supabase.table("user_saved_items").insert(data_to_insert).execute()

        if not result.data:
            logger.error(f"❌ Supabase insert failed: {result}")
            return Response(
                {"status": "error", "message": "Failed to save item to database"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        logger.info(f"✅ Item saved to database")

        # Step 2: Publish to RabbitMQ queue
        queue_success = publish_video_job(user_id, content_id)

        if not queue_success:
            logger.warning("⚠️ Failed to queue job, but item was saved")
            return Response(
                {
                    "status": "partial_success",
                    "message": "Item saved but failed to queue processing job",
                    "data": result.data[0],
                },
                status=status.HTTP_201_CREATED,
            )

        logger.info(f"✅ Job queued successfully")

        return Response(
            {
                "status": "queued",
                "message": "Item saved. Video processing is queued.",
                "data": result.data[0],
            },
            status=status.HTTP_201_CREATED,
        )

    except Exception as e:
        logger.exception(f"❌ Unexpected error: {e}")
        return Response(
            {"status": "error", "message": f"Internal server error: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

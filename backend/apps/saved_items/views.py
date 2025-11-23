from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from apps.feed.models import SocialPost  # Import từ feeds
from .models import UserSavedItem
from .serializers import SaveItemRequestSerializer, SaveItemResponseSerializer
from .tasks import push_to_rag_task
from .serializers import SavedItemSerializer

import logging

logger = logging.getLogger(__name__)


@extend_schema(
    summary="Lưu bài viết (Save Item)",
    request=SaveItemRequestSerializer,
    responses={201: SaveItemResponseSerializer},
    tags=["Saved Items"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def save_item_view(request):
    serializer = SaveItemRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    social_post_id = serializer.validated_data["social_post_id"]

    try:
        # Kiểm tra post tồn tại bên app feeds
        post = SocialPost.objects.get(id=social_post_id)

        saved_item, created = UserSavedItem.objects.update_or_create(
            user=request.user,
            post=post,
            defaults={
                "tags": serializer.validated_data.get("tags", []),
                "user_notes": serializer.validated_data.get("notes", ""),
            },
        )

        # Trigger task bên app saved_items
        push_to_rag_task.delay(saved_item.id)

        return Response(
            {
                "status": "success",
                "message": "Đã lưu thành công.",
                "saved_id": saved_item.id,
            },
            status=status.HTTP_201_CREATED,
        )

    except SocialPost.DoesNotExist:
        return Response({"status": "error", "message": "Post not found"}, status=404)


@extend_schema(
    tags=["Saved Items"],
    summary="List all saved content",
    description="Retrieve a list of all content saved by the authenticated user, including full post details.",
    responses={200: SavedItemSerializer(many=True), 401: "Unauthorized"},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_saved_items(request):
    """
    Lấy danh sách các bài viết đã lưu của user hiện tại.
    """
    try:
        # Sử dụng select_related('post') để join bảng feed_socialpost ngay trong 1 query
        items = (
            UserSavedItem.objects.filter(user=request.user)
            .select_related("post")
            .order_by("-saved_at")
        )

        serializer = SavedItemSerializer(items, many=True)

        return Response(
            {"success": True, "count": items.count(), "results": serializer.data},
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        logger.error(f"Error fetching saved items for user {request.user.id}: {e}")
        return Response(
            {"error": "Internal server error", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@extend_schema(
    tags=["Saved Items"],
    summary="Delete saved item",
    description="Remove a saved item from the user's collection.",
    responses={200: {"description": "Item deleted successfully"}, 404: "Item not found"},
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_saved_item(request, item_id):
    """
    Xóa một item đã lưu của user.
    """
    try:
        item = UserSavedItem.objects.get(id=item_id, user=request.user)
        item.delete()
        
        return Response(
            {"success": True, "message": "Item deleted successfully"},
            status=status.HTTP_200_OK,
        )
    except UserSavedItem.DoesNotExist:
        return Response(
            {"error": "Item not found or you don't have permission to delete it"},
            status=status.HTTP_404_NOT_FOUND,
        )

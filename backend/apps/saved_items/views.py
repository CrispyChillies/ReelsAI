from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from apps.feed.models import SocialPost  # Import từ feeds
from .models import UserSavedItem
from .serializers import SaveItemRequestSerializer, SaveItemResponseSerializer
from .tasks import push_to_rag_task


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

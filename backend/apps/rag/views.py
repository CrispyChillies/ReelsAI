from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .serializers import ItemDataSerializer, QueryRequestSerializer
from apps.agents.rag import utils

from drf_spectacular.utils import extend_schema, OpenApiExample
from drf_spectacular.types import OpenApiTypes

# Example payloads (optional, shown in UI)
ADD_ITEM_EXAMPLE = OpenApiExample(
    "AddItemExample",
    value={
        "content_id": "6952571625178975493",
        "user_id": "strongtherapy",
        "platform": "tiktok",
        "summary": "Part 2: quality mental healthcare is a privilege. #tiktoktherapy",
    },
    request_only=True,
)

QUERY_ITEMS_EXAMPLE = OpenApiExample(
    "QueryItemsExample",
    value={
        "user_id": "strongtherapy",
        "query": "mental healthcare privilege",
        "top_k": 3,
        "from_timestamp": 1600000000,
        "platform": "tiktok",
    },
    request_only=True,
)


@extend_schema(
    request=ItemDataSerializer,
    responses={200: OpenApiTypes.OBJECT},
    examples=[ADD_ITEM_EXAMPLE],
)
@api_view(["PUT"])
def add_item_view(request):

    s = ItemDataSerializer(data=request.data)
    if not s.is_valid():
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        res = utils.insert_item(**s.validated_data)
        return Response(res, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    request=QueryRequestSerializer,
    responses={200: OpenApiTypes.OBJECT},
    examples=[QUERY_ITEMS_EXAMPLE],
)
@api_view(["POST"])
def query_items_view(request):
    s = QueryRequestSerializer(data=request.data)
    if not s.is_valid():
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        res = utils.query_items(**s.validated_data)
        return Response(res, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

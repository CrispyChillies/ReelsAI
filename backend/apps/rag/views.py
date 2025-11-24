from rest_framework.decorators import api_view, permission_classes

# from rest_framework.permissions import IsAuthenticated
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
        "content_url": "https://www.tiktok.com/@strongtherapy/video/6952571625178975493",
        "user_id": "strongtherapy",
        "platform": "tiktok",
        "summary": "Part 2: quality mental healthcare is a privilege. #tiktoktherapy",
        "timestamp": 1700000000,
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
    responses={
        200: {
            "type": "object",
            "properties": {
                "status": {"type": "string", "example": "success"},
                "content_id": {"type": "string", "example": "6952571625178975493"},
            },
        },
        400: {
            "type": "object",
            "properties": {
                "error": {"type": "string"},
                "details": {"type": "object"},
            },
        },
        500: {
            "type": "object",
            "properties": {"error": {"type": "string"}},
        },
    },
    examples=[ADD_ITEM_EXAMPLE],
    description="Add an item to RAG system. Timestamp is optional - if not provided, current timestamp will be used.",
)
@api_view(["PUT"])
# @permission_classes([IsAuthenticated])
def add_item_view(request):
    """
    Add a single item to the RAG system.

    The summary will be embedded using all-MiniLM-L6-v2 and stored in Milvus.
    Timestamp is optional - defaults to None if not provided.
    """
    s = ItemDataSerializer(data=request.data)
    if not s.is_valid():
        return Response(
            {"error": "Invalid data", "details": s.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        # insert_item will handle optional timestamp
        res = utils.insert_item(**s.validated_data)
        return Response(res, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    request=QueryRequestSerializer,
    responses={
        200: {
            "type": "object",
            "properties": {
                "query": {"type": "string", "example": "mental healthcare"},
                "filter": {
                    "type": "string",
                    "example": "user_id == 'strongtherapy' && timestamp >= 1600000000 && platform == 'tiktok'",
                },
                "results": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "content_id": {"type": "string"},
                            "content_url": {"type": "string"},
                            "summary": {"type": "string"},
                            "platform": {"type": "string"},
                            "timestamp": {"type": "integer", "nullable": True},
                            "score": {"type": "number", "format": "float"},
                        },
                    },
                },
            },
        },
        400: {
            "type": "object",
            "properties": {
                "error": {"type": "string"},
                "details": {"type": "object"},
            },
        },
        500: {
            "type": "object",
            "properties": {"error": {"type": "string"}},
        },
    },
    examples=[QUERY_ITEMS_EXAMPLE],
    description="Query items using semantic search with optional filters (timestamp, platform).",
)
@api_view(["POST"])
# @permission_classes([IsAuthenticated])
def query_items_view(request):
    """
    Query items from RAG system using semantic search.

    Filters:
    - user_id (required): Only return items for this user
    - query (required): Semantic search query
    - top_k (optional): Number of results (default: 5)
    - from_timestamp (optional): Filter results after this timestamp
    - platform (optional): Filter by platform

    Note: timestamp field in results may be None if not set when item was added.
    """
    s = QueryRequestSerializer(data=request.data)
    if not s.is_valid():
        return Response(
            {"error": "Invalid data", "details": s.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        res = utils.query_items(**s.validated_data)
        return Response(res, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

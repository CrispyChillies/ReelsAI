from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .serializers import ItemDataSerializer, QueryRequestSerializer
from . import services

# drf-yasg helpers to show request body in Swagger / Redoc
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Example payloads shown in the docs
ADD_ITEM_EXAMPLE = {
    "content_id": "6952571625178975493",
    "user_id": "strongtherapy",
    "platform": "tiktok",
    "summary": "Part 2: quality mental healthcare is a privilege. #tiktoktherapy",
    "timestamp": 1700000000
}

QUERY_ITEMS_EXAMPLE = {
    "user_id": "strongtherapy",
    "query": "mental healthcare privilege",
    "top_k": 3,
    "from_timestamp": 1600000000,
    "platform": "tiktok"
}

@api_view(["PUT"])
@swagger_auto_schema(
    method="put",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "content_id": openapi.Schema(type=openapi.TYPE_STRING),
            "user_id": openapi.Schema(type=openapi.TYPE_STRING),
            "platform": openapi.Schema(type=openapi.TYPE_STRING),
            "summary": openapi.Schema(type=openapi.TYPE_STRING),
            "timestamp": openapi.Schema(type=openapi.TYPE_INTEGER),
        },
        example=ADD_ITEM_EXAMPLE,
    ),
    responses={200: openapi.Response("OK")},
)
 def add_item_view(request):
     s = ItemDataSerializer(data=request.data)
     if not s.is_valid():
         return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)
     try:
         res = services.insert_item(**s.validated_data)
         return Response(res, status=status.HTTP_200_OK)
     except Exception as e:
         return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
 
 
 @api_view(["POST"])
@swagger_auto_schema(
    method="post",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "user_id": openapi.Schema(type=openapi.TYPE_STRING),
            "query": openapi.Schema(type=openapi.TYPE_STRING),
            "top_k": openapi.Schema(type=openapi.TYPE_INTEGER),
            "from_timestamp": openapi.Schema(type=openapi.TYPE_INTEGER),
            "platform": openapi.Schema(type=openapi.TYPE_STRING),
        },
        example=QUERY_ITEMS_EXAMPLE,
    ),
    responses={200: openapi.Response("OK")},
)
 def query_items_view(request):
     s = QueryRequestSerializer(data=request.data)
     if not s.is_valid():
         return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)
     try:
         res = services.query_items(**s.validated_data)
         return Response(res, status=status.HTTP_200_OK)
     except Exception as e:
         return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
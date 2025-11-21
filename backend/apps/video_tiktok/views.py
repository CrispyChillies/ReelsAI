from rest_framework.views import APIView
from drf_spectacular.utils import (
    extend_schema, OpenApiExample, OpenApiParameter, OpenApiResponse
)
from django.http import JsonResponse
from supabase import create_client, Client
from dotenv import load_dotenv
import os
from rest_framework.permissions import IsAuthenticated
import json
import requests
import random

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class GetVideosByIndustryView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Video TikTok"],
        summary="Get videos by industry ID",
        description="Picks a random batch of 3 hashtags. Returns top 5 videos with highest views.",
        parameters=[
            OpenApiParameter(name="industry_id", required=True, location=OpenApiParameter.QUERY, type=int),
        ],
        responses={
            200: OpenApiResponse(description="List of top 5 TikTok videos by views"),
            404: OpenApiResponse(description="No videos found"),
        },
    )
    def get(self, request):
        try:
            industry_id = request.GET.get('industry_id', '').strip()
            if not industry_id.isdigit():
                return JsonResponse({"error": "industry_id is required and must be an integer"}, status=400)

            # Lấy và lọc Hashtag ---
            api_url = f"http://127.0.0.1:8000/api/top-hashtags/?industry_id={industry_id}"
            user_token = request.auth 
            headers = {"Authorization": f"Bearer {user_token}"}
            
            try:
                response = requests.get(api_url, headers=headers)
                response.raise_for_status()
                data = response.json()

                if not isinstance(data, list):
                     return JsonResponse({"error": "Invalid data format from Hashtag API"}, status=500)

                valid_data = [
                    item for item in data 
                    if item.get("hashtag") and str(item["hashtag"]).strip()
                ]
                
                if not valid_data:
                    return JsonResponse({"error": "No valid hashtags received from API"}, status=404)

                # Xáo trộn để đảm bảo tính ngẫu nhiên
                random.shuffle(valid_data)

            except requests.exceptions.RequestException as e:
                return JsonResponse({"error": f"Failed to fetch hashtags: {str(e)}"}, status=500)

            # Tìm kiếm theo Batch
            found_videos_map = {}
            BATCH_SIZE = 3
            MAX_VIDEOS = 5

            for i in range(0, len(valid_data), BATCH_SIZE):
                current_batch = valid_data[i : i + BATCH_SIZE]
                current_batch_videos = {}

                for item in current_batch:
                    ht = item["hashtag"]
                    resp = supabase.table("content_crawling") \
                        .select("*") \
                        .ilike("hashtags", f"%{ht}%") \
                        .order('playCount', desc=True) \
                        .range(0, MAX_VIDEOS - len(found_videos_map)) \
                        .execute()

                    data_rows = getattr(resp, 'data', None)

                    if data_rows:
                        for v in data_rows:
                            if v:
                                key = v.get('id') or v.get('video_url') or json.dumps(v, sort_keys=True, default=str)
                                if key not in found_videos_map:
                                    found_videos_map[key] = v

                if len(found_videos_map) >= MAX_VIDEOS:
                    break

            user_id = getattr(request.user, 'id', None)
            result = []
            for v in found_videos_map.values():
                if isinstance(v, dict) and user_id is not None:
                    v['user_id'] = user_id
                result.append(v)

            if not result:
                return JsonResponse({
                    "error": "No videos found even after rotating through all random hashtag batches.",
                }, status=404)

            result.sort(key=lambda x: int(x.get('play_count') or 0), reverse=True)

            # Lấy 5 video có lượt xem cao nhất
            result = result[:MAX_VIDEOS]

            return JsonResponse(result, safe=False)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
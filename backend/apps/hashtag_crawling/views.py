from rest_framework.views import APIView
from drf_spectacular.utils import (
    extend_schema, OpenApiExample, OpenApiParameter, OpenApiResponse
)
from django.http import JsonResponse
from supabase import create_client, Client
from dotenv import load_dotenv
import os
from rest_framework.permissions import IsAuthenticated

# Load biến môi trường từ file .env
load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class GetTopHashtagsView(APIView):
    permission_classes = [IsAuthenticated]  

    @extend_schema(
        tags=["Hashtags"],
        summary="Get top hashtags",
        description="Retrieve top 20 hashtags: 10 from VN, 5 from US, and 5 from UK based on views.",
        parameters=[
            OpenApiParameter(name="industry_id", required=True, location=OpenApiParameter.QUERY, type=int),
        ],
        responses={
            200: OpenApiResponse(description="List of top hashtags")
        },
    )
    def get(self, request):
        try:
            industry_id = request.GET.get('industry_id')
            if not industry_id:
                return JsonResponse({"error": "industry_id is required"}, status=400)

            # Fetch hashtags from Supabase
            response = supabase.table("HASHTAGS").select("*").eq("industry_id", industry_id).range(0, 999).execute()
            hashtags = response.data

            # Filter hashtags by country
            vietnam_hashtags = [h for h in hashtags if h['country_id'] == 'VN']
            us_hashtags = [h for h in hashtags if h['country_id'] == 'US']
            uk_hashtags = [h for h in hashtags if h['country_id'] == 'GB']

            # Sort by views (descending) and limit results
            vietnam_hashtags = sorted(vietnam_hashtags, key=lambda x: x['views'], reverse=True)[:10]
            us_hashtags = sorted(us_hashtags, key=lambda x: x['views'], reverse=True)[:10]
            uk_hashtags = sorted(uk_hashtags, key=lambda x: x['views'], reverse=True)[:10]

            # Combine results
            top_hashtags = vietnam_hashtags + us_hashtags + uk_hashtags

            # ⭐ Add user_id to each hashtag
            user_id = request.user.id
            for h in top_hashtags:
                h["user_id"] = user_id

            return JsonResponse(top_hashtags, safe=False)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)



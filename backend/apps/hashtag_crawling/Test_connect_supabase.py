from supabase import create_client
import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent.parent / "reelsai" / ".env"
load_dotenv(env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL or SUPABASE_KEY not found in .env file")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Lấy tất cả hashtag của Việt Nam với đúng industry_id
response = (
    supabase
        .table("HASHTAGS")
        .select("*")
        .eq("industry_id", 15000000000)
        .eq("country_id", "VN")   # ⭐ Thêm dòng này
        .range(0, 999)
        .execute()
)

print(response.data)
print(len(response.data))

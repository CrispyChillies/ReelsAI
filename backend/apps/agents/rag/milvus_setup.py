from pymilvus import (
    connections,
    Collection,
    FieldSchema,
    CollectionSchema,
    DataType,
    utility,
)
import os
from dotenv import load_dotenv

load_dotenv()
# from django.conf import settings


# # ========= CONFIG =========
ZILLIZ_URI = os.getenv("ZILLIZ_URI")
ZILLIZ_TOKEN = os.getenv("ZILLIZ_TOKEN")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

# settings.configure()

# ========= CONNECT =========
connections.connect(alias="default", uri=ZILLIZ_URI, token=ZILLIZ_TOKEN)
print("✅ Connected to Zilliz Cloud")

# ========= DEFINE SCHEMA =========
if COLLECTION_NAME not in utility.list_collections():
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="content_id", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="content_url", dtype=DataType.VARCHAR, max_length=256),
        FieldSchema(name="user_id", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="platform", dtype=DataType.VARCHAR, max_length=20),
        FieldSchema(name="summary", dtype=DataType.VARCHAR, max_length=4000),
        FieldSchema(name="timestamp", dtype=DataType.INT64),  # Unix timestamp
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
    ]

    schema = CollectionSchema(
        fields, description="Unified embeddings for TikTok + Facebook content"
    )
    collection = Collection(COLLECTION_NAME, schema)
    print("🆕 Created collection:", COLLECTION_NAME)

    # Sử dụng chỉ mục IVF_FLAT, phù hợp cho kích thước 384 chiều
    index_params = {
        "index_type": "IVF_FLAT",
        "metric_type": "COSINE",
        "params": {"nlist": 128},
    }
    collection.create_index(field_name="embedding", index_params=index_params)
    print("✅ Created Index for 'embedding'")
else:
    collection = Collection(COLLECTION_NAME)
    print("📁 Using existing collection:", COLLECTION_NAME)

collection.load()
print(f"🚀 Loaded collection: {COLLECTION_NAME}")

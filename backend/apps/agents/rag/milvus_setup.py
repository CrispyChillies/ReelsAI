from pymilvus import (
    connections,
    Collection,
    FieldSchema,
    CollectionSchema,
    DataType,
    utility,
)
from django.conf import settings

# ========= CONFIG =========
ZILLIZ_URI = settings.ZILLIZ_URI
ZILLIZ_TOKEN = settings.ZILLIZ_TOKEN
COLLECTION_NAME = settings.COLLECTION_NAME

# ========= CONNECT =========
connections.connect(alias="default", uri=ZILLIZ_URI, token=ZILLIZ_TOKEN)
print("✅ Connected to Zilliz Cloud")

# ========= DEFINE SCHEMA =========
if COLLECTION_NAME not in utility.list_collections():
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="content_id", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="user_id", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="platform", dtype=DataType.VARCHAR, max_length=20),
        FieldSchema(name="summary", dtype=DataType.VARCHAR, max_length=4000),
        FieldSchema(name="timestamp", dtype=DataType.INT64),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=768),
    ]

    schema = CollectionSchema(
        fields, description="Unified embeddings for TikTok + Facebook content"
    )
    collection = Collection(COLLECTION_NAME, schema)
    print("🆕 Created collection:", COLLECTION_NAME)

    # Sử dụng chỉ mục IVF_FLAT, phù hợp cho kích thước 768 chiều
    # nlist là tham số cấu hình, bạn có thể điều chỉnh sau
    index_params = {
        "index_type": "IVF_FLAT",
        "metric_type": "COSINE",
        "params": {"nlist": 128},  # Có thể điều chỉnh
    }
    index_result = collection.create_index(
        field_name="embedding", index_params=index_params
    )
    print("✅ Created Index for 'embedding'")
    print("🆕 Created collection:", COLLECTION_NAME)
else:
    collection = Collection(COLLECTION_NAME)
    print("📁 Using existing collection:", COLLECTION_NAME)

collection.load()
print(f"🚀 Loaded collection: {COLLECTION_NAME}")

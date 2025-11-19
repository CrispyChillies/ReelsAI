from pymilvus import (
    connections,
    Collection,
    FieldSchema,
    CollectionSchema,
    DataType,
    utility,
)

# ========= CONFIG =========
ZILLIZ_URI = "https://in03-3a28b4019057a01.serverless.aws-eu-central-1.cloud.zilliz.com"
ZILLIZ_TOKEN = "fd04e95024f15549f34465178ad131d6b646228f429eca8c469a4c218decc776ba584d111e86e1b40a006fad72f4b63822785d27"
COLLECTION_NAME = "user_saved_items_embeddings"

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

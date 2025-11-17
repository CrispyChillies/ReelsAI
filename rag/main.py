from fastapi import FastAPI
from pydantic import BaseModel
from pymilvus import (
    connections,
    Collection,
    FieldSchema,
    CollectionSchema,
    DataType,
    utility,
)
from sentence_transformers import SentenceTransformer

# ========= CONFIG =========
ZILLIZ_URI = "https://in03-631a9c68371d54c.serverless.aws-eu-central-1.cloud.zilliz.com"
ZILLIZ_TOKEN = "fd04e95024f15549f34465178ad131d6b646228f429eca8c469a4c218decc776ba584d111e86e1b40a006fad72f4b63822785d27"
COLLECTION_NAME = "tiktok_videos"

# ========= CONNECT =========
connections.connect(alias="default", uri=ZILLIZ_URI, token=ZILLIZ_TOKEN)
print("✅ Connected to Zilliz Cloud")

# ========= DEFINE SCHEMA =========
if COLLECTION_NAME not in utility.list_collections():
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="video_id", dtype=DataType.VARCHAR, max_length=255),
        FieldSchema(name="summary", dtype=DataType.VARCHAR, max_length=2000),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
        FieldSchema(name="like_count", dtype=DataType.INT64),
        FieldSchema(name="share_count", dtype=DataType.INT64),
        FieldSchema(name="view_count", dtype=DataType.INT64),
        FieldSchema(name="comment_count", dtype=DataType.INT64),
        FieldSchema(name="collect_count", dtype=DataType.INT64),
        FieldSchema(name="popularity_score", dtype=DataType.FLOAT),
    ]

    schema = CollectionSchema(
        fields, description="TikTok video data with embeddings and engagement stats"
    )
    collection = Collection("tiktok_videos", schema)
    print("🆕 Created collection:", COLLECTION_NAME)
else:
    collection = Collection(COLLECTION_NAME)
    print("📁 Using existing collection:", COLLECTION_NAME)

# ========= EMBEDDING MODEL =========
model = SentenceTransformer("keepitreal/vietnamese-sbert")

# ========= FASTAPI APP =========
app = FastAPI(title="Tiktok RAG Agent API")


class VideoData(BaseModel):
    video_id: str
    summary: str
    like_count: int = 0
    share_count: int = 0
    view_count: int = 0
    comment_count: int = 0
    collect_count: int = 0
    popularity_score: int = 0


class QueryRequest(BaseModel):
    query: str
    top_k: int = 3


@app.put("/videos")
def add_video(data: VideoData):
    embedding = model.encode(data.summary).tolist()
    collection.insert([[data.video_id], [data.summary], [embedding]])
    collection.flush()
    return {"status": "success", "video_id": data.video_id}


@app.post("/query")  # query knowledge graph (link videos) + vector database
def query_videos(req: QueryRequest):
    query_vec = model.encode(req.query).tolist()
    search_params = {"metric_type": "IP", "params": {"nprobe": 10}}
    results = collection.search(
        data=[query_vec],
        anns_field="embedding",
        param=search_params,
        limit=req.top_k,
        output_fields=["video_id", "summary"],
    )

    hits = []
    for r in results[0]:
        hits.append(
            {
                "video_id": r.entity.get("video_id"),
                "summary": r.entity.get("summary"),
                "score": r.score,
            }
        )

    return {"query": req.query, "results": hits}

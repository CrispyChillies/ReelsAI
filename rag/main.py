from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict
from typing import Optional
from sentence_transformers import SentenceTransformer
from milvus_setup import collection

# ========= EMBEDDING MODEL =========
model = SentenceTransformer("keepitreal/vietnamese-sbert")

# ========= FASTAPI APP =========
app = FastAPI(title="Tiktok RAG Agent API")


class ItemData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content_id: str  # UUID hoặc TikTok video ID
    user_id: str  # user đã lưu
    platform: str  # "tiktok" | "facebook"
    summary: str  # summary sinh ra từ captioning
    timestamp: int  # unix timestamp


class QueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str
    query: str
    top_k: int = 5
    from_timestamp: Optional[int] = None
    platform: Optional[str] = None


@app.put("/add-item")
def add_item(data: ItemData):
    embedding = model.encode(data.summary).tolist()

    content_id_col = [data.content_id]
    user_id_col = [data.user_id]
    platform_col = [data.platform]
    summary_col = [data.summary]
    timestamp_col = [data.timestamp]
    embedding_col = [embedding]

    data_to_insert = [
        content_id_col,
        user_id_col,
        platform_col,
        summary_col,
        timestamp_col,
        embedding_col,
    ]

    collection.insert(data_to_insert)
    collection.flush()

    return {"status": "success", "content_id": data.content_id}


@app.post("/query-items")
def query_items(req: QueryRequest):
    query_vec = model.encode(req.query).tolist()

    # Build filter expression
    expr_parts = [f"user_id == '{req.user_id}'"]

    if req.from_timestamp:
        expr_parts.append(f"timestamp >= {req.from_timestamp}")

    if req.platform:
        expr_parts.append(f"platform == '{req.platform}'")

    expr = " && ".join(expr_parts)

    search_params = {"metric_type": "COSINE", "params": {"ef": 64}}

    results = collection.search(
        data=[query_vec],
        anns_field="embedding",
        param=search_params,
        limit=req.top_k,
        expr=expr,
        output_fields=["content_id", "summary", "platform", "timestamp"],
    )

    hits = []
    for hit in results[0]:
        hits.append(
            {
                "content_id": hit.entity.get("content_id"),
                "summary": hit.entity.get("summary"),
                "platform": hit.entity.get("platform"),
                "timestamp": hit.entity.get("timestamp"),
                "score": hit.score,
            }
        )

    return {"query": req.query, "filter": expr, "results": hits}

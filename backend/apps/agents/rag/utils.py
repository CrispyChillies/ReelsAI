from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Lazy load to avoid loading model on import
_model = None
_collection = None


def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        try:
            _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        except Exception as e:
            logger.exception("Failed to load SentenceTransformer model: %s", e)
            _model = None
    return _model


def get_collection():
    global _collection
    if _collection is None:
        try:
            from .milvus_setup import collection

            _collection = collection
        except Exception as e:
            logger.exception("Failed to import milvus collection: %s", e)
            _collection = None
    return _collection


def _build_columns_for_insert(data_map: Dict[str, Any]) -> List[List[Any]]:
    """
    Build column-wise payload according to collection.schema order,
    skipping auto id if present.
    """
    collection = get_collection()
    if collection is None:
        raise RuntimeError("Milvus collection is not available")

    schema_fields = [f.name for f in collection.schema.fields]
    # skip auto id field if collection.auto_id True (usually 'id')
    if collection.schema.auto_id:
        schema_fields = schema_fields[1:]

    # map expected names -> provided values
    # Expect embedding field named 'embedding'
    columns = []
    for fname in schema_fields:
        if fname == "embedding":
            # embedding should be a list of floats
            columns.append([data_map["embedding"]])
        else:
            columns.append([data_map[fname]])
    return columns


def insert_item(
    content_id: str,
    content_url: str,
    user_id: str,
    platform: str,
    summary: str,
    timestamp: Optional[int] = None,
):
    model = get_model()
    collection = get_collection()
    if collection is None or model is None:
        raise RuntimeError("Dependencies missing: model or collection")

    embedding = model.encode(summary).tolist()
    values_map = {
        "content_id": content_id,
        "content_url": content_url,
        "user_id": user_id,
        "platform": platform,
        "summary": summary,
        "timestamp": timestamp,
        "embedding": embedding,
    }

    # Only add timestamp if it exists in schema
    # (kept for backwards compatibility if you re-add it later)
    # if timestamp is not None:
    #     values_map["timestamp"] = timestamp

    columns = _build_columns_for_insert(values_map)
    collection.insert(columns)
    collection.flush()
    return {"status": "success", "content_id": content_id}


def query_items(
    user_id: str,
    query: str,
    top_k: int = 5,
    from_timestamp: Optional[int] = None,
    platform: Optional[str] = None,
) -> Dict[str, Any]:
    model = get_model()
    collection = get_collection()
    if collection is None or model is None:
        raise RuntimeError("Dependencies missing: model or collection")

    query_vec = model.encode(query).tolist()
    expr_parts = [f"user_id == '{user_id}'"]
    if from_timestamp:
        expr_parts.append(f"timestamp >= {from_timestamp}")
    if platform:
        expr_parts.append(f"platform == '{platform}'")
    expr = " && ".join(expr_parts)

    search_params = {"metric_type": "COSINE", "params": {"ef": 64}}
    results = collection.search(
        data=[query_vec],
        anns_field="embedding",
        param=search_params,
        limit=top_k,
        expr=expr,
        output_fields=["content_id", "content_url", "summary", "platform", "timestamp"],
    )

    hits = []
    if results and len(results) > 0:
        for hit in results[0]:
            ent = hit.entity
            hits.append(
                {
                    "content_id": ent.get("content_id"),
                    "content_url": ent.get("content_url"),
                    "summary": ent.get("summary"),
                    "platform": ent.get("platform"),
                    "timestamp": ent.get("timestamp"),
                    "score": hit.score,
                }
            )

    return {"query": query, "filter": expr, "results": hits}

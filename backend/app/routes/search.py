from fastapi import APIRouter, Query, HTTPException
import os
import numpy as np  # ✅ FIX: Needed for np.floating
from backend.app.services.topic_service import get_topic_service

router = APIRouter()

_ts = None


def _ensure_service():
    global _ts
    if _ts is None:
        topics_model_path = os.path.abspath(r"backend/app/ml/models/topics/bertopic_india_global")
        articles_csv = os.path.abspath(r"backend/app/ml/data/topic_corpus/ag_bbc_india_with_topics.csv")
        _ts = get_topic_service(model_path=topics_model_path, articles_csv=articles_csv)
    return _ts


# --- GLOBAL SANITIZER (fixes NaN crashing JSON) ------------------------------------
import math

def clean_json(obj):
    """Recursively clean floats (nan/inf) in lists, dicts, tuples."""
    if isinstance(obj, dict):
        return {k: clean_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_json(v) for v in obj]
    if isinstance(obj, tuple):
        return tuple(clean_json(list(obj)))
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return 0.0
        return float(obj)
    if isinstance(obj, (np.floating,)):
        v = float(obj)
        if math.isnan(v) or math.isinf(v):
            return 0.0
        return v
    return obj
# -----------------------------------------------------------------------------


@router.get("/search", summary="Keyword + semantic search")
def search(q: str = Query(..., min_length=2), k: int = 10):
    svc = _ensure_service()

    kw_results = svc.keyword_search(q, top_k=k)

    if svc.has_embeddings():
        sem_results = svc.semantic_search(q, top_k=k)

        response = {
            "query": q,
            "semantic": sem_results,
            "keyword": kw_results
        }
    else:
        response = {
            "query": q,
            "keyword": kw_results
        }

    return clean_json(response)  # ✅ sanitize before sending JSON


@router.get("/recommend", summary="Recommend similar articles by article id")
def recommend(article_id: int, k: int = 5):
    svc = _ensure_service()

    if not svc.has_embeddings():
        raise HTTPException(status_code=400, detail="Embeddings not found.")

    results = svc.recommend_by_article(article_id, top_k=k)

    return clean_json({
        "article_id": article_id,
        "results": results
    })

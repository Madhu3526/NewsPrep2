# backend/app/routes/topics.py

from fastapi import APIRouter, HTTPException
import math

from sqlalchemy import func
from backend.app.db.session import SessionLocal
from backend.app.db.models.article import Article

# Topic service (optional: only for metadata / keywords)
try:
    from backend.app.services.topic_service import get_topic_service
    TS_AVAILABLE = True
except Exception:
    TS_AVAILABLE = False

router = APIRouter()

# Global reference to topic service
_ts = None


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
def safe_json(obj):
    """Convert NaN/inf to None for JSON."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: safe_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [safe_json(v) for v in obj]
    return obj


# -------------------------------------------------------------------
# Startup → Load BERTopic model (optional, only if available)
# -------------------------------------------------------------------
@router.on_event("startup")
def startup_topic_service():
    global _ts

    if not TS_AVAILABLE:
        print("Topic service not available. Using DB-only topics.")
        return

    MODEL_PATH = "backend/app/ml/models/topics/bertopic_global"
    CSV_PATH = "backend/app/ml/data/topic_corpus/ag_bbc_india_with_topics.csv"
    KEYWORDS_PATH = "backend/app/ml/models/topics/bertopic_keywords.json"

    try:
        print("Loading BERTopic service...")
        _ts = get_topic_service(
            model_path=MODEL_PATH,
            articles_csv=CSV_PATH  # Only used for topic names — articles come from DB
        )
        # Load keywords for better topic names
        import json
        import os
        if os.path.exists(KEYWORDS_PATH):
            with open(KEYWORDS_PATH, 'r') as f:
                _ts.topic_keywords = json.load(f)
        print("Topic service loaded.")
    except Exception as e:
        print("Failed to load topic service:", e)
        _ts = None


# -------------------------------------------------------------------
# GET /api/topics  → ALL TOPICS (DB is source of truth)
# -------------------------------------------------------------------
@router.get("/", summary="List all discovered topics")
def list_topics():
    db = SessionLocal()
    try:
        # Count articles per topic from DB
        counts = {
            row[0]: row[1]
            for row in db.query(Article.topic_id, func.count(Article.id))
                         .group_by(Article.topic_id)
                         .all()
        }
    finally:
        db.close()

    topics_list = []

    # If BERTopic metadata available → enrich names/keywords
    if _ts and _ts.topic_model:
        topic_info = _ts.get_topic_info()

        for t in topic_info:
            tid = int(t["Topic"])
            if tid == -1:
                continue

            # Get better topic name from keywords
            topic_name = f"Topic {tid}"
            keywords = t.get("Representation", [])
            
            if hasattr(_ts, 'topic_keywords') and str(tid) in _ts.topic_keywords:
                kw_list = _ts.topic_keywords[str(tid)][:3]  # Top 3 keywords
                topic_name = " | ".join(kw_list).title()
                keywords = _ts.topic_keywords[str(tid)]
            elif t.get("Name"):
                topic_name = t.get("Name")
            elif keywords:
                topic_name = " | ".join(keywords[:3]).title()
                
            topics_list.append({
                "topic_id": tid,
                "name": topic_name,
                "keywords": keywords,
                "count": int(counts.get(tid, 0)),
            })

    else:
        # Fallback: DB-only topics with keywords if available
        for tid, cnt in counts.items():
            if tid is None or tid == -1:
                continue
            
            topic_name = f"Topic {tid}"
            keywords = []
            
            if _ts and hasattr(_ts, 'topic_keywords') and str(tid) in _ts.topic_keywords:
                kw_list = _ts.topic_keywords[str(tid)][:3]
                topic_name = " | ".join(kw_list).title()
                keywords = _ts.topic_keywords[str(tid)]
                
            topics_list.append({
                "topic_id": int(tid),
                "name": topic_name,
                "keywords": keywords,
                "count": int(cnt),
            })

    return safe_json(topics_list)


# -------------------------------------------------------------------
# GET /api/topics/{topic_id}  → Topic detail + articles
# -------------------------------------------------------------------
@router.get("/{topic_id}", summary="Get topic metadata + top 50 articles")
def get_topic(topic_id: int):

    # Get topic metadata (if BERTopic available)
    if _ts and _ts.topic_model:
        try:
            meta = _ts.get_topic_info(topic_id)
        except Exception:
            meta = None
    else:
        meta = None

    # Fetch articles from DB
    db = SessionLocal()
    try:
        rows = (
            db.query(Article)
              .filter(Article.topic_id == topic_id)
              .order_by(Article.published_date.desc())
              .limit(50)
              .all()
        )
    finally:
        db.close()

    docs = [
        {
            "id": r.id,
            "title": r.title,
            "text": (r.text or "")[:800],
            "summary": r.summary,
            "key_points": r.key_points,
            "published": r.published_date.isoformat() if r.published_date else None,
        }
        for r in rows
    ]

    # Get better topic name
    topic_name = f"Topic {topic_id}"
    keywords = []
    
    if meta:
        topic_name = meta.get("Name", f"Topic {topic_id}")
        keywords = meta.get("Representation", [])
    
    if _ts and hasattr(_ts, 'topic_keywords') and str(topic_id) in _ts.topic_keywords:
        kw_list = _ts.topic_keywords[str(topic_id)][:3]
        topic_name = " | ".join(kw_list).title()
        keywords = _ts.topic_keywords[str(topic_id)]
    
    return {
        "topic_id": topic_id,
        "name": topic_name,
        "keywords": keywords,
        "docs": docs
    }


# -------------------------------------------------------------------
# GET /api/topics/{topic_id}/example → Representative docs
# -------------------------------------------------------------------
@router.get("/{topic_id}/example", summary="Representative sample docs for topic")
def example_articles(topic_id: int, n: int = 12):

    if not _ts:
        raise HTTPException(
            status_code=400,
            detail="No topic model available — cannot get representative docs."
        )

    docs = _ts.get_representative_docs(topic_id, top_n=n)
    return safe_json(docs)

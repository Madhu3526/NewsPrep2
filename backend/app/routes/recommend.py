from fastapi import APIRouter, HTTPException
from typing import List

from backend.app.services.recommender import get_recommender
import os
import json

from fastapi import Query

# collaborative artifacts
_COLLAB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "collab_recs.json"))
_POP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "popularity.json"))

def _load_collab():
    if not os.path.exists(_COLLAB_PATH):
        return {}
    try:
        with open(_COLLAB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _load_pop():
    if not os.path.exists(_POP_PATH):
        return {}
    try:
        with open(_POP_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

router = APIRouter()


@router.get("/article/{article_id}", summary="Recommend by article id")
def recommend_by_article(article_id: int, n: int = 8):
    r = get_recommender()
    try:
        pairs = r.similar_by_article(article_id, top_n=n)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))

    ids = [pid for pid, score in pairs]
    metas = r.get_article_meta(ids)
    # attach scores in same order
    id_to_score = {pid: score for pid, score in pairs}
    out = []
    for m in metas:
        out.append({
            "id": m["id"],
            "title": m.get("title"),
            "excerpt": m.get("excerpt"),
            "score": float(id_to_score.get(m["id"], 0.0)),
            "topic_id": m.get("topic_id"),
        })
    return out


@router.get("/topic/{topic_id}", summary="Recommend by topic id")
def recommend_by_topic(topic_id: int, n: int = 8):
    r = get_recommender()
    try:
        pairs = r.similar_by_topic(topic_id, top_n=n)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))

    ids = [pid for pid, score in pairs]
    metas = r.get_article_meta(ids)
    id_to_score = {pid: score for pid, score in pairs}
    out = []
    for m in metas:
        out.append({
            "id": m["id"],
            "title": m.get("title"),
            "excerpt": m.get("excerpt"),
            "score": float(id_to_score.get(m["id"], 0.0)),
            "topic_id": m.get("topic_id"),
        })
    return out


@router.get("/collab/article/{article_id}", summary="Collaborative recs by article id")
def collab_by_article(article_id: int, n: int = 8):
    collab = _load_collab()
    lst = collab.get(str(article_id)) or collab.get(int(article_id)) or []
    # lst is list of [id, count]
    ids = [int(x[0]) for x in lst[:n]]
    r = get_recommender()
    metas = r.get_article_meta(ids)
    id_to_score = {int(x[0]): float(x[1]) for x in lst}
    out = []
    for m in metas:
        out.append({
            "id": m["id"],
            "title": m.get("title"),
            "excerpt": m.get("excerpt"),
            "score": float(id_to_score.get(m["id"], 0.0)),
            "topic_id": m.get("topic_id"),
        })
    return out


@router.get("/hybrid/article/{article_id}", summary="Hybrid recs for article")
def hybrid_by_article(article_id: int, n: int = 8, alpha: float = Query(0.7), beta: float = Query(0.2)):
    """Blend content-based (alpha) with collaborative (beta) and popularity (remaining)."""
    # load sources
    r = get_recommender()
    content = r.similar_by_article(article_id, top_n=50)
    collab = _load_collab()
    pop = _load_pop()

    collab_scores = {int(x[0]): float(x[1]) for x in collab.get(str(article_id), [])}
    pop_max = max(pop.values()) if pop else 1

    # candidates: union of top content and collab keys
    candidate_ids = set([int(x[0]) for x in content]) | set(collab_scores.keys())

    results = []
    for cid in candidate_ids:
        c_score = next((s for aid, s in content if int(aid) == int(cid)), 0.0)
        k_score = collab_scores.get(int(cid), 0.0)
        p_score = float(pop.get(str(cid), pop.get(int(cid), 0))) / (pop_max or 1)
        final = alpha * float(c_score) + beta * float(k_score) + (1 - alpha - beta) * float(p_score)
        results.append((cid, final))

    results.sort(key=lambda x: x[1], reverse=True)
    ids = [r[0] for r in results[:n]]
    metas = get_recommender().get_article_meta(ids)
    id_to_score = {k: v for k, v in results}
    out = []
    for m in metas:
        out.append({
            "id": m["id"],
            "title": m.get("title"),
            "excerpt": m.get("excerpt"),
            "score": float(id_to_score.get(m["id"], 0.0)),
            "topic_id": m.get("topic_id"),
        })
    return out

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import os
from datetime import datetime

from backend.app.db.session import SessionLocal
from backend.app.db.models.interaction import UserInteraction
from backend.app.db.models.article_stats import ArticleStats

router = APIRouter()

EVENTS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "events.jsonl"))


class EventIn(BaseModel):
    user_id: Optional[int] = None
    event: str
    item_id: int
    context: Optional[Dict[str, Any]] = None
    ts: Optional[datetime] = None


@router.post("/", status_code=201)
def post_event(ev: EventIn):
    # ensure folder exists
    os.makedirs(os.path.dirname(EVENTS_FILE), exist_ok=True)
    record = ev.dict()
    record["ts"] = (ev.ts or datetime.utcnow()).isoformat()
    # append JSONL for audit/backups
    try:
        with open(EVENTS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        # non-fatal; continue to DB persist
        pass

    # persist to DB: update ArticleStats and insert UserInteraction
    db = SessionLocal()
    try:
        # update stats table
        stats = db.query(ArticleStats).get(int(ev.item_id))
        if not stats:
            stats = ArticleStats(article_id=int(ev.item_id), views=0, likes=0, bookmarks=0)
            db.add(stats)

        if ev.event == "view":
            stats.views = (stats.views or 0) + 1
        elif ev.event == "like":
            stats.likes = (stats.likes or 0) + 1
        elif ev.event == "bookmark":
            stats.bookmarks = (stats.bookmarks or 0) + 1

        # user interaction row
        ui = UserInteraction(user_id=ev.user_id, article_id=ev.item_id, event_type=ev.event)
        db.add(ui)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

    return {"ok": True}

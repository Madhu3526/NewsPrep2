from fastapi import APIRouter, HTTPException, Body, Query
from pydantic import BaseModel
from backend.app.services.summarizer import summarize_article_and_store, summarize_text

router = APIRouter()


class SummarizeRequest(BaseModel):
    article_id: int
    use_abstractive: bool = True


@router.post("/summarize")
def summarize(req: SummarizeRequest):
    result = summarize_article_and_store(req.article_id, use_abstractive=req.use_abstractive)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/summarize")
def summarize_text_endpoint(text: str = Query(...), type: str = Query("abstractive")):
    try:
        use_abstractive = type == "abstractive"
        summary = summarize_text(text, use_abstractive=use_abstractive)
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/summarize/{article_id}")
def summarize_by_id(article_id: int, payload: dict = Body(default=None)):
    # Accepts an optional JSON body like {"abstractive": true}
    use_abstractive = True
    if isinstance(payload, dict) and "abstractive" in payload:
        use_abstractive = bool(payload.get("abstractive"))

    result = summarize_article_and_store(article_id, use_abstractive=use_abstractive)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    return result

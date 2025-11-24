from fastapi import APIRouter, HTTPException
from backend.app.services.quiz_service import generate_quiz_from_article, get_quiz

router = APIRouter()

@router.post("/quiz/{article_id}")
def create_quiz(article_id: int):
    result = generate_quiz_from_article(article_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/quiz/{quiz_id}")
def fetch_quiz(quiz_id: int):
    data = get_quiz(quiz_id)
    if not data:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return data

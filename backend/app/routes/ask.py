from fastapi import APIRouter
from pydantic import BaseModel
from backend.app.services.rag_service import ask_question

router = APIRouter()

class AskRequest(BaseModel):
    query: str

@router.post("/ask")
def ask(req: AskRequest):
    return ask_question(req.query)

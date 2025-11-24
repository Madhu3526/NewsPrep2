from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List

from backend.app.db.session import SessionLocal
from backend.app.db.models.quiz import Quiz, QuizQuestion
from backend.app.db.models.article import Article


# --------------------------
# QUIZ OUTPUT STRUCTURE
# --------------------------

class QuizQuestionSchema(BaseModel):
    question: str
    options: List[str]
    answer: str

class QuizSchema(BaseModel):
    title: str
    questions: List[QuizQuestionSchema]


quiz_parser = PydanticOutputParser(pydantic_object=QuizSchema)

# Llama model
llm = Ollama(model="llama3.1")


# --------------------------
# QUIZ GENERATOR
# --------------------------

def generate_quiz_from_article(article_id: int):
    """Generate MCQ quiz using Llama3.1 based on article summary."""

    db = SessionLocal()

    try:
        article = db.query(Article).filter(Article.id == article_id).first()
        if not article:
            return {"error": "Article not found"}

        base_text = article.summary or article.text[:1200]

        prompt = (
            "You are a quiz generator. Create a quiz from this summary.\n\n"
            "Return ONLY valid JSON.\n\n"
            "{format_instructions}\n\n"
            "Summary:\n{summary}\n"
        )

        chain = LLMChain(
            llm=llm,
            prompt=PromptTemplate(
                input_variables=["summary", "format_instructions"],
                template=prompt,
            )
        )

        raw = chain.run(
            summary=base_text,
            format_instructions=quiz_parser.get_format_instructions()
        )

        quiz_data: QuizSchema = quiz_parser.parse(raw)

        # -------------------------
        # Save to database
        # -------------------------
        quiz = Quiz(article_id=article_id, title=quiz_data.title)
        db.add(quiz)
        db.flush()  # Get quiz.id before inserting questions

        for q in quiz_data.questions:
            qq = QuizQuestion(
                quiz_id=quiz.id,
                question=q.question,
                options=q.options,
                answer=q.answer
            )
            db.add(qq)

        db.commit()

        return {"quiz_id": quiz.id}

    finally:
        db.close()


def get_quiz(quiz_id: int):
    db = SessionLocal()
    try:
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            return None
        
        return {
            "id": quiz.id,
            "article_id": quiz.article_id,
            "title": quiz.title,
            "questions": [
                {
                    "id": q.id,
                    "question": q.question,
                    "options": q.options,
                    "answer": q.answer
                }
                for q in quiz.questions
            ]
        }
    finally:
        db.close()

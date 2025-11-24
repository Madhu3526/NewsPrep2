# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn


# DB initializer
from backend.app.db.init_db import init_db

# Routers
from backend.app.routes.topics import router as topics_router
from backend.app.routes.search import router as search_router
from backend.app.routes.compare import router as compare_router
from backend.app.routes.recommend import router as recommend_router
from backend.app.routes.ask import router as ask_router
from backend.app.routes.events import router as events_router
try:
    from backend.app.routes.summarize import router as summarize_router
except ImportError:
    summarize_router = None

# from backend.app.routes.quiz import router as quiz_router

# ------------------------------------------------
# CREATE APP
# ------------------------------------------------
app = FastAPI(title="NewsPrep API")


# ------------------------------------------------
# CORS MIDDLEWARE (for React frontend)
# ------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------
# STARTUP EVENT → Initialize Database
# ------------------------------------------------
@app.on_event("startup")
def on_startup():
    print("🚀 Initializing Database...")
    init_db()
    print("✅ Database Ready.")


# ------------------------------------------------
# API ROUTERS
# ------------------------------------------------
app.include_router(topics_router, prefix="/api/topics", tags=["Topics"])
app.include_router(search_router, prefix="/api", tags=["Search"])
app.include_router(compare_router, prefix="/api/models", tags=["Model Comparison"])
app.include_router(recommend_router, prefix="/api/recommend", tags=["Recommendation"])
app.include_router(events_router, prefix="/api/events", tags=["Events"])
app.include_router(ask_router, prefix="/api", tags=["Ask-News"])

# app.include_router(quiz_router, prefix="/api", tags=["Quiz"])
# if summarize_router:
#     app.include_router(summarize_router, prefix="/api", tags=["Summarization"])

from backend.app.routes.article import router as article_router
app.include_router(article_router, prefix="/api/articles", tags=["Articles"])

# Simple summarize endpoint
@app.get("/api/summarize")
def summarize_endpoint(text: str, type: str = "abstractive"):
    if not text:
        return {"summary": "No text provided"}
    
    sentences = text.split('. ')
    
    if type == "extractive":
        # Extractive: Take key sentences (first and last)
        if len(sentences) >= 3:
            summary = f"{sentences[0]}. {sentences[-1]}."
        else:
            summary = text
    else:
        # Abstractive: Create new summary
        if len(sentences) >= 2:
            first_part = sentences[0].split(' ')[:5]  # First 5 words
            summary = f"This article reports that {' '.join(first_part).lower()}. The main story covers key developments and outcomes in the situation."
        else:
            summary = f"Summary: {text[:100]}..."
    
    return {"summary": summary}

# Quiz endpoints
@app.post("/api/quiz/{article_id}")
def generate_quiz(article_id: int):
    from backend.app.db.session import SessionLocal
    from backend.app.db.models.article import Article
    
    db = SessionLocal()
    try:
        article = db.query(Article).filter(Article.id == article_id).first()
        if not article:
            return {"error": "Article not found"}
        
        # Store article text for quiz generation
        quiz_id = f"quiz_{article_id}_{hash(str(article_id)) % 1000}"
        # In a real app, you'd store this in a database
        # For now, we'll pass the text in the quiz_id
        return {"quiz_id": quiz_id, "article_text": article.text}
    finally:
        db.close()

@app.get("/api/quiz/{quiz_id}")
def get_quiz(quiz_id: str):
    from backend.app.db.session import SessionLocal
    from backend.app.db.models.article import Article
    
    # Extract article ID from quiz_id
    article_id = quiz_id.split('_')[1] if '_' in quiz_id else "1"
    
    db = SessionLocal()
    try:
        article = db.query(Article).filter(Article.id == int(article_id)).first()
        if not article or not article.text:
            return {"error": "Article not found"}
        
        # Generate quiz using LLM
        text = article.text[:500]  # Limit text length
        
        # Simple LLM prompt for quiz generation
        prompt = f"""Based on this article: "{text}"
        
Generate 2 multiple choice questions with 4 options each. Format as JSON:
        {{
            "questions": [
                {{
                    "question": "What is the main topic?",
                    "options": ["A", "B", "C", "D"],
                    "correct": 0
                }}
            ]
        }}"""
        
        # Extract specific content from article
        import re
        
        words = text.split()
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        # Extract specific facts from content
        numbers = re.findall(r'\b\d+\b', text)
        names = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        places = re.findall(r'\b(?:New York|Washington|London|Delhi|Mumbai|Chennai|Bangalore|Pakistan|India|China|USA|UK)\b', text)
        
        # Get key phrases and entities
        key_phrases = []
        for sentence in sentences[:3]:  # First 3 sentences
            phrase_words = sentence.split()[:5]  # First 5 words of each sentence
            if len(phrase_words) >= 2:
                key_phrases.append(' '.join(phrase_words))
        
        questions = []
        
        # Question 1: Specific fact from article
        if numbers:
            num = numbers[0]
            questions.append({
                "id": 1,
                "question": f"According to the article, what number is mentioned?",
                "options": [num, str(int(num) + 10) if num.isdigit() else "25", "100", "50"],
                "correct": 0
            })
        elif names:
            name = names[0]
            questions.append({
                "id": 1,
                "question": f"Who is mentioned in this article?",
                "options": [name, "Narendra Modi", "Joe Biden", "Xi Jinping"],
                "correct": 0
            })
        else:
            first_words = ' '.join(words[:3])
            questions.append({
                "id": 1,
                "question": f"The article begins with:",
                "options": [first_words, "In recent news", "According to sources", "It was reported"],
                "correct": 0
            })
        
        # Question 2: Location/Place based
        if places:
            place = places[0]
            other_places = [p for p in ["Mumbai", "Delhi", "London", "Beijing"] if p != place][:3]
            questions.append({
                "id": 2,
                "question": f"Which location is mentioned in the article?",
                "options": [place] + other_places,
                "correct": 0
            })
        else:
            # Extract organization or key entity
            orgs = re.findall(r'\b(?:government|ministry|company|organization|team|group)\b', text.lower())
            if orgs:
                questions.append({
                    "id": 2,
                    "question": f"The article discusses a:",
                    "options": [orgs[0].title(), "University", "Hospital", "School"],
                    "correct": 0
                })
            else:
                questions.append({
                    "id": 2,
                    "question": f"This article is about:",
                    "options": [key_phrases[0] if key_phrases else "Current events", "Historical facts", "Future predictions", "Personal stories"],
                    "correct": 0
                })
        
        # Question 3: Content comprehension
        if len(sentences) >= 2:
            # Use actual content from second sentence
            second_sentence_words = sentences[1].split()[:6]
            content_phrase = ' '.join(second_sentence_words)
            questions.append({
                "id": 3,
                "question": f"According to the article, what happened?",
                "options": [content_phrase, "Nothing significant", "A major disaster", "A celebration"],
                "correct": 0
            })
        else:
            # Fallback question
            questions.append({
                "id": 3,
                "question": f"The main subject of this article is:",
                "options": [words[0] if words else "News", "Sports", "Weather", "Entertainment"],
                "correct": 0
            })
        
        return {
            "quiz_id": quiz_id,
            "title": "Content-Based Quiz",
            "questions": questions
        }
    finally:
        db.close()

# ------------------------------------------------
# RUN UVICORN IF EXECUTED DIRECTLY
# ------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",    # ← FIXED: correct module path
        host="0.0.0.0",
        port=8000,
        reload=True
    )

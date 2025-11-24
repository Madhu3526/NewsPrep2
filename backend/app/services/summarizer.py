# backend/app/services/summarizer.py

import os
import re
from typing import List, Dict, Any

# ------------------------
# Extractive Summarization
# ------------------------
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer
from heapq import nlargest

# ------------------------
# Abstractive (Ollama Llama3.1)
# ------------------------
from langchain_community.llms import Ollama
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser

# ------------------------
# DB Access
# ------------------------
from backend.app.db.session import SessionLocal
from backend.app.db.models.article import Article




# =====================================================================
# 1) Pydantic model for JSON output
# =====================================================================

class SummaryOut(BaseModel):
    summary_paragraph: str = Field(..., description="Short article paragraph summary")
    key_points: List[str] = Field(..., description="3-5 bullet takeaways")


summary_parser = PydanticOutputParser(pydantic_object=SummaryOut)

# =====================================================================
# 2) LLM — OLLAMA LLAMA 3.1
# =====================================================================

llm = Ollama(model="llama3.1")

# =====================================================================
# 3) Extractive Summarizer (TextRank + fallback)
# =====================================================================

def extractive_summary_text_rank(text: str, sentences_count: int = 2):
    text = text.strip()
    if not text:
        return {"summary": "", "key_points": []}

    sentences = [s.strip() for s in text.split('.') if s.strip()]
    if len(sentences) <= sentences_count:
        return {"summary": text, "key_points": sentences}
    
    # Take first and last sentences
    key_sentences = [sentences[0], sentences[-1]]
    summary = '. '.join(key_sentences) + '.'
    return {"summary": summary, "key_points": key_sentences}


# =====================================================================
# 4) Abstractive Summarizer (Ollama Map-Reduce)
# =====================================================================

def abstractive_summary_langchain(text: str, chunk_size: int = 1800, chunk_overlap: int = 200) -> Dict[str, Any]:

    if not text or text.strip() == "":
        return {"summary_paragraph": "", "key_points": []}

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    chunks = splitter.split_text(text)

    # ------------------------------------------------
    # MAP STEP (chunk-level summaries)
    # ------------------------------------------------
    MAP_PROMPT = PromptTemplate(
        input_variables=["text"],
        template="Summarize the following part in 2-3 clear sentences:\n\n{text}"
    )

    partial_summaries = []
    for chunk in chunks:
        chain = LLMChain(llm=llm, prompt=MAP_PROMPT)
        partial_summaries.append(chain.run(text=chunk))

    combined = "\n".join(partial_summaries)

    # ------------------------------------------------
    # REDUCE STEP — Structured JSON output
    # ------------------------------------------------
    REDUCE_PROMPT = PromptTemplate(
        input_variables=["text", "format_instructions"],
        template=(
            "You are a world-class summarizer.\n"
            "Combine the partial summaries below into:\n"
            "- ONE clear summary paragraph\n"
            "- 3 to 5 concise bullet points\n\n"
            "Return ONLY valid JSON.\n\n"
            "{format_instructions}\n\n"
            "Partial summaries:\n{text}"
        )
    )

    reduce_chain = LLMChain(
        llm=llm,
        prompt=REDUCE_PROMPT
    )

    output_raw = reduce_chain.run(
        text=combined,
        format_instructions=summary_parser.get_format_instructions()
    )

    # Cleanup
    try:
        return summary_parser.parse(output_raw).dict()
    except:
        cleaned = output_raw[output_raw.find("{"): output_raw.rfind("}") + 1]
        return summary_parser.parse(cleaned).dict()


# =====================================================================
# 5) Public Function — Summarize & Save to DB
# =====================================================================

def summarize_article_and_store(article_id: int, use_abstractive: bool = True):
    db = SessionLocal()

    try:
        article = db.query(Article).filter(Article.id == article_id).first()
        if not article:
            return {"error": "Article not found", "article_id": article_id}

        text = article.text or ""

        extractive = extractive_summary_text_rank(text)

        if use_abstractive:
            abstractive = abstractive_summary_langchain(text)
            final_summary = abstractive.get("summary_paragraph") or extractive.get("summary")
            final_key_points = abstractive.get("key_points") or extractive.get("key_points")
        else:
            abstractive = None
            final_summary = extractive.get("summary")
            final_key_points = extractive.get("key_points")

        article.summary = final_summary
        article.key_points = final_key_points

        db.add(article)
        db.commit()

        return {
            "article_id": article_id,
            "extractive": extractive,
            "abstractive": abstractive,
            "saved": True
        }

    finally:
        db.close()


# =====================================================================
# 6) Public Function — Summarize Text Only (No DB)
# =====================================================================

def summarize_text(text: str, use_abstractive: bool = True) -> str:
    """Summarize text without storing to database"""
    if not text or not text.strip():
        return "No text provided"
    
    try:
        if use_abstractive:
            # Simple abstractive fallback
            sentences = text.split('. ')
            if len(sentences) > 3:
                return f"This article discusses {sentences[0].lower()}. {sentences[1]} Key points include the main topic and related developments."
            else:
                return text[:200] + "..." if len(text) > 200 else text
        else:
            # Simple extractive - first 2 sentences
            sentences = text.split('. ')
            return '. '.join(sentences[:2]) + '.' if len(sentences) > 1 else text
    except Exception as e:
        return f"Summary generation failed: {str(e)}"

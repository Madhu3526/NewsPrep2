import os
from typing import List, Dict

from langchain_community.vectorstores import FAISS

# ---- text splitter (new + old LC support) ----
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter

# ---- Document class (new + old LC support) ----
try:
    from langchain_core.documents import Document
except ImportError:
    from langchain.docstore.document import Document

from langchain_community.llms import Ollama
from langchain_community.embeddings import HuggingFaceEmbeddings

from backend.app.db.session import SessionLocal
from backend.app.db.models.article import Article


# -------------------------
# GLOBAL MODELS & MEMORY
# -------------------------

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

llm = Ollama(model="llama3.1")

faiss_index = None
chat_history = []


# -------------------------
# BUILD VECTORSTORE
# -------------------------

def build_vectorstore():
    global faiss_index

    db = SessionLocal()
    articles = db.query(Article).all()
    db.close()

    docs: List[Document] = []
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)

    for art in articles:
        text = art.summary or art.text or ""
        if not text.strip():
            continue

        chunks = splitter.split_text(text)
        for ch in chunks:
            docs.append(
                Document(
                    page_content=ch,
                    metadata={
                        "article_id": art.id,
                        "title": art.title,
                        "published": art.published_date.isoformat()
                        if art.published_date else None
                    }
                )
            )

    faiss_index = FAISS.from_documents(docs, embeddings)

    print(f"✅ FAISS vector store created with {len(docs)} chunks")


# -------------------------
# RAG QUESTION ANSWERING
# -------------------------

def ask_question(query: str):
    global faiss_index, chat_history

    if faiss_index is None:
        build_vectorstore()

    retriever = faiss_index.as_retriever(search_kwargs={"k": 3})

    # ------------------------------
    # Version-safe document retrieval
    # ------------------------------
    try:
        docs = retriever.invoke(query)           # new LC (>=0.2)
    except Exception:
        docs = retriever._get_relevant_documents(query)  # old LC fallback

    # ------------------------------
    # Build context
    # ------------------------------
    context = "\n\n".join(
        f"Source {i+1}: {d.page_content}"
        for i, d in enumerate(docs)
    )

    # ------------------------------
    # RAG Prompt
    # ------------------------------
    prompt = f"""
You are an AI news assistant. Use ONLY the context below to answer the user's question.

CONTEXT:
{context}

CHAT HISTORY:
{chat_history}

QUESTION:
{query}

Give a factual answer. If the answer is not in the context, say: "Information not found in the news corpus."
"""

    llm_response = llm.invoke(prompt).strip()

    # update chat history
    chat_history.append({"user": query, "assistant": llm_response})

    # ------------------------------
    # Build source list
    # ------------------------------
    sources = []
    for d in docs:
        sources.append({
            "article_id": d.metadata.get("article_id"),
            "title": d.metadata.get("title"),
            "snippet": d.page_content[:200] + "...",
            "published": d.metadata.get("published")
        })

    return {
        "answer": llm_response,
        "sources": sources,
        "history": chat_history
    }

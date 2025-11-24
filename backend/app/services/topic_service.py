# backend/app/services/topic_service.py
import os
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import math

# Optional heavy dependencies — import safely so server can start without them
try:
    from bertopic import BERTopic
except Exception:
    BERTopic = None

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None

# Singleton holder to avoid reloading multiple times
_SERVICE_SINGLETON = None


class TopicService:
    def __init__(self, model_path, articles_csv, embedder_name="all-MiniLM-L6-v2"):
        self.model_path = model_path
        self.articles_csv = articles_csv
        print("Loading articles from", articles_csv)

        self.df = pd.read_csv(articles_csv)

        # Ensure id column exists
        if "id" not in self.df.columns:
            self.df = self.df.reset_index().rename(columns={"index": "id"})

        self.topic_info = None
        self.topic_model = None
        self._load_model()

        # Embeddings
        self.embedder_name = embedder_name
        self.embedder = None

        base = os.path.dirname(articles_csv)
        self.emb_path = os.path.join(base, "embeddings.npy")
        self.id_path = os.path.join(base, "article_ids.npy")

        self._embeddings = None
        self._article_ids = None

        if os.path.exists(self.emb_path) and os.path.exists(self.id_path):
            print("Loading precomputed embeddings:", self.emb_path)
            self._embeddings = np.load(self.emb_path)
            self._article_ids = np.load(self.id_path)
        else:
            print("No precomputed embeddings found (semantic search limited).")

    # Clean floats for JSON
    def _clean_float(self, v):
        if v is None or isinstance(v, str):
            return 0.0
        if isinstance(v, (np.floating, float)):
            if math.isnan(v) or math.isinf(v):
                return 0.0
            return float(v)
        return 0.0

    def _load_model(self):
        try:
            if BERTopic is None:
                print("bertopic not installed; topic model features disabled.")
                self.topic_model = None
                return

            if os.path.exists(self.model_path):
                print("Loading BERTopic model from", self.model_path)
                self.topic_model = BERTopic.load(self.model_path)
                try:
                    info = self.topic_model.get_topic_info()
                    info = info.rename(columns={"Name": "Name", "Representation": "Representation"})
                    self.topic_info = info.to_dict(orient="records")
                except Exception:
                    self.topic_info = []
            else:
                print("Model path not found:", self.model_path)
        except Exception as e:
            print("Failed to load BERTopic model:", e)
            self.topic_model = None

    # PUBLIC API =====================================================

    def get_topic_info(self, topic_id: int = None):
        if topic_id is None:
            if self.topic_model:
                info = self.topic_model.get_topic_info()
                result = []
                for _, row in info.iterrows():
                    rep = row["Representation"] if "Representation" in row else []
                    name = row.get("Name") or " | ".join(rep[:4])
                    result.append({
                        "Topic": int(row["Topic"]),
                        "Count": int(row["Count"]),
                        "Name": name,
                        "Representation": rep,
                    })
                return result

            # Fallback grouping
            groups = self.df["bertopic_topic"].value_counts().to_dict()
            return [
                {"Topic": int(k), "Count": int(v), "Name": str(k), "Representation": []}
                for k, v in groups.items()
            ]

        # Specific topic details
        if self.topic_model:
            info = self.topic_model.get_topic_info()
            trow = info[info.Topic == int(topic_id)]
            if trow.empty:
                return None

            row = trow.iloc[0]
            rep = row["Representation"] if "Representation" in row else []
            return {
                "Topic": int(row["Topic"]),
                "Count": int(row["Count"]),
                "Name": row.get("Name") or " | ".join(rep[:4]),
                "Representation": rep,
            }

        return None

    def get_representative_docs(self, topic_id: int, top_n: int = 10):
        try:
            reps = self.topic_model.get_representative_docs(topic_id, n_documents=top_n)
            docs = [{"title": None, "text": r} for r in reps] if isinstance(reps, list) else []
        except Exception:
            docs = []

        dfsel = self.df[self.df["bertopic_topic"] == int(topic_id)].head(top_n)

        ret = []
        for _, r in dfsel.iterrows():
            ret.append({
                "id": int(r["id"]),
                "title": r.get("title"),
                "text": r.get("text"),
                "source": r.get("source"),
                "url": r.get("url") if "url" in r else None,
                "published": r.get("published") if "published" in r else None,
            })

        return ret or docs

    # ===============================================================

    def keyword_search(self, q: str, top_k: int = 10):
        ql = str(q).lower()

        df = self.df
        df["__score_kw"] = (
            df["title"].fillna("").str.lower().str.contains(ql).astype(int) * 2
            + df["text"].fillna("").str.lower().str.contains(ql).astype(int)
        )

        res = df[df["__score_kw"] > 0].sort_values("__score_kw", ascending=False).head(top_k)

        out = []
        for _, r in res.iterrows():
            out.append({
                "id": int(r["id"]),
                "title": r.get("title"),
                "text": r.get("text"),
                "topic": int(r.get("bertopic_topic")) if "bertopic_topic" in r else None,
                "source": r.get("source"),
                "url": r.get("url") if "url" in r else None,
            })

        try:
            df.drop(columns="__score_kw", inplace=True)
        except Exception:
            pass

        return out

    # ===============================================================

    def has_embeddings(self):
        return self._embeddings is not None

    def _ensure_embedder(self):
        if self.embedder is None:
            if SentenceTransformer is None:
                raise RuntimeError("SentenceTransformer is not installed; semantic search is unavailable.")
            print("Loading embedder:", self.embedder_name)
            self.embedder = SentenceTransformer(self.embedder_name)

    # ===============================================================
    # FIXED SEMANTIC SEARCH
    # ===============================================================
    def semantic_search(self, query: str, top_k: int = 10):

        def clean(v):
            return self._clean_float(v)

        # No precomputed embeddings
        if not self.has_embeddings():
            self._ensure_embedder()
            texts = self.df["text"].astype(str).tolist()

            emb = self.embedder.encode(texts, convert_to_numpy=True)
            sims = cosine_similarity(self.embedder.encode([query]), emb)[0]

            idx = sims.argsort()[::-1][:top_k]
            out = []

            for i in idx:
                r = self.df.iloc[i]
                out.append({
                    "id": int(r["id"]),
                    "title": r.get("title"),
                    "text": r.get("text"),
                    "score": clean(sims[i]),
                })

            return out

        # With precomputed embeddings
        self._ensure_embedder()
        q_emb = self.embedder.encode([query], convert_to_numpy=True)

        sims = cosine_similarity(q_emb, self._embeddings)[0]
        idx = sims.argsort()[::-1][:top_k]

        out = []
        for i in idx:
            aid = int(self._article_ids[i])
            row = self.df[self.df["id"] == aid].iloc[0]

            out.append({
                "id": aid,
                "title": row.get("title"),
                "text": (row.get("text") or "")[:600],
                "score": clean(sims[i]),
            })

        return out

    # ===============================================================

    def recommend_by_article(self, article_id: int, top_k: int = 5):

        def clean(v):
            return self._clean_float(v)

        if not self.has_embeddings():
            raise RuntimeError("Embeddings not available.")

        if article_id not in self._article_ids:
            raise RuntimeError("Article id not found in embeddings.")

        i = int(np.where(self._article_ids == article_id)[0][0])
        q_emb = self._embeddings[i:i + 1]

        sims = cosine_similarity(q_emb, self._embeddings)[0]
        idx = sims.argsort()[::-1]

        results = []
        for j in idx[1:top_k+1]:
            aid = int(self._article_ids[j])
            r = self.df[self.df["id"] == aid].iloc[0]

            results.append({
                "id": aid,
                "title": r.get("title"),
                "text": r.get("text"),
                "score": clean(sims[j]),
            })

        return results


# ===============================================================

def get_topic_service(model_path, articles_csv):
    global _SERVICE_SINGLETON
    if _SERVICE_SINGLETON is None:
        _SERVICE_SINGLETON = TopicService(model_path=model_path, articles_csv=articles_csv)
    return _SERVICE_SINGLETON

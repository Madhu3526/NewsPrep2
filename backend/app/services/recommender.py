import os
import numpy as np
from typing import List, Tuple, Optional

from backend.app.db.session import SessionLocal
from backend.app.db.models.article import Article


class RecommenderService:
    """Simple in-memory content-based recommender using precomputed embeddings.

    Expects two files under ML data dir:
      - embeddings.npy : (N, D) float32
      - article_ids.npy : (N,) ints matching DB article.id
    """

    def __init__(self, embeddings_path: Optional[str] = None, ids_path: Optional[str] = None):
        # sensible defaults relative to repo
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ml", "data", "topic_corpus"))
        self.embeddings_path = embeddings_path or os.path.join(base, "embeddings.npy")
        self.ids_path = ids_path or os.path.join(base, "article_ids.npy")

        self._loaded = False
        self.embeddings = None
        self.ids = None
        self.id_to_idx = {}

    def load(self):
        if self._loaded:
            return
        if not os.path.exists(self.embeddings_path) or not os.path.exists(self.ids_path):
            raise FileNotFoundError("Embeddings or ids file not found. Run precompute_embeddings.py first.")

        self.embeddings = np.load(self.embeddings_path)
        self.ids = np.load(self.ids_path)

        # normalize embeddings for cosine similarity
        norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self.embeddings = self.embeddings / norms

        for idx, aid in enumerate(self.ids):
            self.id_to_idx[int(aid)] = idx

        self._loaded = True

    def _ensure(self):
        if not self._loaded:
            self.load()

    def similar_by_article(self, article_id: int, top_n: int = 10, exclude_self: bool = True) -> List[Tuple[int, float]]:
        """Return list of (article_id, score) sorted desc."""
        self._ensure()
        if int(article_id) not in self.id_to_idx:
            return []
        idx = self.id_to_idx[int(article_id)]
        vec = self.embeddings[idx: idx + 1]  # (1, D)
        sims = np.dot(self.embeddings, vec.T).squeeze()
        # sims is length N
        ids = self.ids.copy()

        # build pairs
        pairs = list(zip(ids.tolist(), sims.tolist()))
        # optionally filter self
        if exclude_self:
            pairs = [p for p in pairs if int(p[0]) != int(article_id)]
        pairs.sort(key=lambda x: x[1], reverse=True)
        return [(int(a), float(s)) for a, s in pairs[:top_n]]

    def similar_by_embedding(self, embedding: np.ndarray, top_n: int = 10) -> List[Tuple[int, float]]:
        self._ensure()
        # normalize embedding
        e = embedding.astype(float)
        denom = np.linalg.norm(e)
        if denom == 0:
            return []
        e = e / denom
        sims = np.dot(self.embeddings, e)
        pairs = list(zip(self.ids.tolist(), sims.tolist()))
        pairs.sort(key=lambda x: x[1], reverse=True)
        return [(int(a), float(s)) for a, s in pairs[:top_n]]

    def similar_by_topic(self, topic_id: int, top_n: int = 10) -> List[Tuple[int, float]]:
        """Compute centroid of embeddings for articles with given topic_id and find nearest neighbors."""
        self._ensure()
        db = SessionLocal()
        try:
            q = db.query(Article).filter(Article.topic_id == int(topic_id)).all()
            ids = [r.id for r in q if r.id in self.id_to_idx]
            if not ids:
                return []
            vecs = [self.embeddings[self.id_to_idx[int(i)]] for i in ids]
            centroid = np.mean(np.stack(vecs, axis=0), axis=0)
            return self.similar_by_embedding(centroid, top_n=top_n)
        finally:
            db.close()

    def get_article_meta(self, article_ids: List[int]) -> List[dict]:
        db = SessionLocal()
        try:
            res = []
            for aid in article_ids:
                a = db.query(Article).get(int(aid))
                if not a:
                    continue
                excerpt = (a.text or "")[:350]
                res.append({
                    "id": a.id,
                    "title": a.title,
                    "excerpt": excerpt,
                    "topic_id": a.topic_id
                })
            return res
        finally:
            db.close()


# singleton
_recommender = None

def get_recommender() -> RecommenderService:
    global _recommender
    if _recommender is None:
        _recommender = RecommenderService()
    return _recommender

# backend/app/ml/precompute_embeddings.py
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
import os

MODEL = "all-MiniLM-L6-v2"  # fast and small
OUT_DIR = r"backend\app\ml\data\topic_corpus"
CSV = os.path.join(OUT_DIR, "ag_bbc_india_with_topics.csv")

df = pd.read_csv(CSV)
if "id" not in df.columns:
    df = df.reset_index().rename(columns={"index":"id"})
texts = df["text"].astype(str).tolist()
embedder = SentenceTransformer(MODEL)
embs = embedder.encode(texts, show_progress_bar=True, convert_to_numpy=True, batch_size=64)
np.save(os.path.join(OUT_DIR, "embeddings.npy"), embs)
np.save(os.path.join(OUT_DIR, "article_ids.npy"), df["id"].to_numpy())
print("Saved embeddings to", OUT_DIR)

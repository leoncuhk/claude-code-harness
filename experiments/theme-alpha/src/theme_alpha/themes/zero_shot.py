"""Zero-shot theme attention (primary H1 input): count news docs per concept per week by embedding
similarity between each document and the concept's text (name + description), using ONLY concepts
that exist at the document's week (PIT). Mirrors BERTrend's 'targeted zero-shot monitoring'
(paper: similarity threshold 0.4-0.6 for expert-defined topics)."""
from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd

EmbedFn = Callable[[list[str]], np.ndarray]  # returns L2-normalised vectors, shape (n, d)


def sentence_transformer_embedder(model_name: str = "BAAI/bge-m3") -> EmbedFn:
    from sentence_transformers import SentenceTransformer  # optional dependency [nlp]
    m = SentenceTransformer(model_name)
    return lambda texts: m.encode(texts, normalize_embeddings=True, batch_size=64, show_progress_bar=False)


def theme_doc_counts(news: pd.DataFrame, concepts: pd.DataFrame, embed: EmbedFn,
                     threshold: float = 0.5, week_freq: str = "W-FRI") -> pd.DataFrame:
    """news: doc_id, published_at, title, text.  concepts: concept_id, name, description, created_at.
    Returns long table week, concept_id, n_docs (one doc may count for several concepts)."""
    news = news.copy()
    news["week"] = pd.to_datetime(news["published_at"]).dt.to_period(week_freq).dt.end_time.dt.normalize()
    ctext = (concepts["name"].fillna("") + "：" + concepts.get("description", "").fillna("")).tolist()
    C = embed(ctext)
    created = pd.to_datetime(concepts["created_at"]).to_numpy()
    rows = []
    for wk, g in news.groupby("week"):
        D = embed((g["title"].fillna("") + "。" + g["text"].fillna("").str[:512]).tolist())
        sim = D @ C.T
        alive = created <= np.datetime64(wk)
        hits = (sim >= threshold) & alive[None, :]
        n = hits.sum(axis=0)
        for k in np.flatnonzero(alive):
            rows.append((wk, concepts["concept_id"].iloc[k], int(n[k])))
    return pd.DataFrame(rows, columns=["week", "concept_id", "n_docs"])

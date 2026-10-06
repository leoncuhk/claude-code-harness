"""Bridge to the BERTrend package for EXPLORATORY new-theme discovery (E1), not for gated tests.

BERTrend (pip `bertrend`, rte-france) requires a recent Python (>=3.13 per its README) and heavy deps,
so run it in an isolated env and exchange files:

  1. export_corpus(news, out_dir)         -> parquet slices: doc_id, timestamp, text
  2. (separate venv) run BERTrend weak-signal pipeline on the slices, export per-slice topic table:
        topic_id, slice_end, n_docs, representation (top words), is_new
  3. import_topics(path)                  -> long table week, topic_id, n_docs, representation

E1 metric ('lead time'): for each concept created after the corpus start, find the earliest BERTrend
topic whose representation embeds within cosine >= 0.5 of the concept text AND was classified weak;
lead_time = concept.created_at - first_weak_week. Report distribution; positive median = BERTrend sees
themes before the concept board exists. Never feed LLM-generated interpretations into signals.
"""
from __future__ import annotations

import os

import pandas as pd


def export_corpus(news: pd.DataFrame, out_dir: str, freq: str = "W-FRI") -> None:
    os.makedirs(out_dir, exist_ok=True)
    n = news.rename(columns={"published_at": "timestamp"})[["doc_id", "timestamp", "text"]]
    n["slice"] = pd.to_datetime(n["timestamp"]).dt.to_period(freq).astype(str)
    for s, g in n.groupby("slice"):
        g.drop(columns="slice").to_parquet(f"{out_dir}/slice_{s.replace('/', '_')}.parquet", index=False)


def import_topics(path: str) -> pd.DataFrame:
    df = pd.read_parquet(path)
    need = {"topic_id", "slice_end", "n_docs", "representation"}
    missing = need - set(df.columns)
    if missing:
        raise ValueError(f"BERTrend export missing columns: {missing}")
    return df.rename(columns={"slice_end": "week"})

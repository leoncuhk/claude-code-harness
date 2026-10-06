"""BERTrend-style popularity and signal classification, implemented natively.

The BERTrend paper (Boutaleb et al., FuturED@ACL 2024) defines:
  * popularity: increments by #docs when a topic receives documents; otherwise decays
    p_t = p_{t-1} * exp(-lambda * dt^2), dt = days since last update  -> `classic_popularity`
  * classification over a sliding window of pooled popularity values (all topics):
      p < P10                      -> noise
      P10 <= p <= P50 and slope>0  -> weak signal
      P10 <= p <= P50 and slope<=0 -> noise
      p > P50                      -> strong signal
For finance we pre-register an EWM variant (`ewm_popularity`) because cumulative counts let old,
large topics stay 'strong' forever. Both variants share `classify_states`.

Input `counts`: DataFrame index=week, columns=concept_id, values=#docs; NaN where the concept did
not exist yet (PIT: a concept must not have attention before it exists).
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

NOISE, WEAK, STRONG = 0, 1, 2


def counts_matrix(theme_docs: pd.DataFrame, weeks: pd.DatetimeIndex, concept_ids: list) -> pd.DataFrame:
    c = theme_docs.pivot_table(index="week", columns="concept_id", values="n_docs", aggfunc="sum")
    return c.reindex(index=weeks, columns=concept_ids)  # NaN = concept not alive / no record


def ewm_popularity(counts: pd.DataFrame, half_life_weeks: float = 8.0) -> pd.DataFrame:
    decay = np.exp(-np.log(2) / half_life_weeks)
    C = counts.to_numpy(dtype=float)
    out = np.full_like(C, np.nan)
    prev = np.zeros(C.shape[1])
    for t in range(C.shape[0]):
        alive = ~np.isnan(C[t])
        cur = prev * decay + np.nan_to_num(C[t])
        out[t] = np.where(alive, cur, np.nan)
        prev = np.where(alive, cur, 0.0)
    return pd.DataFrame(out, index=counts.index, columns=counts.columns)


def classic_popularity(counts: pd.DataFrame, lam: float = 0.01, slice_days: int = 7) -> pd.DataFrame:
    C = counts.to_numpy(dtype=float)
    out = np.full_like(C, np.nan)
    prev = np.zeros(C.shape[1])
    since = np.zeros(C.shape[1])
    for t in range(C.shape[0]):
        alive = ~np.isnan(C[t])
        n = np.nan_to_num(C[t])
        upd = n > 0
        since = np.where(upd, 0, since + slice_days)
        cur = np.where(upd, prev + n, prev * np.exp(-lam * since ** 2))
        out[t] = np.where(alive, cur, np.nan)
        prev = np.where(alive, cur, 0.0)
    return pd.DataFrame(out, index=counts.index, columns=counts.columns)


def _rolling_slope(P: np.ndarray, t: int, w: int) -> np.ndarray:
    lo = max(0, t - w + 1)
    Y = P[lo:t + 1]
    if Y.shape[0] < 3:
        return np.full(P.shape[1], np.nan)
    x = np.arange(Y.shape[0], dtype=float)
    x -= x.mean()
    with np.errstate(invalid="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        Yc = Y - np.nanmean(Y, axis=0)
    return np.nansum(x[:, None] * Yc, axis=0) / (x ** 2).sum()


def classify_states(pop: pd.DataFrame, window_weeks: int = 26, slope_window_weeks: int = 6) -> pd.DataFrame:
    """Return states (0 noise / 1 weak / 2 strong; NaN where concept not alive). Uses data <= t only."""
    P = pop.to_numpy(dtype=float)
    S = np.full_like(P, np.nan)
    for t in range(P.shape[0]):
        pooled = P[max(0, t - window_weeks + 1):t + 1].ravel()
        pooled = pooled[~np.isnan(pooled)]
        if pooled.size < 20:
            continue
        p10, p50 = np.percentile(pooled, [10, 50])
        slope = _rolling_slope(P, t, slope_window_weeks)
        p = P[t]
        s = np.where(p > p50, STRONG, np.where((p >= p10) & (slope > 0), WEAK, NOISE)).astype(float)
        S[t] = np.where(np.isnan(p), np.nan, s)
    return pd.DataFrame(S, index=pop.index, columns=pop.columns)


def detect_transitions(states: pd.DataFrame, cooldown_weeks: int = 26) -> pd.DataFrame:
    """Events: weak at t-1 -> strong at t, and not strong anywhere in the previous `cooldown_weeks`."""
    S = states.to_numpy()
    rows = []
    for t in range(1, S.shape[0]):
        hit = (S[t - 1] == WEAK) & (S[t] == STRONG)
        for k in np.flatnonzero(hit):
            past = S[max(0, t - cooldown_weeks):t - 1, k]
            if not np.any(past == STRONG):
                rows.append((states.index[t], states.columns[k]))
    return pd.DataFrame(rows, columns=["week", "concept_id"])


def attention_share(counts: pd.DataFrame) -> pd.DataFrame:
    """Share of all concept-tagged documents in week t (Bybee-Kelly style 'attention')."""
    tot = counts.sum(axis=1, skipna=True).replace(0, np.nan)
    return counts.div(tot, axis=0)

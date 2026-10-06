"""Crowding x implied expectations (H4). Ben-David et al. (RFS 2023): specialised ETFs launch after
run-ups in over-valued themes; we flag themes where an ETF launched recently AND the basket's implied
growth (reverse DCF, PIT) sits at the top of its own history."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..data.pit import MembershipIndex


def etf_launch_counts(etf_launches: pd.DataFrame, weeks: pd.DatetimeIndex, concept_ids: list,
                      window_weeks: int = 26) -> pd.DataFrame:
    out = pd.DataFrame(0.0, index=weeks, columns=concept_ids)
    w = weeks.to_numpy()
    for _, r in etf_launches.iterrows():
        if r["concept_id"] not in out.columns:
            continue
        lo = np.searchsorted(w, np.datetime64(r["list_date"]), side="left")
        hi = np.searchsorted(w, np.datetime64(r["list_date"] + pd.Timedelta(weeks=window_weeks)), side="left")
        out.iloc[lo:hi, out.columns.get_loc(r["concept_id"])] += 1
    return out


def basket_implied_growth(implied_growth: pd.DataFrame, mi: MembershipIndex) -> pd.DataFrame:
    G = implied_growth.to_numpy()
    out = np.full((G.shape[0], len(mi.concept_ids)), np.nan)
    for p, t in enumerate(implied_growth.index):
        for k, cid in enumerate(mi.concept_ids):
            mem = mi.members(cid, t)
            if mem.size >= 5:
                out[p, k] = np.nanmedian(G[p, mem])
    return pd.DataFrame(out, index=implied_growth.index, columns=mi.concept_ids)


def expanding_percentile(df: pd.DataFrame, min_periods: int = 52) -> pd.DataFrame:
    """Percentile of value at t within the concept's own history up to and including t."""
    X = df.to_numpy()
    out = np.full_like(X, np.nan)
    for k in range(X.shape[1]):
        col = X[:, k]
        for t in range(X.shape[0]):
            hist = col[:t + 1]
            hist = hist[~np.isnan(hist)]
            if hist.size >= min_periods and not np.isnan(col[t]):
                out[t, k] = (hist <= col[t]).mean()
    return pd.DataFrame(out, index=df.index, columns=df.columns)


def crowd_flags(etf_counts: pd.DataFrame, ig_pct: pd.DataFrame, etf_min: int = 1,
                ig_pct_min: float = 0.8) -> pd.DataFrame:
    return (etf_counts >= etf_min) & (ig_pct >= ig_pct_min)

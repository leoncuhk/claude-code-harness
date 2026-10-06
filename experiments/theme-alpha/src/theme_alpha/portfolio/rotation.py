"""Theme rotation overlay with a tracking-error budget (THRO-style architecture, long-only).

total_t = bench_t + alpha * (theme_t - bench_t) - cost_t,   alpha in [0, 1]
alpha is reset at each rebalance to hit `te_target_annual` using trailing active volatility (PIT).
With alpha <= 1 the portfolio is a blend of the benchmark and long-only theme baskets -> long-only.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def rotation_returns(basket_ret: pd.DataFrame, bench: pd.Series, eligible: pd.DataFrame,
                     lookback: int, top_k: int, rebalance_every: int = 4,
                     exclude: pd.DataFrame | None = None, te_target_annual: float = 0.04,
                     te_window: int = 52, cost_rt: float = 0.003) -> pd.DataFrame:
    T = len(basket_ret)
    B = basket_ret.to_numpy()
    b = bench.to_numpy()
    ex = basket_ret.sub(bench, axis=0)
    score = ex.rolling(lookback, min_periods=lookback).sum().to_numpy()
    elig = eligible.reindex_like(basket_ret).fillna(False).to_numpy(dtype=bool)
    excl = exclude.reindex_like(basket_ret).fillna(False).to_numpy(dtype=bool) if exclude is not None else None
    te_w = te_target_annual / np.sqrt(52)

    theme = np.full(T, np.nan)
    alpha_arr = np.zeros(T)
    cost = np.zeros(T)
    sel: np.ndarray | None = None
    alpha = 0.5
    for p in range(T):
        if sel is not None and sel.size:
            x = B[p, sel]
            if np.any(~np.isnan(x)):
                theme[p] = np.nanmean(x)
        alpha_arr[p] = alpha if sel is not None else 0.0
        if p >= lookback and (p - lookback) % rebalance_every == 0 and p + 1 < T:
            s = score[p].copy()
            s[~elig[p]] = np.nan
            if excl is not None:
                s[excl[p]] = np.nan
            ok = np.flatnonzero(~np.isnan(s))
            new = ok[np.argsort(-s[ok])[:top_k]] if ok.size else np.empty(0, dtype=int)
            hist = (theme - b)[max(0, p - te_window + 1):p + 1]
            hist = hist[~np.isnan(hist)]
            if hist.size >= 26 and hist.std(ddof=1) > 0:
                alpha = float(np.clip(te_w / hist.std(ddof=1), 0.0, 1.0))
            turnover = 1.0 if sel is None or sel.size == 0 else 1 - len(set(new) & set(sel)) / max(1, top_k)
            cost[p + 1] += alpha * turnover * cost_rt
            sel = new
    active = np.where(np.isnan(theme), 0.0, alpha_arr * (theme - b))
    out = pd.DataFrame({"theme": theme, "alpha": alpha_arr, "cost": cost}, index=basket_ret.index)
    out["active_net"] = active - cost
    out["total"] = b + out["active_net"]
    return out

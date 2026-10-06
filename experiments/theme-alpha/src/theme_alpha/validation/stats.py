"""Inference utilities. Default significance hurdle t >= 3.0 for NEW signals (Harvey-Liu-Zhu 2016);
t >= 2.0 is acceptable only when replicating a published effect (H2)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

HLZ_T = 3.0


def nw_tstat(x, lags: int | None = None) -> tuple[float, float]:
    """Mean and Newey-West t-stat of a series (overlapping-horizon safe)."""
    x = pd.Series(x).dropna().to_numpy(dtype=float)
    if x.size < 10:
        return float("nan"), float("nan")
    if lags is None:
        lags = int(np.floor(4 * (x.size / 100) ** (2 / 9)))
    res = sm.OLS(x, np.ones_like(x)).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return float(res.params[0]), float(res.tvalues[0])


def fama_macbeth(panel: pd.DataFrame, y: str, xs: list[str], time_col: str = "week",
                 min_obs: int = 30, nw_lags: int = 4) -> pd.DataFrame:
    """Cross-sectional OLS each period, then NW t-stats of the coefficient time series."""
    coefs = []
    for t, g in panel.groupby(time_col):
        g = g.dropna(subset=[y] + xs)
        if len(g) < min_obs:
            continue
        X = sm.add_constant(g[xs].to_numpy(dtype=float), has_constant="add")
        b = np.linalg.lstsq(X, g[y].to_numpy(dtype=float), rcond=None)[0]
        coefs.append([t] + list(b))
    C = pd.DataFrame(coefs, columns=[time_col, "const"] + xs).set_index(time_col)
    rows = []
    for c in C.columns:
        m, tt = nw_tstat(C[c], lags=nw_lags)
        rows.append((c, m, tt, len(C)))
    return pd.DataFrame(rows, columns=["var", "coef", "t", "n_periods"]).set_index("var")


def ann_ir(weekly: pd.Series) -> float:
    w = pd.Series(weekly).dropna()
    return float(w.mean() / w.std(ddof=1) * np.sqrt(52)) if w.std(ddof=1) > 0 else float("nan")


def max_drawdown(weekly_returns: pd.Series) -> float:
    w = pd.Series(weekly_returns).fillna(0.0)
    eq = (1 + w).cumprod()
    return float((1 - eq / eq.cummax()).max())


def block_bootstrap_mean(x, block: int = 8, n_boot: int = 2000, seed: int = 0) -> tuple[float, float]:
    """Return (bootstrap std error of mean, one-sided p-value for mean <= 0)."""
    x = pd.Series(x).dropna().to_numpy(dtype=float)
    rng = np.random.default_rng(seed)
    n = x.size
    n_blocks = int(np.ceil(n / block))
    means = np.empty(n_boot)
    for b in range(n_boot):
        starts = rng.integers(0, max(1, n - block + 1), n_blocks)
        idx = (starts[:, None] + np.arange(block)[None, :]).ravel()[:n]
        means[b] = x[idx].mean()
    se = means.std(ddof=1)
    centered = means - means.mean()
    p = float((centered >= x.mean()).mean())
    return float(se), p

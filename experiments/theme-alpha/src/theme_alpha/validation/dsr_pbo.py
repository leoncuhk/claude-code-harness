"""Deflated Sharpe Ratio (Bailey & Lopez de Prado 2014) and Probability of Backtest Overfitting
via CSCV (Bailey, Borwein, Lopez de Prado, Zhu 2017)."""
from __future__ import annotations

from itertools import combinations

import numpy as np
from scipy.stats import kurtosis, norm, skew

EULER = 0.5772156649


def deflated_sharpe(returns: np.ndarray, trial_sharpes: np.ndarray) -> float:
    """Probability that the true (per-period) Sharpe > the max expected under N independent trials.
    trial_sharpes: per-period Sharpe ratios of ALL configurations tried (incl. this one)."""
    r = np.asarray(returns, dtype=float)
    r = r[~np.isnan(r)]
    T = r.size
    sr = r.mean() / r.std(ddof=1)
    N = max(2, len(trial_sharpes))
    var_sr = np.var(trial_sharpes, ddof=1) if len(trial_sharpes) > 1 else 0.0
    sr0 = np.sqrt(var_sr) * ((1 - EULER) * norm.ppf(1 - 1 / N) + EULER * norm.ppf(1 - 1 / (N * np.e)))
    g3, g4 = skew(r), kurtosis(r, fisher=False)
    denom = np.sqrt(max(1e-12, 1 - g3 * sr + (g4 - 1) / 4 * sr ** 2))
    return float(norm.cdf((sr - sr0) * np.sqrt(T - 1) / denom))


def pbo_cscv(M: np.ndarray, n_blocks: int = 10) -> float:
    """M: T x S matrix of per-period returns for S configurations. Returns PBO in [0,1]."""
    M = np.nan_to_num(np.asarray(M, dtype=float))
    T, S = M.shape
    blocks = np.array_split(np.arange(T), n_blocks)
    logits = []
    for is_b in combinations(range(n_blocks), n_blocks // 2):
        is_idx = np.concatenate([blocks[b] for b in is_b])
        oos_idx = np.concatenate([blocks[b] for b in range(n_blocks) if b not in is_b])
        sr_is = M[is_idx].mean(0) / (M[is_idx].std(0, ddof=1) + 1e-12)
        sr_oos = M[oos_idx].mean(0) / (M[oos_idx].std(0, ddof=1) + 1e-12)
        best = int(np.argmax(sr_is))
        rank = (sr_oos <= sr_oos[best]).sum() / (S + 1)
        rank = min(max(rank, 1e-6), 1 - 1e-6)
        logits.append(np.log(rank / (1 - rank)))
    return float((np.array(logits) <= 0).mean())

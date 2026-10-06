"""Combinatorial Purged Cross-Validation (Lopez de Prado, AFML ch.12) for SELECTION processes.

For rule-based strategies there is nothing to 'fit' except the choice among a parameter grid, so
each split selects the best config on the train groups and records its returns on the test groups.
Paths are then recombined -> a distribution of out-of-sample outcomes instead of one backtest.
If the user's AFML framework is available, replace `cpcv_splits` with it (same contract);
`skfolio.model_selection.CombinatorialPurgedCV` is an alternative implementation.
"""
from __future__ import annotations

from itertools import combinations
from math import comb

import numpy as np
import pandas as pd


def cpcv_splits(T: int, n_groups: int = 10, k_test: int = 2, purge: int = 4, embargo: int = 4):
    bounds = np.linspace(0, T, n_groups + 1).astype(int)
    groups = [np.arange(bounds[i], bounds[i + 1]) for i in range(n_groups)]
    splits = []
    for test_g in combinations(range(n_groups), k_test):
        test_idx = np.concatenate([groups[g] for g in test_g])
        banned = np.zeros(T, dtype=bool)
        for g in test_g:
            lo, hi = bounds[g], bounds[g + 1]
            banned[max(0, lo - purge):min(T, hi + embargo)] = True
        train_idx = np.flatnonzero(~banned)
        splits.append((train_idx, test_g, groups))
    return splits


def _sharpe(x: np.ndarray) -> float:
    x = x[~np.isnan(x)]
    return float(x.mean() / x.std(ddof=1)) if x.size > 5 and x.std(ddof=1) > 0 else -np.inf


def selection_cpcv_paths(returns_by_config: pd.DataFrame, n_groups: int = 10, k_test: int = 2,
                         purge: int = 4, embargo: int = 4, score=_sharpe) -> pd.DataFrame:
    """returns_by_config: index=week, columns=config_id (weekly returns of each config).
    Returns DataFrame index=week, columns=path_0..path_{phi-1}: OOS returns of the config SELECTED
    on train data for the split that tested that week's group."""
    R = returns_by_config.to_numpy()
    T = R.shape[0]
    n_paths = comb(n_groups - 1, k_test - 1)
    paths = np.full((T, n_paths), np.nan)
    used = np.zeros(n_groups, dtype=int)
    for train_idx, test_g, groups in cpcv_splits(T, n_groups, k_test, purge, embargo):
        best = int(np.argmax([score(R[train_idx, c]) for c in range(R.shape[1])]))
        for g in test_g:
            paths[groups[g], used[g]] = R[groups[g], best]
            used[g] += 1
    return pd.DataFrame(paths, index=returns_by_config.index,
                        columns=[f"path_{i}" for i in range(n_paths)])

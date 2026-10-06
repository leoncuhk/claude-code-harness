"""Fixed per-case diagnostics. The loop compares these numbers iteration over iteration.

Price-path landmarks (breakout, peak) use hindsight and are for EVALUATION ONLY: they define what a
signal should have caught; no signal may read them."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..themes.attention import STRONG, WEAK, classify_states, ewm_popularity


def cum_excess(ret: pd.DataFrame, bench: pd.Series, tickers: list) -> pd.Series:
    cols = [t for t in tickers if t in ret.columns]
    ex = ret[cols].mean(axis=1, skipna=True) - bench
    return ex.fillna(0.0).cumsum()


def landmarks(ce: pd.Series, breakout: float = 0.20) -> dict:
    w = ce.index
    bo = int(np.argmax(ce.to_numpy() - np.minimum.accumulate(ce.to_numpy()) >= breakout)) \
        if np.any(ce.to_numpy() - np.minimum.accumulate(ce.to_numpy()) >= breakout) else None
    pk = int(np.argmax(ce.to_numpy()))
    after = ce.iloc[pk:]
    return {"breakout_week": w[bo] if bo is not None else None, "peak_week": w[pk],
            "rise_to_peak": float(ce.iloc[pk] - ce.iloc[:pk + 1].min()),
            "drawdown_after_peak": float(ce.iloc[pk] - after.min())}


def attention_events(att: pd.Series, half_life: float = 8, window: int = 26, slope_w: int = 6) -> pd.Series:
    """Single-theme version: popularity is compared with the theme's OWN trailing distribution
    (no cross-section of themes inside one case)."""
    pop = ewm_popularity(att.to_frame("x"), half_life)["x"]
    P = pop.to_numpy()
    st = np.full(P.size, np.nan)
    for t in range(P.size):
        hist = P[max(0, t - window + 1):t + 1]
        hist = hist[~np.isnan(hist)]
        if hist.size < 8 or np.isnan(P[t]):
            continue
        p10, p50 = np.percentile(hist, [10, 50])
        y = hist[-slope_w:]
        slope = np.polyfit(np.arange(y.size), y, 1)[0] if y.size >= 3 else 0.0
        st[t] = STRONG if P[t] > p50 and slope > 0 else (WEAK if P[t] >= p10 and slope > 0 else 0)
    return pd.Series(st, index=att.index)


def first_transition(states: pd.Series):
    s = states.to_numpy()
    for t in range(1, s.size):
        if s[t - 1] == WEAK and s[t] == STRONG:
            return states.index[t]
    return None


def weeks_between(a, b):
    if a is None or b is None:
        return None
    return int(round((pd.Timestamp(b) - pd.Timestamp(a)).days / 7))


def exit_value(ce: pd.Series, flag_week, horizon_weeks: int | None = None) -> float | None:
    """Value of exiting at the first flag = minus the excess return earned after the flag
    (to window end or +horizon). Positive = the exit helped."""
    if flag_week is None:
        return None
    i = ce.index.get_loc(flag_week)
    j = len(ce) - 1 if horizon_weeks is None else min(len(ce) - 1, i + horizon_weeks)
    return float(-(ce.iloc[j] - ce.iloc[i]))


def tsmom_capture(ex: pd.Series, lookback: int = 4) -> dict:
    """Hold the core basket only when its trailing excess > 0 (signal at t, hold t+1)."""
    sig = ex.rolling(lookback).sum().shift(1) > 0
    strat = ex.where(sig, 0.0)
    bh = ex.sum()
    return {"capture_ratio": float(strat.sum() / bh) if abs(bh) > 1e-9 else None,
            "strategy_excess": float(strat.sum()), "buy_hold_excess": float(bh)}


def lead_lag(core_ex: pd.Series, so_ex: pd.Series, max_lag: int = 4) -> dict:
    out = {}
    for L in range(0, max_lag + 1):
        out[L] = float(core_ex.corr(so_ex.shift(-L)))
    best = max(out, key=lambda k: out[k] if not np.isnan(out[k]) else -9)
    return {"xcorr_by_lag": out, "best_lag": best, "lag1_minus_lag0": out.get(1, np.nan) - out.get(0, np.nan)}

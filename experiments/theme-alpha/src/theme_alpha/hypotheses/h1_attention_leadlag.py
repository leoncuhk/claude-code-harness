"""H1  Attention lead-lag.
H1: a BERTrend weak->strong transition of a concept's attention at week t predicts positive excess
    return of that concept's basket over t+1..t+H.
H0: mean CAR after transitions = mean CAR at placebo dates of the same concepts (<= 0 excess).
Design: event study, CARs clustered by event week (NW t), placebo draws from the same concepts."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..data.bundle import DataBundle
from ..data.pit import MembershipIndex, basket_returns
from ..themes.attention import classic_popularity, classify_states, counts_matrix, detect_transitions, ewm_popularity
from ..validation.stats import nw_tstat
from .common import HypothesisResult, evaluate_gates, window


def run(b: DataBundle, cfg: dict, start=None, end=None, split="custom") -> HypothesisResult:
    p_ = cfg["params"]
    H = p_["horizon_weeks"]
    mi = MembershipIndex(b.membership, b.concepts, b.stock_ids)
    basket = basket_returns(b.stock_ret, mi, p_["min_members"])
    ex = basket.sub(b.bench_ret, axis=0)
    counts = counts_matrix(b.theme_docs, b.weeks, mi.concept_ids)
    pop = ewm_popularity(counts, p_["half_life_weeks"]) if p_["popularity"] == "ewm" else classic_popularity(counts)
    states = classify_states(pop, p_["window_weeks"], p_["slope_window_weeks"])
    events = detect_transitions(states, p_["cooldown_weeks"])

    X = ex.to_numpy()
    T, K = X.shape
    valid = ~np.isnan(X)
    cum = np.vstack([np.zeros(K), np.cumsum(np.nan_to_num(X), axis=0)])   # cum[p] = sum X[:p]
    cnt = np.vstack([np.zeros(K), np.cumsum(valid, axis=0)])
    P = np.arange(T)
    ok_h = P + H < T
    car = np.full((T, K), np.nan)
    car[ok_h] = cum[P[ok_h] + 1 + H] - cum[P[ok_h] + 1]               # weeks p+1 .. p+H
    n_obs = np.zeros((T, K))
    n_obs[ok_h] = cnt[P[ok_h] + 1 + H] - cnt[P[ok_h] + 1]
    car[n_obs < 0.8 * H] = np.nan

    inwin = window(b.weeks, start, end)
    pos = {w: i for i, w in enumerate(b.weeks)}
    kpos = {c: i for i, c in enumerate(mi.concept_ids)}
    ev = [(pos[w], kpos[c]) for w, c in zip(events["week"], events["concept_id"])]
    ev = [(p, k) for p, k in ev if inwin[p] and not np.isnan(car[p, k])]
    notes = []
    if len(ev) < 20:
        notes.append(f"only {len(ev)} usable events")
    ev_car = np.array([car[p, k] for p, k in ev]) if ev else np.array([])
    by_week = pd.Series(ev_car, index=[b.weeks[p] for p, _ in ev]).groupby(level=0).mean().sort_index()
    mean_car, t = nw_tstat(by_week, lags=H) if len(by_week) >= 10 else (float("nan"), float("nan"))

    # placebo: same concepts, random weeks away from their real events
    rng = np.random.default_rng(cfg.get("seed", 0))
    cand = {}
    for k in set(k for _, k in ev):
        ep = np.array([p for p, kk in ev if kk == k])
        c = np.flatnonzero(inwin & ~np.isnan(car[:, k]))
        c = c[np.min(np.abs(c[:, None] - ep[None, :]), axis=1) > H]
        cand[k] = c
    n_by_k = pd.Series([k for _, k in ev]).value_counts().to_dict() if ev else {}
    reps = []
    for _ in range(p_["n_placebo"]):
        draws = [car[rng.choice(cand[k], n), k] for k, n in n_by_k.items() if cand[k].size]
        if draws:
            reps.append(np.concatenate(draws).mean())
    placebo_p = float((np.array(reps) >= ev_car.mean()).mean()) if reps and ev_car.size else float("nan")

    metrics = {
        "n_events": len(ev),
        "car_mean": float(ev_car.mean()) if ev_car.size else float("nan"),
        "car_nw_mean_by_week": mean_car,
        "t_stat": t,
        "placebo_p": placebo_p,
        "net_car_mean": float(ev_car.mean() - cfg["costs"]["round_trip"]) if ev_car.size else float("nan"),
        "hit_rate": float((ev_car > 0).mean()) if ev_car.size else float("nan"),
    }
    checks = evaluate_gates(metrics, cfg["gates"])
    return HypothesisResult("H1", split, b.meta.get("source", "?"), metrics, checks, all(checks.values()), notes)

"""H3  Low-visibility spillover.
H1: stocks linked to a theme via news co-mention but NOT in its concept board earn next-week excess
returns proportional to the theme basket's excess return this week (slow diffusion to second-order
beneficiaries; Hoberg-Phillips JFQA 2018, PKU JBF 2025).
Test: weekly Fama-MacBeth  y_{i,t+1} ~ s_{i,t} + own r_{i,t} + own 12w momentum  (NW t >= 3),
plus decile long-short net of measured turnover costs."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..data.bundle import DataBundle
from ..data.pit import MembershipIndex, basket_returns
from ..themes.linkage import ThemeLinks
from ..validation.stats import fama_macbeth, nw_tstat
from .common import HypothesisResult, evaluate_gates, window


def run(b: DataBundle, cfg: dict, start=None, end=None, split="custom") -> HypothesisResult:
    p_ = cfg["params"]
    cost_rt = cfg["costs"]["round_trip"]
    mi = MembershipIndex(b.membership, b.concepts, b.stock_ids)
    basket = basket_returns(b.stock_ret, mi, p_["min_members"])
    ex = basket.sub(b.bench_ret, axis=0)
    links = ThemeLinks(b.comention, p_["link_window_weeks"])
    R, bench = b.stock_ret.to_numpy(), b.bench_ret.to_numpy()
    spos = {s: i for i, s in enumerate(b.stock_ids)}
    inwin = window(b.weeks, start, end)
    rows, ls_g, ls_n = [], [], []
    prev_top = prev_bot = None
    for p in range(max(13, p_["link_window_weeks"]), len(b.weeks) - 1):
        if not inwin[p + 1]:
            continue
        t = b.weeks[p]
        W = links.weights_at(t, mi)
        if W.empty:
            continue
        exk = ex.iloc[p]
        W = W.assign(x=W["concept_id"].map(exk)).dropna(subset=["x"])
        s = (W["w"] * W["x"]).groupby(W["stock_id"]).sum()
        if len(s) < p_["min_linked"]:
            continue
        idx = s.index.map(spos).to_numpy()
        y = R[p + 1, idx] - bench[p + 1]
        own = R[p, idx]
        mom = np.nansum(R[p - 12:p, idx], axis=0)
        df = pd.DataFrame({"week": t, "s": s.to_numpy(), "own_r": own, "own_mom": mom, "y": y}).dropna()
        rows.append(df)
        n = len(df)
        q = max(1, n // 10)
        o = df.sort_values("s")
        sid = s.index.to_numpy()
        top_ids, bot_ids = set(sid[o.index[-q:]]), set(sid[o.index[:q]])
        gross = o["y"].iloc[-q:].mean() - o["y"].iloc[:q].mean()
        tt = 1.0 if prev_top is None else 1 - len(top_ids & prev_top) / q
        tb = 1.0 if prev_bot is None else 1 - len(bot_ids & prev_bot) / q
        prev_top, prev_bot = top_ids, bot_ids
        ls_g.append((t, gross))
        ls_n.append((t, gross - (tt + tb) * cost_rt))
    panel = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    fm = fama_macbeth(panel, "y", ["s", "own_r", "own_mom"], min_obs=p_["min_linked"], nw_lags=2) \
        if not panel.empty else pd.DataFrame()
    g = pd.Series(dict(ls_g)); n_ = pd.Series(dict(ls_n))
    ls_m, ls_t = nw_tstat(g, lags=2) if len(g) > 10 else (float("nan"), float("nan"))
    metrics = {
        "n_weeks": int(len(g)),
        "avg_linked": float(panel.groupby("week").size().mean()) if not panel.empty else 0.0,
        "fm_s_coef": float(fm.loc["s", "coef"]) if "s" in fm.index else float("nan"),
        "fm_s_t": float(fm.loc["s", "t"]) if "s" in fm.index else float("nan"),
        "ls_gross_mean": ls_m, "ls_t": ls_t,
        "ls_net_mean": float(n_.mean()) if len(n_) else float("nan"),
    }
    checks = evaluate_gates(metrics, cfg["gates"])
    return HypothesisResult("H3", split, b.meta.get("source", "?"), metrics, checks, all(checks.values()))

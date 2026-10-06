"""H2  Concept momentum after publication.
Replication of 'Concept links and return momentum' (JBF 2022) on PIT concept baskets, split at the
publication date. H1: post-publication long-short concept momentum is still positive (t >= 2,
replication hurdle) and the implementable long-only leg has net IR >= 0.3; and it is not subsumed by
stock-level momentum (Fama-MacBeth). Decay ratio is reported (McLean-Pontiff style)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..data.bundle import DataBundle
from ..data.pit import MembershipIndex, alive_mask, basket_returns
from ..validation.stats import ann_ir, fama_macbeth, nw_tstat
from .common import HypothesisResult, evaluate_gates, window


def run(b: DataBundle, cfg: dict, start=None, end=None, split="custom") -> HypothesisResult:
    p_ = cfg["params"]
    J, Kh = p_["formation_weeks"], p_["holding_weeks"]
    cost_rt = cfg["costs"]["round_trip"]
    mi = MembershipIndex(b.membership, b.concepts, b.stock_ids)
    basket = basket_returns(b.stock_ret, mi, p_["min_members"])
    ex = basket.sub(b.bench_ret, axis=0)
    alive = alive_mask(b.weeks, mi, min_age_weeks=J + 1)  # formation window must be post-creation
    T = len(b.weeks)
    Bm, R, bench = basket.to_numpy(), b.stock_ret.to_numpy(), b.bench_ret.to_numpy()
    ls, lo, lo_net = (np.full(T, np.nan) for _ in range(3))
    fm_rows, prev_top = [], None
    for p in range(J, T - Kh, Kh):
        s = ex.iloc[p - J + 1:p + 1].sum(min_count=J).to_numpy().copy()
        s[~alive.iloc[p].to_numpy()] = np.nan
        ok = np.flatnonzero(~np.isnan(s))
        if ok.size < 10:
            continue
        q = max(1, ok.size // 5)
        order = ok[np.argsort(s[ok])]
        bot, top = order[:q], order[-q:]
        turn = 1.0 if prev_top is None else 1 - len(set(top) & set(prev_top)) / q
        prev_top = top
        for h in range(1, Kh + 1):
            w = p + h
            ls[w] = np.nanmean(Bm[w, top]) - np.nanmean(Bm[w, bot])
            lo[w] = np.nanmean(Bm[w, top]) - bench[w]
            lo_net[w] = lo[w] - (turn * cost_rt if h == 1 else 0.0)
        # stock-level Fama-MacBeth: does concept momentum survive own momentum?
        t = b.weeks[p]
        cm = {}
        for k in ok:
            for i in mi.members(mi.concept_ids[k], t):
                cm.setdefault(i, []).append(s[k])
        fut = np.nansum(R[p + 1:p + 1 + Kh], axis=0) - bench[p + 1:p + 1 + Kh].sum()
        own = np.nansum(R[p - J + 1:p + 1], axis=0)
        for i, vals in cm.items():
            fm_rows.append((t, np.mean(vals), own[i], fut[i]))

    weeks = b.weeks
    inwin = window(weeks, start, end)
    pub = pd.Timestamp(p_["publication_date"])
    pre, post = inwin & (weeks < pub), inwin & (weeks >= pub)
    s_ls, s_lo_net = pd.Series(ls, index=weeks), pd.Series(lo_net, index=weeks)
    pre_m, pre_t = nw_tstat(s_ls[pre], lags=Kh)
    post_m, post_t = nw_tstat(s_ls[post], lags=Kh)
    fm = pd.DataFrame(fm_rows, columns=["week", "concept_mom", "own_mom", "fut"])
    fm = fm[fm["week"] >= pub] if p_.get("fm_post_only", True) else fm
    fm = fm[inwin[np.searchsorted(weeks, fm["week"])]]
    fmres = fama_macbeth(fm, "fut", ["concept_mom", "own_mom"], min_obs=30, nw_lags=1)
    metrics = {
        "pre_mean": pre_m, "pre_t": pre_t, "post_mean": post_m, "post_t": post_t,
        "decay_ratio": float(1 - post_m / pre_m) if pre_m and pre_m > 0 else float("nan"),
        "post_ir_net": ann_ir(s_lo_net[post]),
        "fm_concept_t": float(fmres.loc["concept_mom", "t"]) if "concept_mom" in fmres.index else float("nan"),
        "fm_own_t": float(fmres.loc["own_mom", "t"]) if "own_mom" in fmres.index else float("nan"),
    }
    checks = evaluate_gates(metrics, cfg["gates"])
    return HypothesisResult("H2", split, b.meta.get("source", "?"), metrics, checks, all(checks.values()))

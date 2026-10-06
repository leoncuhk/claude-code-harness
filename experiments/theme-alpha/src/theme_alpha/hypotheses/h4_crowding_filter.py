"""H4  Crowding x implied-expectations filter.
H1: excluding themes with (recent ETF launch) AND (basket implied growth >= 80th pct of own history)
from a momentum theme-rotation overlay reduces RELATIVE drawdown without materially hurting IR.
Test: selection-CPCV over a small parameter grid for both arms (base vs filtered), paired by path;
robustness across all grid configs on the full window. PBO and DSR are reported for the strategy gate."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..data.bundle import DataBundle
from ..data.pit import MembershipIndex, alive_mask, basket_returns
from ..portfolio.rotation import rotation_returns
from ..signals.crowding import basket_implied_growth, crowd_flags, etf_launch_counts, expanding_percentile
from ..validation.cpcv import selection_cpcv_paths
from ..validation.dsr_pbo import deflated_sharpe, pbo_cscv
from ..validation.stats import ann_ir, max_drawdown
from .common import HypothesisResult, evaluate_gates, window


def run(b: DataBundle, cfg: dict, start=None, end=None, split="custom") -> HypothesisResult:
    p_ = cfg["params"]
    mi = MembershipIndex(b.membership, b.concepts, b.stock_ids)
    basket = basket_returns(b.stock_ret, mi, p_["min_members"])
    alive = alive_mask(b.weeks, mi, min_age_weeks=p_["min_age_weeks"])
    etf = etf_launch_counts(b.etf_launches, b.weeks, mi.concept_ids, p_["etf_window_weeks"])
    ig_pct = expanding_percentile(basket_implied_growth(b.implied_growth, mi), p_["ig_min_history_weeks"])
    flags = crowd_flags(etf, ig_pct, p_["etf_min"], p_["ig_pct_min"])
    inwin = window(b.weeks, start, end)

    base, filt = {}, {}
    for L in p_["grid"]["lookback_weeks"]:
        for k in p_["grid"]["top_k"]:
            kw = dict(lookback=L, top_k=k, rebalance_every=p_["rebalance_weeks"],
                      te_target_annual=p_["te_target_annual"], cost_rt=cfg["costs"]["round_trip"])
            cid = f"L{L}_k{k}"
            base[cid] = rotation_returns(basket, b.bench_ret, alive, **kw)["active_net"]
            filt[cid] = rotation_returns(basket, b.bench_ret, alive, exclude=flags, **kw)["active_net"]
    Bm = pd.DataFrame(base)[inwin]
    Fm = pd.DataFrame(filt)[inwin]

    cv = p_["cpcv"]
    pb = selection_cpcv_paths(Bm, cv["n_groups"], cv["k_test"], cv["purge"], cv["embargo"])
    pf = selection_cpcv_paths(Fm, cv["n_groups"], cv["k_test"], cv["purge"], cv["embargo"])
    mdd_b = np.array([max_drawdown(pb[c]) for c in pb])
    mdd_f = np.array([max_drawdown(pf[c]) for c in pf])
    red = 1 - mdd_f / np.where(mdd_b > 0, mdd_b, np.nan)
    ir_diff = np.array([ann_ir(pf[c]) - ann_ir(pb[c]) for c in pf])

    cfg_red = np.array([1 - max_drawdown(Fm[c]) / max(1e-9, max_drawdown(Bm[c])) for c in Bm])
    best = max(Fm.columns, key=lambda c: ann_ir(Fm[c]))
    trial_sr = np.array([s.mean() / s.std(ddof=1) for s in Fm.T.values])  # family searched for the final strategy
    metrics = {
        "n_paths": int(pb.shape[1]),
        "mdd_red_median": float(np.nanmedian(red)),
        "mdd_red_frac_paths": float(np.nanmean(red > 0)),
        "ir_diff_median": float(np.nanmedian(ir_diff)),
        "configs_improved_frac": float(np.mean(cfg_red >= 0.10)),
        "n_flag_weeks": int(flags[inwin].to_numpy().sum()),
        "pbo_filtered": pbo_cscv(Fm.to_numpy(), cv["pbo_blocks"]),
        "dsr_filtered_best": deflated_sharpe(Fm[best].to_numpy(), trial_sr),
        "ir_filtered_best": ann_ir(Fm[best]),
    }
    checks = evaluate_gates(metrics, cfg["gates"])
    return HypothesisResult("H4", split, b.meta.get("source", "?"), metrics, checks, all(checks.values()))

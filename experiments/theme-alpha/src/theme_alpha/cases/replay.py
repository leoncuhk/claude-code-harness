"""Replay one case week by week with point-in-time signals, then score it with fixed diagnostics."""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from .diagnostics import (attention_events, cum_excess, exit_value, first_transition, landmarks, lead_lag,
                          tsmom_capture, weeks_between)
from .spec import CaseData


def _own_history_pct(x: pd.Series, min_hist: int) -> pd.Series:
    v = x.to_numpy()
    out = np.full(v.size, np.nan)
    for t in range(v.size):
        h = v[:t + 1]
        h = h[~np.isnan(h)]
        if h.size >= min_hist and not np.isnan(v[t]):
            out[t] = (h <= v[t]).mean()
    return pd.Series(out, index=x.index)


def crowd_flags(d: CaseData, mech: dict) -> pd.DataFrame:
    w = d.ret.index
    core = [t for t in d.core if t in d.implied_growth.columns]
    ig_core = d.implied_growth[core].median(axis=1, skipna=True) if core else pd.Series(np.nan, index=w)
    if mech["crowd_percentile_basis"] == "own_history":
        ig_pct = _own_history_pct(ig_core, mech["crowd_min_history_weeks"])
    else:  # peer_cross_section: core median vs all tickers in the case universe at the same week
        allv = d.implied_growth
        ig_pct = pd.Series([(allv.loc[t].dropna() <= ig_core.loc[t]).mean() if allv.loc[t].notna().sum() >= 5
                            else np.nan for t in w], index=w)
    etf = pd.Series(0, index=w)
    for dt in d.etf_launch_dates:
        etf[(w >= pd.Timestamp(dt)) & (w < pd.Timestamp(dt) + pd.Timedelta(weeks=26))] += 1
    flag = (etf >= 1) & (ig_pct >= mech.get("ig_pct_min", 0.8))
    confirm = pd.Series(True, index=w)
    if mech.get("confirm_with_revisions"):
        confirm = revision_confirmation(d.meta.get("revenue_ttm_core"), w, core)
    supply = pd.Series(False, index=w)
    if mech.get("use_supply_events") and len(d.supply_events):
        for _, e in d.supply_events.iterrows():
            if e["size_frac"] >= 0.2:  # scheduled events (lockups, IPOs) are known in advance -> PIT-legal
                supply[(w < pd.Timestamp(e["date"])) & (w >= pd.Timestamp(e["date"]) - pd.Timedelta(weeks=8))] = True
        flag = flag | (supply & (ig_pct >= mech.get("ig_pct_min", 0.8)))
    flag = flag & confirm
    return pd.DataFrame({"etf_26w": etf, "ig_core": ig_core, "ig_pct": ig_pct, "supply": supply,
                         "confirm": confirm, "flag": flag})


def revision_confirmation(rev: pd.DataFrame | None, weeks: pd.DatetimeIndex, core: list, lag: int = 13) -> pd.Series:
    """PROXY for 'estimate revisions turn negative' (no consensus feed): confirm crowding only when the
    core-median growth of REPORTED TTM revenue (as announced, ffilled from ann_date) is decelerating,
    g_t = rev_t / rev_{t-lag} - 1 and g_t < g_{t-lag}. Weeks without enough history -> not confirmed."""
    if rev is None or rev.empty:
        return pd.Series(False, index=weeks)
    r = rev.reindex(weeks)[[c for c in core if c in rev.columns]]
    g = r / r.shift(lag) - 1.0
    med = g.median(axis=1, skipna=True)
    return (med < med.shift(lag)).fillna(False)


ATTENTION_FALLBACK = ("news_count", "wiki_views", "turnover")


def pick_attention(att: pd.DataFrame, requested: str) -> str | None:
    """Requested source if this case has it (>= 8 non-zero weeks), else the first available fallback."""
    for s in (requested, *ATTENTION_FALLBACK):
        if s in att.columns and (att[s].fillna(0) > 0).sum() >= 8:
            return s
    return None


def replay(d: CaseData, cfg: dict, start=None, end=None) -> dict:
    fz, mech = cfg["frozen"], cfg["mechanisms"]
    R = d.ret.loc[start:end]
    B = d.bench.loc[start:end]
    dd = CaseData(R, B, d.core, d.second_order, d.attention.loc[start:end], d.etf_launch_dates,
                  d.supply_events, d.implied_growth.loc[start:end], d.meta)
    ce = cum_excess(R, B, d.core)
    core_ex = ce.diff().fillna(ce.iloc[0])
    so = [t for t in d.second_order if t in R.columns]
    so_ex = (R[so].mean(axis=1, skipna=True) - B) if so else pd.Series(np.nan, index=R.index)
    lm = landmarks(ce, fz["breakout_threshold"])

    # H1 attention lead
    src = mech["attention_source"]
    used = pick_attention(dd.attention, src)
    ev = None
    if used is not None:
        states = attention_events(dd.attention[used], mech["attention_half_life_weeks"])
        ev = first_transition(states)
    car13 = None
    if ev is not None:
        i = ce.index.get_loc(ev)
        j = min(len(ce) - 1, i + 13)
        car13 = float(ce.iloc[j] - ce.iloc[i])

    # H3 spillover: does second-order follow the core with a lag?
    h3 = {"n_second_order": len(so)}
    if so and so_ex.notna().sum() > 20:
        h3.update(lead_lag(core_ex, so_ex))
        y = so_ex.shift(-1).dropna()
        x = core_ex.loc[y.index]
        res = sm.OLS(y.to_numpy(), sm.add_constant(x.to_numpy())).fit(cov_type="HAC", cov_kwds={"maxlags": 2})
        h3["next_week_beta"], h3["next_week_t"] = float(res.params[1]), float(res.tvalues[1])

    # H4 crowding flag timing and value
    cf = crowd_flags(dd, mech)
    fw = cf.index[cf["flag"].to_numpy()].min() if cf["flag"].any() else None
    cov = float(dd.implied_growth[[t for t in d.core if t in dd.implied_growth.columns]].notna().mean().mean()) \
        if len(d.core) else 0.0
    return {
        "landmarks": {k: (str(v.date()) if isinstance(v, pd.Timestamp) else v) for k, v in lm.items()},
        "H1": {"attention_source": src, "attention_source_used": used, "first_weak_to_strong": str(ev.date()) if ev is not None else None,
               "lead_weeks_vs_breakout": weeks_between(ev, lm["breakout_week"]),
               "car13_after_event": car13},
        "H2": tsmom_capture(core_ex, 4),
        "H3": h3,
        "H4": {"first_flag": str(fw.date()) if fw is not None else None,
               "flag_lead_weeks_vs_peak": weeks_between(fw, lm["peak_week"]),
               "exit_value_to_end": exit_value(ce, fw),
               "exit_value_26w": exit_value(ce, fw, fz["exit_eval_horizon_weeks"]),
               "flag_weeks": int(cf["flag"].sum()),
               "implied_growth_coverage_core": cov,
               "blocked_by_missing_expectations": bool(cov < 0.3)},
    }


def case_from_bundle(b, concept_id: str, start, end, n_second: int = 15) -> CaseData:
    """Synthetic case for offline testing of the loop harness."""
    from ..data.pit import MembershipIndex
    from ..themes.linkage import ThemeLinks
    mi = MembershipIndex(b.membership, b.concepts, b.stock_ids)
    core = [b.stock_ids[p] for p in mi.members(concept_id, pd.Timestamp(start))]
    W = ThemeLinks(b.comention, 52).weights_at(pd.Timestamp(start), mi)
    so = (W[W["concept_id"] == concept_id].sort_values("w", ascending=False)["stock_id"].head(n_second).tolist())
    td = b.theme_docs[b.theme_docs["concept_id"] == concept_id].set_index("week")["n_docs"]
    att = pd.DataFrame({"news_count": td}).reindex(b.weeks)
    etf = b.etf_launches.loc[b.etf_launches["concept_id"] == concept_id, "list_date"].tolist()
    tick = core + so
    return CaseData(b.stock_ret[tick], b.bench_ret, core, so, att, etf,
                    pd.DataFrame(columns=["date", "kind", "size_frac"]), b.implied_growth[tick],
                    {"source": "synthetic", "concept_id": concept_id})

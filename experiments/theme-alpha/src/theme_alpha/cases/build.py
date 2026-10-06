"""Build a point-in-time weekly CaseData panel from the free web sources (scripts/fetch_case_data.py).

PIT rules implemented here (each is also listed in meta.json["pit_notes"]):
  * prices: weekly close = last trading day of the W-FRI week; return NaN before listing.
  * fundamentals: as-of join on ann_date. A-share/US use the vendor NOTICE_DATE when it is within the
    statutory deadline, else report_date + deadline + buffer (the vendor re-stamps old periods with the
    date of the latest filing that repeats them). HK has no notice date -> statutory deadline.
  * ETF launches: listing date = first traded day. An ETF mapped to the theme through its HOLDINGS is
    only counted from the day its first qualifying holdings report became public (quarter end + 25 d).
  * second-order universe: stocks in the latest PUBLIC top-10 holdings of a theme ETF, excluding core;
    their weekly return is NaN in weeks when they were not in that set (membership mask).
  * attention: wiki pageviews and turnover are stamped by the week they occur; GitHub stars by the
    day the star was given.
Nothing in cases/*.yaml `known_events` is read here."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from ..data.providers import web
from ..signals.expectations import SalesDrivenReverseDCF, TwoStageReverseDCF
from .spec import CaseSpec

FREQ = "W-FRI"
HOLDINGS_LAG_DAYS = 25          # quarterly report (top-10) due 15 working days after quarter end
# statutory filing deadline (days after period end) for vendor-date sanity checks / fallback
DEADLINE = {"US": {"Q": 45 + 5, "FY": 90 + 15}, "CN_A": {3: 31, 6: 62, 9: 31, 12: 120}}
MARGIN_CLIP = (-1.0, 0.6)       # sales-driven engine: current margin bounds (ASTS-type -900% margins)


# ---------------------------------------------------------------------------------- prices

def weekly_close(daily: pd.DataFrame, weeks: pd.DatetimeIndex) -> pd.Series:
    if daily.empty:
        return pd.Series(np.nan, index=weeks)
    s = daily.set_index("date")["close"].resample(FREQ).last()
    return s.reindex(weeks)


def weekly_dollar_volume(daily: pd.DataFrame, weeks: pd.DatetimeIndex) -> pd.Series:
    if daily.empty:
        return pd.Series(np.nan, index=weeks)
    d = daily.set_index("date")
    return (d["close"] * d["volume"]).resample(FREQ).sum(min_count=1).reindex(weeks)


def abnormal_turnover(dv: pd.DataFrame, base_weeks: int = 26, min_obs: int = 8) -> pd.Series:
    """Mean over tickers of dollar volume / its trailing median (strictly prior weeks)."""
    med = dv.shift(1).rolling(base_weeks, min_periods=min_obs).median()
    ratio = dv / med
    return ratio.mean(axis=1, skipna=True)


# ---------------------------------------------------------------------------------- fundamentals

def _fix_ann_dates(df: pd.DataFrame, market: str) -> tuple[pd.DataFrame, int]:
    """Replace vendor dates that are later than the statutory deadline (re-stamped comparatives)."""
    df = df.copy()
    lag = (df["ann_date"] - df["report_date"]).dt.days
    if market == "US":
        fy = df["report_date"].dt.month == 12
        dl = np.where(fy, DEADLINE["US"]["FY"], DEADLINE["US"]["Q"])
    else:
        dl = df["report_date"].dt.month.map(DEADLINE["CN_A"]).fillna(120).to_numpy()
    bad = (lag > dl) | df["ann_date"].isna()
    df.loc[bad, "ann_date"] = df.loc[bad, "report_date"] + pd.to_timedelta(dl[bad.to_numpy()], unit="D")
    return df, int(bad.sum())


def _ytd_to_ttm(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """TTM from cumulative (YTD) reports: YTD(P) + FY(prev) - YTD(P - 1y). FY rows are already TTM.
    If the comparable prior period is missing, annualise YTD x 12 / months (flagged in `ttm_method`)."""
    df = df.sort_values("report_date").reset_index(drop=True)
    by_date = df.set_index("report_date")
    out = df.copy()
    method = []
    for i, r in df.iterrows():
        P = r["report_date"]
        months = P.month if "period_start" not in r or pd.isna(r.get("period_start")) else \
            (P.year - r["period_start"].year) * 12 + P.month - r["period_start"].month + 1
        if P.month == 12 and months == 12:
            method.append("fy")
            continue
        prev_fy = pd.Timestamp(year=P.year - 1, month=12, day=31)
        prev_p = P - pd.DateOffset(years=1)
        if prev_fy in by_date.index and prev_p in by_date.index:
            for c in cols:
                out.at[i, c] = r[c] + by_date.at[prev_fy, c] - by_date.at[prev_p, c]
            method.append("ttm")
        else:
            for c in cols:
                out.at[i, c] = r[c] * 12.0 / max(months, 1)
            method.append("annualised")
    out["ttm_method"] = method
    return out


def _sum_last4(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    df = df.sort_values("report_date").reset_index(drop=True)
    out = df.copy()
    for c in cols:
        out[c] = df[c].rolling(4, min_periods=4).sum()
    out["ttm_method"] = "sum4q"
    return out


def fundamentals_ttm(ticker: str, market: str) -> tuple[pd.DataFrame, dict]:
    """PIT table: ann_date, revenue_ttm, margin, fcf_ttm, net_debt, shares."""
    note = {"ticker": ticker}
    if market == "US":
        raw = web.em_us_statements(ticker)
        if raw.empty:
            return raw, {**note, "status": "no_data"}
        raw, nfix = _fix_ann_dates(raw, "US")
        t = _sum_last4(raw.rename(columns={"revenue_q": "rev", "net_income_q": "prof", "ocf_q": "ocf",
                                           "capex_q": "capex"}), ["rev", "prof", "ocf", "capex"])
        t["shares"] = t["shares"].ffill()
        note["margin_basis"] = "net income / revenue (US feed has no operating income)"
    else:
        raw = web.em_cn_statements(ticker) if market == "CN_A" else web.em_hk_statements(ticker)
        if raw.empty:
            return raw, {**note, "status": "no_data"}
        nfix = 0
        if market == "CN_A":
            raw, nfix = _fix_ann_dates(raw, "CN_A")
        t = _ytd_to_ttm(raw.rename(columns={"revenue_ytd": "rev", "op_profit_ytd": "prof", "ocf_ytd": "ocf",
                                            "capex_ytd": "capex"}), ["rev", "prof", "ocf", "capex"])
        note["margin_basis"] = "operating profit / revenue"
    t = t.dropna(subset=["rev"])
    out = pd.DataFrame({
        "ann_date": t["ann_date"].to_numpy(), "report_date": t["report_date"].to_numpy(),
        "revenue_ttm": t["rev"].to_numpy(),
        "margin": (t["prof"] / t["rev"]).to_numpy(),
        "fcf_ttm": (t["ocf"] - t["capex"].abs().fillna(0.0)).to_numpy(),
        "net_debt": (t.get("debt", 0.0) - t.get("cash", 0.0)).fillna(0.0).to_numpy()
        if "cash" in t else np.zeros(len(t)),
        "shares": t["shares"].to_numpy(), "ttm_method": t["ttm_method"].to_numpy()})
    out = out.sort_values("ann_date").reset_index(drop=True)
    note.update({"status": "ok", "n_reports": int(len(out)), "vendor_dates_replaced": nfix,
                 "ttm_methods": out["ttm_method"].value_counts().to_dict()})
    return out, note


def implied_growth_panel(close: pd.DataFrame, fund: dict[str, pd.DataFrame], base: dict) -> tuple[dict, dict]:
    """Week x ticker implied growth for the three engines (fcf / sales / auto) + status counts."""
    e = base["expectations"]
    fcf_eng, sales_eng = TwoStageReverseDCF(), SalesDrivenReverseDCF()
    out = {k: pd.DataFrame(np.nan, index=close.index, columns=close.columns) for k in ("fcf", "sales", "auto")}
    status: dict[str, dict] = {}
    for tk in close.columns:
        f = fund.get(tk)
        st = {"fcf": {}, "sales": {}}
        if f is None or f.empty:
            status[tk] = {"no_fundamentals": int(close[tk].notna().sum())}
            continue
        ad = f["ann_date"].to_numpy()
        for w, px in close[tk].dropna().items():
            j = np.searchsorted(ad, np.datetime64(w), side="right") - 1
            if j < 0:
                st["fcf"]["no_report_yet"] = st["fcf"].get("no_report_yet", 0) + 1
                continue
            r = f.iloc[j]
            a = fcf_eng.implied(price=px, shares=r["shares"], net_debt=r["net_debt"], fcf_ttm=r["fcf_ttm"],
                                wacc=e["wacc"], terminal_g=e["terminal_g"], years=e["years"])
            m = float(np.clip(r["margin"], *MARGIN_CLIP)) if pd.notna(r["margin"]) else None
            b = sales_eng.implied(price=px, shares=r["shares"], net_debt=r["net_debt"], revenue_ttm=r["revenue_ttm"],
                                  current_margin=m)
            st["fcf"][a.status] = st["fcf"].get(a.status, 0) + 1
            st["sales"][b.status] = st["sales"].get(b.status, 0) + 1
            out["fcf"].at[w, tk] = a.implied_growth
            out["sales"].at[w, tk] = b.implied_growth
            out["auto"].at[w, tk] = a.implied_growth if a.status == "ok" else b.implied_growth
        status[tk] = st
    return out, status


# ---------------------------------------------------------------------------------- ETFs / holdings

def listing_date(ticker: str, search_from: str = "2010-01-01", end: str | None = None):
    """First traded day: first monthly bar, then the daily bars of that month (2 requests)."""
    end = end or datetime.now().strftime("%Y-%m-%d")
    for sym in web.tencent_symbol(ticker):
        body, _ = web._get("tencent", "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get",
                           {"param": f"{sym},month,{search_from},{end},800,qfq"})
        node = ((body or {}).get("data") or {}).get(sym)
        bars = (node.get("qfqmonth") or node.get("month") or []) if isinstance(node, dict) else []
        if not bars:
            continue
        m0 = pd.Timestamp(bars[0][0])
        d = web.tencent_daily_sym(sym, str((m0 - pd.offsets.MonthBegin(1)).date()), str((m0 + pd.Timedelta(days=7)).date()))
        if d.empty:  # stub symbol (monthly quote without daily history): try the next exchange suffix
            continue
        return d["date"].min(), sym
    return None, None


def holdings_membership(codes: list[str], years: list[int]) -> pd.DataFrame:
    rows = []
    for c in codes:
        h = web.em_fund_holdings(c, years)
        if not h.empty:
            h["etf"] = c
            rows.append(h)
    if not rows:
        return pd.DataFrame(columns=["quarter_end", "stock", "etf", "public_date"])
    h = pd.concat(rows)
    h["public_date"] = h["quarter_end"] + pd.Timedelta(days=HOLDINGS_LAG_DAYS)
    return h


def cn_listed_etf_rule(rule: dict, core: list[str], years: list[int], window_end: str) -> tuple[list, pd.DataFrame, list]:
    """A-share-listed ETFs: name rule -> theme from listing; holdings rule -> theme from first public
    report whose top-10 contains >= min_core core names. Returns (launch dates, holdings of theme ETFs, log)."""
    cat = web.em_fund_catalog()
    etf = cat[cat["name"].str.contains("ETF") & ~cat["name"].str.contains("联接") & cat["type"].str.startswith("指数")]
    exc = rule.get("name_exclude")
    by_name = etf[etf["name"].str.contains(rule.get("name_regex", "$^"))]
    if exc:
        by_name = by_name[~by_name["name"].str.contains(exc)]
    pool = etf[etf["name"].str.contains(rule.get("holdings_pool_regex", "$^"))]
    if exc:
        pool = pool[~pool["name"].str.contains(exc)]
    launches, log, theme_codes = [], [], []
    for _, r in by_name.iterrows():
        ld, sym = listing_date(r["code"] + (".SH" if r["code"].startswith("5") else ".SZ"), end=window_end)
        if ld is not None:
            launches.append(ld)
            theme_codes.append(r["code"])
            log.append({"etf": r["code"], "name": r["name"], "mapped_by": "name", "knowable": str(ld.date())})
    H = holdings_membership(pool["code"].tolist(), years)
    min_core = rule.get("holdings_min_core", 2)
    for code, g in H.groupby("etf"):
        if code in theme_codes:
            continue
        hits = g[g["stock"].isin(core)].groupby("quarter_end")["stock"].nunique()
        hits = hits[hits >= min_core]
        if hits.empty:
            continue
        knowable = hits.index.min() + pd.Timedelta(days=HOLDINGS_LAG_DAYS)
        ld, _ = listing_date(code + (".SH" if code.startswith("5") else ".SZ"), end=window_end)
        when = max(knowable, ld) if ld is not None else knowable
        launches.append(when)
        theme_codes.append(code)
        name = pool.loc[pool["code"] == code, "name"].iloc[0]
        log.append({"etf": code, "name": name, "mapped_by": f"holdings>={min_core} core",
                    "listed": str(ld.date()) if ld is not None else None, "knowable": str(when.date())})
    theme_h = holdings_membership(theme_codes, years)
    return launches, theme_h, log


def us_etf_rule(rule: dict, window_end: str) -> tuple[list, list]:
    import requests
    found = {}
    for q in rule["search_terms"]:
        r = requests.get("https://api.nasdaq.com/api/autocomplete/slookup/10", params={"search": q},
                         headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"}, timeout=30)
        for x in (r.json().get("data") or []):
            if x.get("asset") == "ETF" and pd.Series([x["name"]]).str.contains(rule["name_regex"], case=False).iloc[0] \
                    and not pd.Series([x["name"]]).str.contains(rule.get("name_exclude", "$^"), case=False).iloc[0]:
                found[x["symbol"]] = x["name"]
    for s in rule.get("always_include", []):
        found.setdefault(s, s)
    launches, log = [], []
    for s, name in sorted(found.items()):
        ld, sym = listing_date(s, end=window_end)
        log.append({"etf": s, "name": name, "listed": str(ld.date()) if ld is not None else None, "symbol": sym})
        if ld is not None:
            launches.append(ld)
    return launches, log


def membership_mask(h: pd.DataFrame, weeks: pd.DatetimeIndex, exclude: list[str]) -> pd.DataFrame:
    """week x stock: True if stock is in the latest PUBLIC top-10 of any theme ETF as of that week."""
    h = h[~h["stock"].isin(exclude)]
    stocks = sorted(h["stock"].unique())
    M = pd.DataFrame(False, index=weeks, columns=stocks)
    for etf, g in h.groupby("etf"):
        reports = sorted(g["public_date"].unique())
        for k, pdt in enumerate(reports):
            nxt = reports[k + 1] if k + 1 < len(reports) else pd.Timestamp.max
            names = g.loc[g["public_date"] == pdt, "stock"].unique()
            sel = (weeks >= pdt) & (weeks < nxt)
            M.loc[sel, [n for n in names if n in M.columns]] = True
    return M


# ---------------------------------------------------------------------------------- attention

def wiki_attention(articles: list[str], start, end, project: str = "en.wikipedia") -> tuple[pd.Series, dict]:
    tot, got = None, {}
    for a in articles:
        try:
            s = web.wiki_pageviews(a, start, end, project)
        except RuntimeError as ex:  # rate-limited after retries: recorded in meta, series left out
            got[a] = f"unavailable: {str(ex)[:60]}"
            continue
        got[a] = int(s.sum()) if len(s) else 0
        if len(s):
            tot = s if tot is None else tot.add(s, fill_value=0.0)
    if tot is None:
        return pd.Series(dtype=float), got
    return tot.resample(FREQ).sum(), got


def github_stars_weekly(repo: str, weeks: pd.DatetimeIndex) -> pd.Series:
    """New stars per week, PIT. OSSInsight samples the cumulative count sparsely (monthly), so between
    samples we carry the LAST KNOWN rate (S_k - S_{k-1}) / days * 7 forward; never interpolate toward a
    future sample."""
    s = web.ossinsight_stars(repo)
    if len(s) < 2:
        return pd.Series(np.nan, index=weeks)
    rate = (s.diff() / s.index.to_series().diff().dt.days * 7.0).dropna()
    return rate.reindex(weeks.union(rate.index)).ffill().reindex(weeks)


# ---------------------------------------------------------------------------------- main

def build_case(spec: CaseSpec, base: dict) -> tuple[dict, dict]:
    raw = spec.raw
    u = spec.universe
    start, end = pd.Timestamp(spec.window["start"]), pd.Timestamp(spec.window["end"])
    hist_start = start - pd.DateOffset(years=1)
    weeks = pd.date_range(hist_start, end, freq=FREQ)
    market = spec.market
    core = list(u["core"]) + list((u.get("late_listing") or {}).keys())
    pit_notes, sources = [], {}

    # ---- ETFs + second-order universe
    rule = raw.get("etf_rule", {})
    years = list(range(hist_start.year, end.year + 1))
    launches, etf_log, theme_h = [], [], pd.DataFrame()
    if market == "US":
        launches, etf_log = us_etf_rule(rule, str(end.date()))
        pit_notes.append("US ETF list from a Nasdaq name search run today: ETFs that closed before today are "
                         "missing (survivorship); listing dates are first traded days.")
    else:
        launches, theme_h, etf_log = cn_listed_etf_rule(rule, core, years, str(end.date()))
        pit_notes.append("ETF->theme mapping by name at listing, or by holdings from first public report.")
    second = []
    mask = None
    if not theme_h.empty:
        mask = membership_mask(theme_h, weeks, core)
        keep = mask.loc[start:end].sum()
        second = keep[keep >= rule.get("second_order_min_weeks", 4)].index.tolist()
        mask = mask[second]
        pit_notes.append("second_order = top-10 holdings of theme ETFs (latest public report), excl. core; "
                         "returns masked to NaN outside membership.")
    else:
        pit_notes.append("no PIT holdings source for this market -> second_order empty (H3 not evaluable).")

    # ---- prices
    tickers = core + second
    closes, dvol = {}, {}
    for tk in tickers:
        d = web.tencent_daily(tk, str(hist_start.date()), str(end.date()))
        closes[tk] = weekly_close(d, weeks)
        dvol[tk] = weekly_dollar_volume(d, weeks)
        sources[tk] = d.attrs.get("symbol")
    close = pd.DataFrame(closes)
    ret = close.pct_change(fill_method=None)
    if mask is not None:
        ret[second] = ret[second].where(mask.reindex(ret.index).fillna(False).astype(bool))
    bd = web.tencent_daily(u["benchmark"], str(hist_start.date()), str(end.date()))
    bench = weekly_close(bd, weeks).pct_change(fill_method=None).rename("bench")
    sources["benchmark"] = bd.attrs.get("symbol")

    # ---- fundamentals -> implied growth. MVP: core only (second-order IG would only feed the
    # peer_cross_section knob; documented in docs/case_data.md)
    fund, fnotes = {}, []
    for tk in core:
        try:
            f, n = fundamentals_ttm(tk, market if not tk.endswith(".HK") else "HK")
        except Exception as ex:  # vendor gaps are recorded, never silently filled
            f, n = pd.DataFrame(), {"ticker": tk, "status": f"error: {ex!r}"[:200]}
        fund[tk] = f
        fnotes.append(n)
    ig, ig_status = implied_growth_panel(close[core], fund, base)

    # ---- attention
    att = pd.DataFrame(index=weeks)
    att["turnover"] = abnormal_turnover(pd.DataFrame(dvol)[core])
    wiki = raw.get("wiki_articles") or {}
    wiki_got = {}
    for proj, arts in wiki.items():
        s, got = wiki_attention(arts, hist_start, end, proj)
        wiki_got.update({f"{proj}:{k}": v for k, v in got.items()})
        if len(s):
            att["wiki_views"] = att.get("wiki_views", 0.0) + s.reindex(weeks).fillna(0.0)
    if raw.get("github_repo"):
        att["github_stars_delta"] = github_stars_weekly(raw["github_repo"], weeks)
    pit_notes.append("news_count unavailable (GDELT 429 for this egress); attention sources = "
                     + ", ".join(att.columns))

    # ---- supply events (scheduled, announced in advance)
    se = pd.DataFrame((raw.get("crowding_sources") or {}).get("supply_events") or [])
    if not se.empty:
        se["date"] = pd.to_datetime(se["date"])
        se = se[["date", "kind", "ticker", "size_frac"]]
    else:
        se = pd.DataFrame(columns=["date", "kind", "ticker", "size_frac"])

    # ---- fundamentals momentum (for confirm_with_revisions proxy): core median revenue_ttm growth
    rev = pd.DataFrame(np.nan, index=weeks, columns=core)
    for tk in core:
        f = fund.get(tk)
        if f is None or f.empty:
            continue
        s = f.drop_duplicates("ann_date", keep="last").set_index("ann_date")["revenue_ttm"]
        s = s.groupby(level=0).last()
        rev[tk] = s.reindex(weeks.union(s.index)).ffill().reindex(weeks)
    data = {"ret": ret, "bench": bench.to_frame(), "attention": att, "supply_events": se,
            "revenue_ttm_core": rev, **{f"implied_growth_{k}": v for k, v in ig.items()}}
    meta = {"case_id": spec.case_id, "market": market, "core": core, "second_order": second,
            "etf_launch_dates": [str(pd.Timestamp(x).date()) for x in sorted(launches)], "etf_log": etf_log,
            "engine": "fcf", "sources": sources, "fundamentals": fnotes, "implied_growth_status": ig_status,
            "wiki_views_by_article": wiki_got, "pit_notes": pit_notes,
            "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "hist_start": str(hist_start.date())}
    return data, meta


def write_case(data: dict, meta: dict, out: str) -> None:
    import os
    os.makedirs(out, exist_ok=True)
    for k, v in data.items():
        v.to_parquet(f"{out}/{k}.parquet")
    json.dump(meta, open(f"{out}/meta.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False, default=str)

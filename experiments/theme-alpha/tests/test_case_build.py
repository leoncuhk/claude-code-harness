"""Known-answer tests for the Case Lab data transforms and the new loop mechanisms."""
import numpy as np
import pandas as pd

from theme_alpha.cases.build import _fix_ann_dates, _sum_last4, _ytd_to_ttm, abnormal_turnover, membership_mask
from theme_alpha.cases.replay import pick_attention, revision_confirmation


def test_ytd_to_ttm_uses_prior_year_and_annualises_when_missing():
    df = pd.DataFrame({"report_date": pd.to_datetime(["2024-06-30", "2024-12-31", "2025-06-30", "2023-06-30"]),
                       "rev": [40.0, 100.0, 70.0, 30.0]})
    out = _ytd_to_ttm(df, ["rev"]).set_index("report_date")
    assert out.at[pd.Timestamp("2025-06-30"), "rev"] == 70 + 100 - 40          # YTD + FY(prev) - YTD(prev)
    assert out.at[pd.Timestamp("2024-12-31"), "ttm_method"] == "fy"
    assert out.at[pd.Timestamp("2023-06-30"), "rev"] == 60.0                    # 30 x 12/6, no comparatives
    assert out.at[pd.Timestamp("2023-06-30"), "ttm_method"] == "annualised"


def test_sum_last4_needs_four_quarters():
    df = pd.DataFrame({"report_date": pd.date_range("2025-03-31", periods=5, freq="QE"), "rev": [1.0, 2, 3, 4, 5]})
    out = _sum_last4(df, ["rev"])
    assert np.isnan(out["rev"].iloc[2]) and out["rev"].iloc[3] == 10 and out["rev"].iloc[4] == 14


def test_restamped_vendor_dates_fall_back_to_deadline():
    df = pd.DataFrame({"report_date": pd.to_datetime(["2025-06-30", "2026-06-30"]),
                       "ann_date": pd.to_datetime(["2026-08-10", "2026-08-10"])})   # 1st is a re-stamp
    out, n = _fix_ann_dates(df, "US")
    assert n == 1
    assert out["ann_date"].iloc[0] == pd.Timestamp("2025-06-30") + pd.Timedelta(days=50)
    assert out["ann_date"].iloc[1] == pd.Timestamp("2026-08-10")               # genuine release kept


def test_membership_mask_starts_at_public_date_and_rolls():
    weeks = pd.date_range("2025-01-03", periods=30, freq="W-FRI")
    h = pd.DataFrame({"quarter_end": pd.to_datetime(["2024-12-31", "2025-03-31"]), "stock": ["A", "B"],
                      "etf": ["E", "E"]})
    h["public_date"] = h["quarter_end"] + pd.Timedelta(days=25)
    M = membership_mask(h, weeks, exclude=[])
    assert not M.loc[:"2025-01-24", "A"].any()                                  # not public yet
    assert M.loc["2025-01-31":"2025-04-18", "A"].all()
    assert not M.loc["2025-04-25":, "A"].any() and M.loc["2025-04-25":, "B"].all()


def test_abnormal_turnover_uses_only_prior_weeks():
    w = pd.date_range("2025-01-03", periods=40, freq="W-FRI")
    dv = pd.DataFrame({"X": np.r_[np.ones(30), 5 * np.ones(10)]}, index=w)
    a = abnormal_turnover(dv, base_weeks=26, min_obs=8)
    assert np.isnan(a.iloc[0]) and abs(a.iloc[29] - 1.0) < 1e-12 and abs(a.iloc[30] - 5.0) < 1e-12


def test_revision_confirmation_planted_deceleration_vs_null():
    w = pd.date_range("2025-01-03", periods=80, freq="W-FRI")
    accel = pd.DataFrame({"A": np.exp(np.linspace(0, 1, 80) ** 2)}, index=w)          # accelerating
    decel = pd.DataFrame({"A": np.exp(np.sqrt(np.linspace(0, 1, 80)))}, index=w)       # decelerating
    assert not revision_confirmation(accel, w, ["A"]).any()
    assert revision_confirmation(decel, w, ["A"]).iloc[30:].all()
    assert not revision_confirmation(None, w, ["A"]).any()


def test_pick_attention_fallback_chain():
    w = pd.date_range("2025-01-03", periods=20, freq="W-FRI")
    att = pd.DataFrame({"turnover": np.ones(20), "wiki_views": np.r_[np.zeros(15), np.ones(5)]}, index=w)
    assert pick_attention(att, "github_stars_delta") == "turnover"   # wiki has < 8 non-zero weeks
    att["wiki_views"] = 1.0
    assert pick_attention(att, "news_count") == "wiki_views"
    assert pick_attention(att, "turnover") == "turnover"


def test_github_rate_is_last_known_not_interpolated(monkeypatch):
    from theme_alpha.cases import build
    s = pd.Series([0.0, 70.0, 70.0], index=pd.to_datetime(["2026-01-01", "2026-01-11", "2026-02-10"]))
    monkeypatch.setattr(build.web, "ossinsight_stars", lambda repo: s)
    w = pd.date_range("2026-01-02", periods=8, freq="W-FRI")
    r = build.github_stars_weekly("x/y", w)
    assert np.isnan(r.iloc[0])                       # before the second sample nothing is known
    assert r.loc["2026-01-16"] == 49.0               # 70 stars / 10 days * 7, known since 01-11
    assert r.loc["2026-02-06"] == 49.0               # still the last known rate (no peeking at 02-10)
    assert r.loc["2026-02-13"] == 0.0

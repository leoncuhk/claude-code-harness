import pandas as pd

from theme_alpha.data.scd import snapshots_to_scd
from theme_alpha.signals.expectations import TwoStageReverseDCF


def test_reverse_dcf_recovers_growth():
    eng = TwoStageReverseDCF()
    g, fcf, wacc, tg, n = 0.12, 100.0, 0.09, 0.03, 10
    v, cf = 0.0, fcf
    for y in range(1, n + 1):
        cf *= 1 + g
        v += cf / (1 + wacc) ** y
    ev = v + cf * (1 + tg) / (wacc - tg) / (1 + wacc) ** n
    r = eng.implied(price=ev / 10, shares=10, net_debt=0.0, fcf_ttm=fcf, wacc=wacc, terminal_g=tg, years=n)
    assert r.status == "ok" and abs(r.implied_growth - g) < 1e-6
    assert eng.implied(price=1, shares=1, net_debt=0, fcf_ttm=-5).status == "non_positive_fcf"


def test_snapshots_to_scd_handles_gaps_and_censoring():
    d = pd.to_datetime(["2026-01-05", "2026-01-06", "2026-01-07", "2026-01-08"])
    snaps = pd.DataFrame([(d[0], "C", "A"), (d[1], "C", "A"), (d[3], "C", "A"),   # A leaves d2, returns d3
                          (d[1], "C", "B"), (d[2], "C", "B")],                     # B joins d1, leaves d3
                         columns=["snapshot_date", "concept_id", "stock_id"])
    scd = snapshots_to_scd(snaps).sort_values(["stock_id", "in_date"]).reset_index(drop=True)
    a = scd[scd.stock_id == "A"]
    assert list(a.in_date) == [d[0], d[3]] and a.out_date.iloc[0] == d[2] and pd.isna(a.out_date.iloc[1])
    assert bool(a.left_censored.iloc[0]) and not bool(a.left_censored.iloc[1])
    b = scd[scd.stock_id == "B"].iloc[0]
    assert b.in_date == d[1] and b.out_date == d[3]

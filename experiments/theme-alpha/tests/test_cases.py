import numpy as np
import pandas as pd

from theme_alpha.cases.diagnostics import exit_value, landmarks, lead_lag, tsmom_capture
from theme_alpha.signals.expectations import SalesDrivenReverseDCF


def test_sales_dcf_recovers_growth_for_loss_maker():
    eng = SalesDrivenReverseDCF()
    kw = dict(shares=100.0, net_debt=-50.0, revenue_ttm=80.0, current_margin=-0.60, target_margin=0.25,
              tax=0.2, sales_to_capital=1.5, wacc=0.10, terminal_g=0.03, years=10)
    # higher price -> higher implied revenue CAGR (monotone), solvable for a deep loss-maker
    gs = [eng.implied(price=p, **kw).implied_growth for p in (20.0, 60.0, 200.0)]
    assert all(g is not None for g in gs) and gs[0] < gs[1] < gs[2]
    assert eng.implied(price=1, shares=1, net_debt=0, revenue_ttm=0, current_margin=0).status == "non_positive_revenue"


def test_landmarks_and_exit_value():
    w = pd.date_range("2025-01-03", periods=40, freq="W-FRI")
    ce = pd.Series(np.r_[np.linspace(0, 1.0, 20), np.linspace(1.0, 0.4, 20)], index=w)
    lm = landmarks(ce, 0.2)
    assert lm["peak_week"] == w[19] and abs(lm["drawdown_after_peak"] - 0.6) < 1e-9
    assert exit_value(ce, w[19]) > 0.59           # exiting at the peak avoids the fall
    assert exit_value(ce, w[5]) < 0               # exiting early forgoes the rise


def test_lead_lag_detects_one_week_follow():
    rng = np.random.default_rng(0)
    w = pd.date_range("2025-01-03", periods=200, freq="W-FRI")
    core = pd.Series(rng.normal(0, 0.03, 200), index=w)
    so = core.shift(1).fillna(0) * 0.8 + rng.normal(0, 0.01, 200)
    assert lead_lag(core, so)["best_lag"] == 1
    assert tsmom_capture(core)["buy_hold_excess"] == core.sum()

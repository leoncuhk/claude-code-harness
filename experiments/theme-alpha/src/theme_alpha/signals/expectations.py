"""Implied expectations (Mauboussin & Rappaport). Default engine: two-stage FCF reverse DCF that solves
for the 10-year FCF growth implied by today's enterprise value. Swap in the user's existing calculator
via `ExternalReverseDCF` (dotted path in configs/base.yaml: expectations.engine)."""
from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Protocol

from scipy.optimize import brentq


@dataclass
class ImpliedResult:
    implied_growth: float | None
    status: str  # ok | non_positive_fcf | no_solution | missing_input


class ImpliedExpectationsEngine(Protocol):
    def implied(self, *, price: float, shares: float, net_debt: float, fcf_ttm: float,
                wacc: float, terminal_g: float, years: int) -> ImpliedResult: ...


class TwoStageReverseDCF:
    def implied(self, *, price, shares, net_debt, fcf_ttm, wacc=0.09, terminal_g=0.03, years=10) -> ImpliedResult:
        if any(v is None for v in (price, shares, net_debt, fcf_ttm)):
            return ImpliedResult(None, "missing_input")
        if fcf_ttm <= 0:
            return ImpliedResult(None, "non_positive_fcf")  # Phase 1: fall back to NOPAT-based engine
        target_ev = price * shares + net_debt

        def ev(g: float) -> float:
            v, cf = 0.0, fcf_ttm
            for y in range(1, years + 1):
                cf *= 1 + g
                v += cf / (1 + wacc) ** y
            tv = cf * (1 + terminal_g) / (wacc - terminal_g)
            return v + tv / (1 + wacc) ** years

        try:
            return ImpliedResult(brentq(lambda g: ev(g) - target_ev, -0.5, 2.0), "ok")
        except ValueError:
            return ImpliedResult(None, "no_solution")


class ExternalReverseDCF:
    """Adapter for an existing calculator: module must expose `implied_growth(**kwargs) -> float | None`."""

    def __init__(self, dotted_path: str):
        mod, fn = dotted_path.rsplit(".", 1)
        self._fn = getattr(importlib.import_module(mod), fn)

    def implied(self, **kw) -> ImpliedResult:
        g = self._fn(**kw)
        return ImpliedResult(g, "ok" if g is not None else "no_solution")


class SalesDrivenReverseDCF:
    """Reverse DCF for loss-making / early-stage firms (most space and AI-model names).

    Solves for the revenue CAGR over `years` implied by today's EV, assuming the operating margin moves
    linearly from `current_margin` to `target_margin`, growth is funded at `sales_to_capital`
    (new revenue per unit of invested capital), and the terminal period earns ROIC = wacc
    (no value creation after year N; conservative). Mauboussin's value drivers: sales growth,
    operating margin, incremental investment."""

    def implied(self, *, price, shares, net_debt, revenue_ttm, current_margin, target_margin=0.25,
                tax=0.20, sales_to_capital=1.5, wacc=0.10, terminal_g=0.03, years=10) -> ImpliedResult:
        if any(v is None for v in (price, shares, net_debt, revenue_ttm, current_margin)):
            return ImpliedResult(None, "missing_input")
        if revenue_ttm <= 0:
            return ImpliedResult(None, "non_positive_revenue")
        target_ev = price * shares + net_debt

        def ev(g: float) -> float:
            v, rev_prev, nopat = 0.0, revenue_ttm, 0.0
            for y in range(1, years + 1):
                rev = rev_prev * (1 + g)
                m = current_margin + (target_margin - current_margin) * y / years
                ebit = rev * m
                nopat = ebit * (1 - tax) if ebit > 0 else ebit
                fcf = nopat - (rev - rev_prev) / sales_to_capital
                v += fcf / (1 + wacc) ** y
                rev_prev = rev
            tv = nopat * (1 + terminal_g) * (1 - terminal_g / wacc) / (wacc - terminal_g)
            return v + tv / (1 + wacc) ** years

        try:
            return ImpliedResult(brentq(lambda g: ev(g) - target_ev, -0.5, 3.0), "ok")
        except ValueError:
            return ImpliedResult(None, "no_solution")

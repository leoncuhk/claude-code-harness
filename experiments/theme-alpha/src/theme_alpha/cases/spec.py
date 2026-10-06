"""Case specification (cases/*.yaml) and weekly case data container."""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd
import yaml


@dataclass
class CaseSpec:
    case_id: str
    title: str
    market: str
    window: dict                 # replay start / end
    universe: dict               # core / second_order_candidates / benchmark
    attention_sources: list
    crowding_sources: list
    known_events: list           # ANNOTATION ONLY - never used as a signal
    hypotheses: dict             # what each hypothesis predicts for this case
    role: str = "dev"            # dev (feedback loop allowed) | holdout (one-shot, no loop)
    raw: dict = field(default_factory=dict)

    @classmethod
    def load(cls, path: str) -> "CaseSpec":
        with open(path, encoding="utf-8") as f:
            d = yaml.safe_load(f)
        return cls(case_id=d["case_id"], title=d["title"], market=d["market"], window=d["window"],
                   universe=d["universe"], attention_sources=d.get("attention_sources", []),
                   crowding_sources=d.get("crowding_sources", []), known_events=d.get("known_events", []),
                   hypotheses=d.get("hypotheses", {}), role=d.get("role", "dev"), raw=d)


@dataclass
class CaseData:
    """Weekly, point-in-time case panel. Built by scripts/fetch_case_data.py (or from a synthetic bundle)."""
    ret: pd.DataFrame                 # week x ticker, weekly total return (NaN before listing / when untradable)
    bench: pd.Series                  # week, benchmark weekly return
    core: list                        # tickers in the theme as known at each date (v1: static list + listing NaNs)
    second_order: list                # candidate low-visibility beneficiaries
    attention: pd.DataFrame           # week x source (news_count, github_stars_delta, search_index, token_share...)
    etf_launch_dates: list            # dates of thematic ETF launches
    supply_events: pd.DataFrame       # date, kind (ipo / lockup / index_inclusion / placement), size_frac
    implied_growth: pd.DataFrame      # week x ticker, from the expectations engine (NaN if not solvable)
    meta: dict = field(default_factory=dict)

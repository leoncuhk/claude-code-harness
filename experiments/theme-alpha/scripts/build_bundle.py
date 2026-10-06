"""Phase 1: build data/processed/bundle from real providers. TEMPLATE - wire your providers here.

Order of operations (each step must be PIT):
  1. universe + daily returns (incl. delisted)        -> weekly.to_weekly_returns
  2. benchmark                                         -> weekly compounded
  3. concepts (created_at) + membership SCD            -> provider (JoinQuant history) or data/scd.snapshots_to_scd
  4. news -> theme_docs via themes/zero_shot.theme_doc_counts (concepts alive at each week only)
  5. news -> comention edges (pairs of stock_ids in the same doc, aggregated per week)
  6. ETF list -> etf_launches (map ETF benchmark/name to concept_id with the same zero-shot matcher)
  7. fundamentals_pit (ann_date) x weekly price -> implied_growth via signals/expectations engine
  8. DataBundle(...).to_parquet(out); then `make audit`
"""
from __future__ import annotations

import sys

sys.path.insert(0, "src")

if __name__ == "__main__":
    raise SystemExit("build_bundle.py is a template: implement providers (Phase 1) and remove this line.")

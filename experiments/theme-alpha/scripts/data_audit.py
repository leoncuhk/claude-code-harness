"""Phase 1 data audit: coverage + point-in-time red flags. Writes reports/data_audit.json.

  python scripts/data_audit.py --bundle data/processed/bundle
  python scripts/data_audit.py --synthetic"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, "src")
from theme_alpha.data.bundle import DataBundle, validate_bundle  # noqa: E402
from theme_alpha.data.providers.synthetic import generate  # noqa: E402


def audit(b: DataBundle) -> dict:
    m, c = b.membership, b.concepts
    created = c.set_index("concept_id")["created_at"]
    in_eq_created = (m["in_date"] == m["concept_id"].map(created)).mean()
    r = {
        "weeks": [str(b.weeks[0].date()), str(b.weeks[-1].date()), len(b.weeks)],
        "n_stocks": len(b.stock_ids),
        "ret_nan_frac": float(np.isnan(b.stock_ret.to_numpy()).mean()),
        "n_concepts": len(c),
        "concepts_created_in_panel_frac": float((c["created_at"] > b.weeks[0]).mean()),
        "membership_rows": len(m),
        "membership_with_out_date_frac": float(m["out_date"].notna().mean()),
        "membership_in_equals_created_frac": float(in_eq_created),
        "docs_per_week_median": float(b.theme_docs.groupby("week")["n_docs"].sum().median()),
        "comention_edges_per_week_median": float(b.comention.groupby("week").size().median()),
        "etf_launches": len(b.etf_launches),
        "implied_growth_coverage": float(np.isfinite(b.implied_growth.to_numpy()).mean()),
        "validate_bundle": validate_bundle(b),
    }
    flags = []
    if r["membership_with_out_date_frac"] == 0:
        flags.append("no membership ever ends -> looks like TODAY's snapshot, not PIT (survivorship in concepts)")
    if r["membership_in_equals_created_frac"] > 0.95 and r["concepts_created_in_panel_frac"] < 0.05:
        flags.append("all members joined at concept creation and no concept created in-panel -> back-filled?")
    if r["implied_growth_coverage"] < 0.5:
        flags.append("implied growth coverage < 50%: H4 underpowered; implement NOPAT fallback")
    r["red_flags"] = flags
    return r


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", default="data/processed/bundle")
    ap.add_argument("--synthetic", action="store_true")
    a = ap.parse_args()
    b = generate() if a.synthetic else DataBundle.from_parquet(a.bundle)
    rep = audit(b)
    os.makedirs("reports", exist_ok=True)
    with open("reports/data_audit.json", "w") as f:
        json.dump(rep, f, indent=2, ensure_ascii=False, default=str)
    print(json.dumps(rep, indent=2, ensure_ascii=False, default=str))

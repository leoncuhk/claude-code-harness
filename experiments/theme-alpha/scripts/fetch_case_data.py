"""Build data/cases/<case_id>/ for the feedback loop from free web sources.

  python scripts/fetch_case_data.py --case us_space_2025
  python scripts/fetch_case_data.py --all

Writes: ret.parquet (week x ticker), bench.parquet, attention.parquet (week x source),
        supply_events.parquet, implied_growth_{fcf,sales,auto}.parquet, revenue_ttm_core.parquet, meta.json
All three expectations engines are built up front, so switching `expectations_engine` in the loop does
not require a refetch. Raw pulls are cached under data/raw/web/ with their pull timestamps.
PIT rules and known data gaps are listed in src/theme_alpha/cases/build.py and in meta.json["pit_notes"].

Prototype-quality sources (see src/theme_alpha/data/providers/web.py). Confirmatory work needs a PIT vendor."""
from __future__ import annotations

import argparse
import json
import sys

sys.path.insert(0, "src")
from theme_alpha.cases.build import build_case, write_case  # noqa: E402
from theme_alpha.cases.spec import CaseSpec  # noqa: E402
from theme_alpha.hypotheses.common import load_yaml  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", action="append", default=[])
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    cases = load_yaml("configs/case_lab.yaml")["frozen"]["dev_cases"] if a.all else a.case
    if not cases:
        raise SystemExit("--case <id> or --all")
    base = load_yaml("configs/base.yaml")
    for cid in cases:
        spec = CaseSpec.load(f"cases/{cid}.yaml")
        data, meta = build_case(spec, base)
        write_case(data, meta, f"data/cases/{cid}")
        ig = data["implied_growth_auto"][meta["core"]].loc[spec.window["start"]:]
        print(json.dumps({"case": cid, "weeks": len(data["ret"]), "core": len(meta["core"]),
                          "second_order": len(meta["second_order"]), "etf_launches": len(meta["etf_launch_dates"]),
                          "attention": list(data["attention"].columns),
                          "ig_auto_coverage_core": round(float(ig.notna().mean().mean()), 3)},
                         ensure_ascii=False))


if __name__ == "__main__":
    main()

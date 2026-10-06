"""Run one hypothesis on synthetic or real data for a given split.

  python scripts/run_hypothesis.py --h H2 --data real --split validation
  python scripts/run_hypothesis.py --h H1 --data synthetic --split full
  python scripts/run_hypothesis.py --h H3 --data real --split holdout --unlock-holdout   # ONE shot

Rules enforced here: bundle validation, pre-registration hash check for confirmatory splits,
one-shot holdout, and an append-only trial log (reports/trials.jsonl)."""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, "src")
from theme_alpha.data.bundle import DataBundle, validate_bundle  # noqa: E402
from theme_alpha.data.providers.synthetic import SynthConfig, generate  # noqa: E402
from theme_alpha.hypotheses.common import load_yaml  # noqa: E402
from theme_alpha.hypotheses.registry import CONFIGS, RUNNERS  # noqa: E402
from theme_alpha.validation.prereg import check_frozen, claim_holdout, config_hashes  # noqa: E402
from theme_alpha.validation.trials import log_trial  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--h", required=True, choices=list(RUNNERS))
    ap.add_argument("--data", default="synthetic", choices=["synthetic", "synthetic-null", "real"])
    ap.add_argument("--bundle", default="data/processed/bundle")
    ap.add_argument("--split", default="full", choices=["full", "discovery", "validation", "holdout"])
    ap.add_argument("--unlock-holdout", action="store_true")
    ap.add_argument("--exploratory", action="store_true", help="allowed on discovery; never counts for gates")
    a = ap.parse_args()

    base = load_yaml("configs/base.yaml")
    cfg = load_yaml(CONFIGS[a.h])
    cfg["costs"] = base["costs"]

    if a.data == "real":
        b = DataBundle.from_parquet(a.bundle)
    else:
        b = generate(SynthConfig(planted=(a.data == "synthetic")))
    errs = validate_bundle(b)
    if errs:
        sys.exit("bundle invalid:\n  " + "\n  ".join(errs))

    start = end = None
    if a.split != "full":
        start, end = base["splits"][a.split]["start"], base["splits"][a.split]["end"]
    confirmatory = a.data == "real" and a.split in ("validation", "holdout") and not a.exploratory
    if confirmatory:
        changed = check_frozen()
        if changed:
            sys.exit(f"pre-registration violated, changed configs: {changed}. Run as --exploratory or re-freeze "
                     "(re-freezing after seeing validation results invalidates the confirmatory claim).")
    if a.split == "holdout":
        if not a.unlock_holdout:
            sys.exit("holdout requires --unlock-holdout (one shot per hypothesis)")
        claim_holdout(a.h)

    res = RUNNERS[a.h](b, cfg, start, end, split=a.split)
    print(res.summary())
    log_trial({"hypothesis": a.h, "data": a.data, "split": a.split, "confirmatory": confirmatory,
               "passed": res.passed, "metrics": res.metrics, "checks": res.checks,
               "config_hash": config_hashes().get(CONFIGS[a.h])})
    os.makedirs("reports", exist_ok=True)
    with open(f"reports/{a.h}_{a.data}_{a.split}.json", "w") as f:
        json.dump({"metrics": res.metrics, "checks": res.checks, "passed": res.passed, "notes": res.notes},
                  f, indent=2, default=str)


if __name__ == "__main__":
    main()

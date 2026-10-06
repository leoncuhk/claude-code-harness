"""One feedback-loop iteration over the dev cases:  do -> look -> adjust -> do again.

  python scripts/case_loop.py --iter 0 --note "baseline"                      # all dev cases
  python scripts/case_loop.py --iter 1 --set expectations_engine=auto --note "loss-makers need sales DCF"
  python scripts/case_loop.py --synthetic --iter 0 --note "harness check"      # offline

Each run: replays every dev case with the current mechanisms (+ the one --set override), writes
reports/loop/iter_NN.json, prints a delta table vs the previous iteration, appends a card to
reports/loop/ITERATIONS.md and a line to reports/trials.jsonl. The AGENT then reads the card,
decides accept/reject per LOOP.md, and plans the next single change."""
from __future__ import annotations

import argparse
import copy
import glob
import json
import os
import sys

sys.path.insert(0, "src")
from theme_alpha.cases.replay import case_from_bundle, replay  # noqa: E402
from theme_alpha.cases.spec import CaseData, CaseSpec  # noqa: E402
from theme_alpha.data.providers.synthetic import SynthConfig, generate  # noqa: E402
from theme_alpha.hypotheses.common import load_yaml  # noqa: E402
from theme_alpha.validation.trials import log_trial  # noqa: E402

OUT = "reports/loop"


def load_case_data(case_id: str, engine: str = "fcf") -> CaseData:
    """`engine` comes from the loop's `expectations_engine` mechanism (all engines are prebuilt)."""
    import pandas as pd
    p = f"data/cases/{case_id}"
    if not os.path.exists(p):
        raise SystemExit(f"missing {p}: run scripts/fetch_case_data.py --case {case_id} first")
    rd = pd.read_parquet
    meta = json.load(open(f"{p}/meta.json", encoding="utf-8"))
    meta["engine"] = engine
    if os.path.exists(f"{p}/revenue_ttm_core.parquet"):
        meta["revenue_ttm_core"] = rd(f"{p}/revenue_ttm_core.parquet")
    return CaseData(rd(f"{p}/ret.parquet"), rd(f"{p}/bench.parquet")["bench"], meta["core"], meta["second_order"],
                    rd(f"{p}/attention.parquet"), meta["etf_launch_dates"], rd(f"{p}/supply_events.parquet"),
                    rd(f"{p}/implied_growth_{engine}.parquet"), meta)


def flat(d: dict, prefix: str = "") -> dict:
    out = {}
    for k, v in d.items():
        if isinstance(v, dict) and k != "xcorr_by_lag":
            out.update(flat(v, f"{prefix}{k}."))
        elif isinstance(v, (int, float)) or v is None or isinstance(v, str):
            out[f"{prefix}{k}"] = v
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--iter", type=int, required=True)
    ap.add_argument("--set", action="append", default=[], help="mechanism override key=value (ONE per iteration)")
    ap.add_argument("--note", required=True, help="why this change (from the previous observation)")
    ap.add_argument("--synthetic", action="store_true")
    a = ap.parse_args()
    if len(a.set) > 1:
        raise SystemExit("one change per iteration (LOOP.md rule 1)")
    cfg = copy.deepcopy(load_yaml("configs/case_lab.yaml"))
    for kv in a.set:
        k, v = kv.split("=", 1)
        if k not in cfg["mechanisms"]:
            raise SystemExit(f"{k} is not a mechanism knob (frozen keys cannot be changed)")
        cfg["mechanisms"][k] = yaml_value(v)

    results = {}
    if a.synthetic:
        b = generate(SynthConfig())
        first = b.etf_launches.sort_values("list_date").iloc[len(b.etf_launches) // 3]
        t0 = first["list_date"]
        d = case_from_bundle(b, first["concept_id"], t0 - _weeks(60), t0 + _weeks(30))
        results["synthetic"] = replay(d, cfg, t0 - _weeks(60), t0 + _weeks(30))
    else:
        for cid in cfg["frozen"]["dev_cases"]:
            spec = CaseSpec.load(f"cases/{cid}.yaml")
            results[cid] = replay(load_case_data(cid, cfg["mechanisms"]["expectations_engine"]), cfg, spec.window["start"], spec.window["end"])

    os.makedirs(OUT, exist_ok=True)
    tag = "synthetic_" if a.synthetic else ""
    path = f"{OUT}/{tag}iter_{a.iter:02d}.json"
    json.dump({"iter": a.iter, "note": a.note, "override": a.set, "mechanisms": cfg["mechanisms"],
               "results": results}, open(path, "w"), indent=2, default=str, ensure_ascii=False)
    prev = sorted(p for p in glob.glob(f"{OUT}/{tag}iter_*.json") if p != path)
    prev_res = json.load(open(prev[-1]))["results"] if prev else {}
    lines = [f"\n## iter {a.iter:02d} — {a.note}", f"override: {a.set or 'none'}", "",
             "| case | metric | prev | now |", "|---|---|---|---|"]
    for cid, r in results.items():
        now, old = flat(r), flat(prev_res.get(cid, {}))
        for k, v in now.items():
            if k.startswith("landmarks."):
                continue
            lines.append(f"| {cid} | {k} | {old.get(k, '—')} | {v} |")
    lines.append("\ndecision: _agent fills: ACCEPT / REJECT + one-line reason + next single change_")
    card = "\n".join(lines)
    with open(f"{OUT}/{tag}ITERATIONS.md", "a", encoding="utf-8") as f:
        f.write(card + "\n")
    print(card)
    log_trial({"hypothesis": "CASE_LOOP", "iter": a.iter, "override": a.set, "note": a.note,
               "synthetic": a.synthetic, "metrics": {c: flat(r) for c, r in results.items()}})


def yaml_value(v: str):
    import yaml
    return yaml.safe_load(v)


def _weeks(n: int):
    import pandas as pd
    return pd.Timedelta(weeks=n)


if __name__ == "__main__":
    main()

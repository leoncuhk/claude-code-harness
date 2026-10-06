"""Power (and size) of each hypothesis test at a given effect scale.

  python scripts/power_analysis.py --h H1,H2,H4 --scales 0.25,0.5,1.0 --n-sims 10
  python scripts/power_analysis.py --h H2 --calibrate-from data/processed/bundle

Interpretation: if power at a REALISTIC effect size (literature magnitude, scale chosen BEFORE seeing
real results) is < 0.8, a real-data FAIL is 'inconclusive', not 'no effect'. Fix the design first
(longer sample, coarser horizon, fewer/larger baskets) and only then `make freeze`."""
from __future__ import annotations

import argparse
import sys
from dataclasses import replace

import numpy as np

sys.path.insert(0, "src")
from theme_alpha.data.bundle import DataBundle  # noqa: E402
from theme_alpha.data.pit import MembershipIndex, basket_returns  # noqa: E402
from theme_alpha.data.providers.synthetic import SynthConfig, generate  # noqa: E402
from theme_alpha.hypotheses.common import load_yaml  # noqa: E402
from theme_alpha.hypotheses.registry import CONFIGS, RUNNERS  # noqa: E402


def calibrate(path: str) -> dict:
    b = DataBundle.from_parquet(path)
    resid = b.stock_ret.sub(b.bench_ret, axis=0)
    mi = MembershipIndex(b.membership, b.concepts, b.stock_ids)
    ex = basket_returns(b.stock_ret, mi).sub(b.bench_ret, axis=0)
    return {"idio_vol": float(np.nanmedian(resid.std())), "factor_vol": float(np.nanmedian(ex.std()))}


def scaled(base: SynthConfig, s: float) -> SynthConfig:
    return replace(base, episode_drift=base.episode_drift * s, phi_pre=base.phi_pre * s,
                   phi_post=base.phi_post * s, spill_beta=base.spill_beta * s, crowd_crash=base.crowd_crash * s)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--h", default="H1,H2,H4")
    ap.add_argument("--scales", default="0.25,0.5,1.0")
    ap.add_argument("--n-sims", type=int, default=10)
    ap.add_argument("--calibrate-from", default=None)
    a = ap.parse_args()
    base_cfg = load_yaml("configs/base.yaml")
    sc = SynthConfig()
    if a.calibrate_from:
        sc = replace(sc, **calibrate(a.calibrate_from))
        print("calibrated:", sc.idio_vol, sc.factor_vol)
    hs = [h.strip() for h in a.h.split(",")]
    print(f"{'hyp':4s} {'scale':>6s} {'power':>6s}   (null false-pass rate at the end)")
    for h in hs:
        cfg = load_yaml(CONFIGS[h]); cfg["costs"] = base_cfg["costs"]
        for s in [float(x) for x in a.scales.split(",")]:
            hits = [RUNNERS[h](generate(replace(scaled(sc, s), seed=100 + i)), cfg).passed for i in range(a.n_sims)]
            print(f"{h:4s} {s:6.2f} {np.mean(hits):6.2f}")
        nulls = [RUNNERS[h](generate(replace(sc, planted=False, seed=200 + i)), cfg).passed for i in range(a.n_sims)]
        print(f"{h:4s}  null  {np.mean(nulls):6.2f}  <- must be ~0 (size)")


if __name__ == "__main__":
    main()

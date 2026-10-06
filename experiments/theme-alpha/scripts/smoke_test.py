"""Known-answer test of the whole harness (run before touching real data).

Expectation: on PLANTED synthetic data every hypothesis PASSES (power), on NULL synthetic data every
hypothesis FAILS (size). Any deviation means the harness is broken or under-powered - fix it first."""
from __future__ import annotations

import sys
import time

sys.path.insert(0, "src")
from theme_alpha.data.bundle import validate_bundle  # noqa: E402
from theme_alpha.data.providers.synthetic import SynthConfig, generate  # noqa: E402
from theme_alpha.hypotheses.common import load_yaml  # noqa: E402
from theme_alpha.hypotheses.registry import CONFIGS, RUNNERS  # noqa: E402


def main(only: list[str] | None = None) -> int:
    base = load_yaml("configs/base.yaml")
    bad = 0
    for planted in (True, False):
        b = generate(SynthConfig(planted=planted))
        assert not validate_bundle(b), validate_bundle(b)
        for hid, run in RUNNERS.items():
            if only and hid not in only:
                continue
            cfg = load_yaml(CONFIGS[hid]); cfg["costs"] = base["costs"]
            t0 = time.time()
            res = run(b, cfg, split="full")
            expect = planted
            ok = res.passed == expect
            bad += (not ok)
            tag = "planted" if planted else "null   "
            print(f"{tag} {hid}: {'PASS' if res.passed else 'FAIL'} (expected {'PASS' if expect else 'FAIL'}) "
                  f"{'OK' if ok else '<<< HARNESS PROBLEM'}  [{time.time()-t0:.1f}s]")
            if not ok or "-v" in sys.argv:
                print(res.summary())
    print("SMOKE", "OK" if bad == 0 else f"FAILED ({bad} mismatches)")
    return bad


if __name__ == "__main__":
    only = [a for a in sys.argv[1:] if a.startswith("H")]
    sys.exit(1 if main(only or None) else 0)

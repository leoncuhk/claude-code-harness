"""Pre-registration: freeze hypothesis configs by hash; one-shot holdout lock."""
from __future__ import annotations

import glob
import hashlib
import json
import os

LOCK = "configs/prereg.lock"


def config_hashes(pattern: str = "configs/**/*.yaml") -> dict[str, str]:
    out = {}
    for p in sorted(glob.glob(pattern, recursive=True)):
        with open(p, "rb") as f:
            out[p] = hashlib.sha256(f.read()).hexdigest()
    return out


def freeze() -> dict:
    h = config_hashes()
    with open(LOCK, "w") as f:
        json.dump(h, f, indent=2)
    return h


def check_frozen() -> list[str]:
    """Return list of config files whose content changed since freeze (empty = OK)."""
    if not os.path.exists(LOCK):
        return ["<no prereg.lock: run `make freeze` before confirmatory runs>"]
    with open(LOCK) as f:
        locked = json.load(f)
    now = config_hashes()
    return [p for p in set(locked) | set(now) if locked.get(p) != now.get(p)]


def holdout_marker(hid: str) -> str:
    return f"reports/HOLDOUT_USED_{hid}.json"


def claim_holdout(hid: str) -> None:
    """Holdout may be evaluated ONCE per hypothesis. Raises if already used."""
    m = holdout_marker(hid)
    if os.path.exists(m):
        raise RuntimeError(f"Holdout for {hid} already consumed ({m}). Refusing to re-run.")
    os.makedirs("reports", exist_ok=True)
    with open(m, "w") as f:
        json.dump({"hypothesis": hid, "hashes": config_hashes()}, f, indent=2)

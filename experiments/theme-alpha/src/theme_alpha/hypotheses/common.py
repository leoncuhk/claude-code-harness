from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import yaml

OPS = {"gt": lambda a, b: a > b, "ge": lambda a, b: a >= b, "lt": lambda a, b: a < b, "le": lambda a, b: a <= b}


@dataclass
class HypothesisResult:
    hid: str
    split: str
    data: str
    metrics: dict
    checks: dict
    passed: bool
    notes: list = field(default_factory=list)

    def summary(self) -> str:
        lines = [f"[{self.hid}] data={self.data} split={self.split} -> {'PASS' if self.passed else 'FAIL'}"]
        for k, v in self.metrics.items():
            lines.append(f"    {k:28s} {v:.4f}" if isinstance(v, (float, np.floating)) else f"    {k:28s} {v}")
        for k, ok in self.checks.items():
            lines.append(f"    gate {k:23s} {'ok' if ok else 'FAILED'}")
        lines += [f"    note: {n}" for n in self.notes]
        return "\n".join(lines)


def evaluate_gates(metrics: dict, gates: dict) -> dict:
    """Gate keys are '<metric>_<op>' with op in gt/ge/lt/le, e.g. 't_stat_ge: 3.0'."""
    checks = {}
    for key, thr in gates.items():
        name, op = key.rsplit("_", 1)
        v = metrics.get(name, float("nan"))
        checks[key] = bool(v is not None and not (isinstance(v, float) and np.isnan(v)) and OPS[op](v, thr))
    return checks


def load_yaml(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def window(weeks: pd.DatetimeIndex, start: str | None, end: str | None) -> np.ndarray:
    m = np.ones(len(weeks), dtype=bool)
    if start:
        m &= weeks >= pd.Timestamp(start)
    if end:
        m &= weeks <= pd.Timestamp(end)
    return m

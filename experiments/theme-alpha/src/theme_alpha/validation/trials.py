"""Append-only trial log. EVERY run (incl. failed / exploratory) is recorded; DSR uses the count."""
from __future__ import annotations

import json
import os
import time

LOG = "reports/trials.jsonl"


def log_trial(record: dict, path: str = LOG) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    record = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), **record}
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def load_trials(hypothesis: str | None = None, path: str = LOG) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    return [r for r in rows if hypothesis is None or r.get("hypothesis") == hypothesis]

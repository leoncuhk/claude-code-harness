"""PreToolUse guard: CLAUDE.md is guidance; this enforces the pre-registration rules.
Exit 2 = block, stderr is shown to Claude as the reason."""
import json
import os
import sys

ALWAYS_LOCKED = ("reports/trials.jsonl", "configs/prereg.lock")
LOCKED_AFTER_FREEZE_PREFIX = ("configs/",)

data = json.load(sys.stdin)
path = (data.get("tool_input") or {}).get("file_path", "")
root = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
rel = os.path.relpath(os.path.abspath(path), root) if path else ""

if rel in ALWAYS_LOCKED or os.path.basename(rel).startswith("HOLDOUT_USED_"):
    sys.stderr.write(f"BLOCKED: {rel} is append-only / system-managed. Use the scripts, never edit by hand.\n")
    sys.exit(2)
if os.path.exists(os.path.join(root, "configs/prereg.lock")) and rel.startswith(LOCKED_AFTER_FREEZE_PREFIX):
    sys.stderr.write(f"BLOCKED: {rel} is frozen (configs/prereg.lock exists). Changes after freeze are "
                     "exploratory only; ask the human before re-freezing.\n")
    sys.exit(2)
sys.exit(0)

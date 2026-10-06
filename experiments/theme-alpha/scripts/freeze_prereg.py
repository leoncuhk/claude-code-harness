"""Freeze pre-registered configs. Run ONCE after the power analysis, BEFORE any confirmatory run."""
import sys

sys.path.insert(0, "src")
from theme_alpha.validation.prereg import freeze  # noqa: E402

for path, h in freeze().items():
    print(f"{h[:12]}  {path}")
print("written configs/prereg.lock - commit it together with configs/ (git tag prereg-v1)")

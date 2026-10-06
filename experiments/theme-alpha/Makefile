PY ?= python
export PYTHONPATH := src

.PHONY: setup smoke test power freeze audit bundle snapshot h1 h2 h3 h4 loop-check

setup:      ## install package + dev deps + git guard
	$(PY) -m pip install -e ".[dev,web]"
	git config core.hooksPath .githooks || true

smoke:      ## known-answer test: planted effects must PASS, null data must FAIL
	$(PY) scripts/smoke_test.py

test:       ## unit tests
	$(PY) -m pytest -q

power:      ## power analysis on synthetic data calibrated to real stats
	$(PY) scripts/power_analysis.py --n-sims 10

freeze:     ## hash pre-registered configs -> configs/prereg.lock
	$(PY) scripts/freeze_prereg.py

audit:      ## data coverage / PIT audit report (Phase 1)
	$(PY) scripts/data_audit.py

bundle:     ## build weekly research bundle from providers (Phase 1)
	$(PY) scripts/build_bundle.py

snapshot:   ## daily PIT snapshot of concept membership + ETF list (cron)
	$(PY) scripts/snapshot_daily.py

h1 h2 h3 h4:
	$(PY) scripts/run_hypothesis.py --h $(shell echo $@ | tr a-z A-Z) --data real --split validation

loop-check: ## feedback-loop harness on a synthetic case (offline)
	$(PY) scripts/case_loop.py --synthetic --iter 0 --note "harness check"

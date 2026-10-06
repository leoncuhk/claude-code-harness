# CLAUDE.md — theme-alpha

Read `SPEC.md` before doing anything, and `LOOP.md` before any case-lab work.

**Working style: feedback loops.** Do one thing, look at the result, adjust based on it, do it again.
Every loop iteration changes ONE mechanism, is logged, and is accepted only if it does not hurt the
other dev cases and `make smoke` stays 8/8. It defines the investment thesis, the four pre-registered
hypotheses (H1–H4), data contracts, and the phase plan with acceptance criteria. Work phase by phase;
do not start a phase until the previous phase's acceptance check passes.

## Commands

```bash
make setup          # pip install -e ".[dev]"
make test           # unit tests (must stay green)
make smoke          # known-answer test: planted -> PASS, null -> FAIL for H1..H4
make power          # power analysis on synthetic data (Phase 2)
make audit          # data coverage + PIT red flags (Phase 1) -> reports/data_audit.json
make freeze         # hash configs -> configs/prereg.lock (Phase 2 end, once)
make loop-check     # feedback-loop harness on a synthetic case (offline)
python scripts/fetch_case_data.py --all     # build data/cases/* from free web sources (docs/case_data.md)
python scripts/case_loop.py --iter N --set <knob>=<value> --note "<why>"   # one loop iteration
python scripts/loop_decide.py "ACCEPT|REJECT: <reason>. next: <change>"   # fill the last card's decision
python scripts/run_hypothesis.py --h H2 --data real --split validation
```

## Non-negotiable rules

1. **Point-in-time.** A value stamped at week t must have been knowable at the close of week t.
   Financials join on `ann_date`; concept membership comes from a historical SCD; concepts do not
   exist before `created_at`; signals formed at t trade from t+1. If unsure whether a vendor field is
   PIT, assume it is NOT and record it in the audit.
2. **Survivorship.** Universe includes delisted stocks. Membership must include stocks that later left.
3. **Pre-registration.** After `make freeze`, never edit `configs/hypotheses/*.yaml` or
   `configs/base.yaml` to make a result pass. Any change after freeze = exploratory run only.
4. **Holdout is one shot** per hypothesis (`--unlock-holdout`, enforced by `reports/HOLDOUT_USED_*`).
   Never inspect holdout-period returns while developing.
5. **Log every trial.** `run_hypothesis.py` appends to `reports/trials.jsonl`; do not delete lines.
   DSR uses the trial count. Negative results are results — keep them.
6. **No LLM in the signal path for backtests** (`text.llm_in_signal_path: false`). LLMs may label or
   summarise for humans; their outputs never feed a backtested signal (parametric look-ahead).
   Embedding models are allowed but weeks before the model's release date are flagged as possibly
   contaminated; the holdout must lie after the release date.
7. **Costs and tradability.** Use `configs/base.yaml: costs.round_trip`; untradable (suspended /
   limit-locked) weeks have NaN returns and cannot be entered or exited.
8. **Case facts are annotation only.** `known_events` in `cases/*.yaml` and hindsight landmarks
   (breakout, peak) must never feed a signal. Second-order universes come from the PIT rule in the case
   yaml, never from hand-picked lists.
9. **Every new signal or data transform ships with**: a unit test, and a planted-effect case in
   `data/providers/synthetic.py` so `make smoke` proves the test can find it and rejects it on null data.

## Enforcement (not just guidance)

- `.claude/settings.json` registers a PreToolUse hook (`.claude/hooks/guard_frozen.py`) that blocks
  Edit/Write on `reports/trials.jsonl`, `configs/prereg.lock`, `reports/HOLDOUT_USED_*`, and on
  everything under `configs/` once `configs/prereg.lock` exists.
- `.githooks/pre-commit` (enabled by `make setup`) re-checks frozen configs and the append-only trial
  log at commit time, which also catches changes made through shell commands.
- Human checkpoints: `make freeze`, re-freezing, and any `--unlock-holdout` run need the user's go-ahead.

## Code map

- `src/theme_alpha/data/` — `DataBundle` (the only object hypotheses consume), PIT helpers
  (`MembershipIndex`, `basket_returns`), SCD builder, weekly conversion, provider protocols/templates.
- `src/theme_alpha/themes/` — BERTrend-style attention (native), zero-shot doc counting, links (co-mention).
- `src/theme_alpha/signals/` — crowding flags, reverse-DCF implied expectations.
- `src/theme_alpha/portfolio/rotation.py` — long-only theme overlay with tracking-error budget.
- `src/theme_alpha/validation/` — NW / Fama-MacBeth / bootstrap, CPCV, DSR, PBO, trial log, prereg.
- `src/theme_alpha/hypotheses/h1..h4_*.py` — one `run(bundle, cfg, start, end, split)` each.

## Integration with existing tooling

- AFML stack (CPCV / DSR / PBO): may replace `validation/cpcv.py` and `validation/dsr_pbo.py` if it keeps
  the same function contracts; re-run `make test && make smoke` after swapping.
- Existing reverse-DCF calculator: point `expectations.engine` to it through `ExternalReverseDCF`
  (module must expose `implied_growth(**kwargs) -> float | None`).

## Performance notes

H3 recomputes link weights weekly (~40 s on synthetic data). At real scale (~5,000 stocks, ~400 concepts)
cache `MembershipIndex.asof_table(t)` per week and pre-aggregate co-mention edges with rolling sums
before optimising anything else.

"""Pick the THEME HOLDOUT by a mechanical rule BEFORE inspecting any returns. TEMPLATE.

Rule (configs/case_lab.yaml: frozen.holdout_rule): for each market (US / A / HK), rank candidate themes
(thematic ETFs' benchmarks, concept boards) by the jump in attention share between consecutive 13-week
windows during 2025-01..2026-06; take the top-8 overall excluding the dev cases; write
cases/holdout/<theme>.yaml with role: holdout. Uses ONLY attention data (no prices) so the choice cannot
be biased by outcomes. Commit the output together with configs/prereg.lock."""
raise SystemExit("TEMPLATE: implement after attention data for the full theme universe exists (Phase 1).")

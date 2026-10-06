
## iter 00 — baseline: all default mechanisms on real case data (news_count unavailable -> fallback chain)
override: none

| case | metric | prev | now |
|---|---|---|---|
| us_space_2025 | H1.attention_source | — | news_count |
| us_space_2025 | H1.attention_source_used | — | wiki_views |
| us_space_2025 | H1.first_weak_to_strong | — | None |
| us_space_2025 | H1.lead_weeks_vs_breakout | — | None |
| us_space_2025 | H1.car13_after_event | — | None |
| us_space_2025 | H2.capture_ratio | — | 0.8181327530642376 |
| us_space_2025 | H2.strategy_excess | — | 0.9684945099546889 |
| us_space_2025 | H2.buy_hold_excess | — | 1.1837865020405134 |
| us_space_2025 | H3.n_second_order | — | 0 |
| us_space_2025 | H4.first_flag | — | None |
| us_space_2025 | H4.flag_lead_weeks_vs_peak | — | None |
| us_space_2025 | H4.exit_value_to_end | — | None |
| us_space_2025 | H4.exit_value_26w | — | None |
| us_space_2025 | H4.flag_weeks | — | 0 |
| us_space_2025 | H4.implied_growth_coverage_core | — | 0.2879684418145957 |
| us_space_2025 | H4.blocked_by_missing_expectations | — | True |
| cn_optical_2025 | H1.attention_source | — | news_count |
| cn_optical_2025 | H1.attention_source_used | — | turnover |
| cn_optical_2025 | H1.first_weak_to_strong | — | 2025-06-13 |
| cn_optical_2025 | H1.lead_weeks_vs_breakout | — | -5 |
| cn_optical_2025 | H1.car13_after_event | — | 1.1480658767981091 |
| cn_optical_2025 | H2.capture_ratio | — | 0.7453642191718207 |
| cn_optical_2025 | H2.strategy_excess | — | 1.6302287214595534 |
| cn_optical_2025 | H2.buy_hold_excess | — | 2.1871572038578826 |
| cn_optical_2025 | H3.n_second_order | — | 66 |
| cn_optical_2025 | H3.best_lag | — | 0 |
| cn_optical_2025 | H3.lag1_minus_lag0 | — | -0.510414533249808 |
| cn_optical_2025 | H3.next_week_beta | — | -0.0491018759444499 |
| cn_optical_2025 | H3.next_week_t | — | -1.9990492995446971 |
| cn_optical_2025 | H4.first_flag | — | 2025-06-20 |
| cn_optical_2025 | H4.flag_lead_weeks_vs_peak | — | 52 |
| cn_optical_2025 | H4.exit_value_to_end | — | -2.037859875397337 |
| cn_optical_2025 | H4.exit_value_26w | — | -1.3341614726594493 |
| cn_optical_2025 | H4.flag_weeks | — | 44 |
| cn_optical_2025 | H4.implied_growth_coverage_core | — | 0.7148148148148149 |
| cn_optical_2025 | H4.blocked_by_missing_expectations | — | False |
| hk_ai_openclaw_2026 | H1.attention_source | — | news_count |
| hk_ai_openclaw_2026 | H1.attention_source_used | — | wiki_views |
| hk_ai_openclaw_2026 | H1.first_weak_to_strong | — | None |
| hk_ai_openclaw_2026 | H1.lead_weeks_vs_breakout | — | None |
| hk_ai_openclaw_2026 | H1.car13_after_event | — | None |
| hk_ai_openclaw_2026 | H2.capture_ratio | — | 0.2722436322644482 |
| hk_ai_openclaw_2026 | H2.strategy_excess | — | 0.519892959860899 |
| hk_ai_openclaw_2026 | H2.buy_hold_excess | — | 1.9096606797983533 |
| hk_ai_openclaw_2026 | H3.n_second_order | — | 0 |
| hk_ai_openclaw_2026 | H4.first_flag | — | None |
| hk_ai_openclaw_2026 | H4.flag_lead_weeks_vs_peak | — | None |
| hk_ai_openclaw_2026 | H4.exit_value_to_end | — | None |
| hk_ai_openclaw_2026 | H4.exit_value_26w | — | None |
| hk_ai_openclaw_2026 | H4.flag_weeks | — | 0 |
| hk_ai_openclaw_2026 | H4.implied_growth_coverage_core | — | 0.0 |
| hk_ai_openclaw_2026 | H4.blocked_by_missing_expectations | — | True |

decision: BASELINE. Landmarks: US peak 2026-05-29 (dd 56%), CN peak 2026-06-19 (dd 4%, still rising), HK peak 2026-06-19 (dd 71%). US/HK H4 blocked (IG coverage 0.29 / 0.00, FCF<=0) = problem A confirmed. CN H4 flags 2025-06-20, 52w before peak, exit_value_to_end -2.04 = problem C confirmed. H1: wiki fallback gives no weak->strong in US/HK; CN turnover transition lags breakout 5w. next: expectations_engine=auto

## iter 01 — problem A: loss-makers (US/HK) have FCF<=0 -> use sales-driven reverse DCF when FCF<=0; expect US/HK IG coverage up and H4 able to fire; CN mostly unchanged
override: ['expectations_engine=auto']

| case | metric | prev | now |
|---|---|---|---|
| us_space_2025 | H1.attention_source | news_count | news_count |
| us_space_2025 | H1.attention_source_used | wiki_views | wiki_views |
| us_space_2025 | H1.first_weak_to_strong | None | None |
| us_space_2025 | H1.lead_weeks_vs_breakout | None | None |
| us_space_2025 | H1.car13_after_event | None | None |
| us_space_2025 | H2.capture_ratio | 0.8181327530642376 | 0.8181327530642376 |
| us_space_2025 | H2.strategy_excess | 0.9684945099546889 | 0.9684945099546889 |
| us_space_2025 | H2.buy_hold_excess | 1.1837865020405134 | 1.1837865020405134 |
| us_space_2025 | H3.n_second_order | 0 | 0 |
| us_space_2025 | H4.first_flag | None | 2026-03-06 |
| us_space_2025 | H4.flag_lead_weeks_vs_peak | None | 12 |
| us_space_2025 | H4.exit_value_to_end | None | -0.23024245030405455 |
| us_space_2025 | H4.exit_value_26w | None | -0.18183849964756416 |
| us_space_2025 | H4.flag_weeks | 0 | 12 |
| us_space_2025 | H4.implied_growth_coverage_core | 0.2879684418145957 | 0.831360946745562 |
| us_space_2025 | H4.blocked_by_missing_expectations | True | False |
| cn_optical_2025 | H1.attention_source | news_count | news_count |
| cn_optical_2025 | H1.attention_source_used | turnover | turnover |
| cn_optical_2025 | H1.first_weak_to_strong | 2025-06-13 | 2025-06-13 |
| cn_optical_2025 | H1.lead_weeks_vs_breakout | -5 | -5 |
| cn_optical_2025 | H1.car13_after_event | 1.1480658767981091 | 1.1480658767981091 |
| cn_optical_2025 | H2.capture_ratio | 0.7453642191718207 | 0.7453642191718207 |
| cn_optical_2025 | H2.strategy_excess | 1.6302287214595534 | 1.6302287214595534 |
| cn_optical_2025 | H2.buy_hold_excess | 2.1871572038578826 | 2.1871572038578826 |
| cn_optical_2025 | H3.n_second_order | 66 | 66 |
| cn_optical_2025 | H3.best_lag | 0 | 0 |
| cn_optical_2025 | H3.lag1_minus_lag0 | -0.510414533249808 | -0.510414533249808 |
| cn_optical_2025 | H3.next_week_beta | -0.0491018759444499 | -0.0491018759444499 |
| cn_optical_2025 | H3.next_week_t | -1.9990492995446971 | -1.9990492995446971 |
| cn_optical_2025 | H4.first_flag | 2025-06-20 | 2025-06-27 |
| cn_optical_2025 | H4.flag_lead_weeks_vs_peak | 52 | 51 |
| cn_optical_2025 | H4.exit_value_to_end | -2.037859875397337 | -2.0045586469258563 |
| cn_optical_2025 | H4.exit_value_26w | -1.3341614726594493 | -1.3126682487937589 |
| cn_optical_2025 | H4.flag_weeks | 44 | 35 |
| cn_optical_2025 | H4.implied_growth_coverage_core | 0.7148148148148149 | 0.9888888888888889 |
| cn_optical_2025 | H4.blocked_by_missing_expectations | False | False |
| hk_ai_openclaw_2026 | H1.attention_source | news_count | news_count |
| hk_ai_openclaw_2026 | H1.attention_source_used | wiki_views | wiki_views |
| hk_ai_openclaw_2026 | H1.first_weak_to_strong | None | None |
| hk_ai_openclaw_2026 | H1.lead_weeks_vs_breakout | None | None |
| hk_ai_openclaw_2026 | H1.car13_after_event | None | None |
| hk_ai_openclaw_2026 | H2.capture_ratio | 0.2722436322644482 | 0.2722436322644482 |
| hk_ai_openclaw_2026 | H2.strategy_excess | 0.519892959860899 | 0.519892959860899 |
| hk_ai_openclaw_2026 | H2.buy_hold_excess | 1.9096606797983533 | 1.9096606797983533 |
| hk_ai_openclaw_2026 | H3.n_second_order | 0 | 0 |
| hk_ai_openclaw_2026 | H4.first_flag | None | None |
| hk_ai_openclaw_2026 | H4.flag_lead_weeks_vs_peak | None | None |
| hk_ai_openclaw_2026 | H4.exit_value_to_end | None | None |
| hk_ai_openclaw_2026 | H4.exit_value_26w | None | None |
| hk_ai_openclaw_2026 | H4.flag_weeks | 0 | 0 |
| hk_ai_openclaw_2026 | H4.implied_growth_coverage_core | 0.0 | 1.0 |
| hk_ai_openclaw_2026 | H4.blocked_by_missing_expectations | True | False |

decision: ACCEPT: (a) IG coverage US 0.29->0.83, HK 0.00->1.00, H4 unblocked; US now flags 2026-03-06, 12w before the 05-29 peak (exit_value_to_end -0.23: still early); (b) CN not worse (exit -2.04 -> -2.00); (c) smoke 8/8. next: HK still cannot flag: zero theme-ETF launches and own_history needs 26w of IG after a Jan IPO -> crowd_percentile_basis=peer_cross_section (problem B)

## iter 02 — problem E: HK has no theme-ETF launches; scheduled supply (MiniMax 44.85% lockup, SpaceX IPO) is PIT-legal crowding input; expect HK/US exit_value_26w up, CN unchanged (only a 0.5% insider sale)
override: ['use_supply_events=true']

| case | metric | prev | now |
|---|---|---|---|
| us_space_2025 | H1.attention_source | news_count | news_count |
| us_space_2025 | H1.attention_source_used | wiki_views | wiki_views |
| us_space_2025 | H1.first_weak_to_strong | None | None |
| us_space_2025 | H1.lead_weeks_vs_breakout | None | None |
| us_space_2025 | H1.car13_after_event | None | None |
| us_space_2025 | H2.capture_ratio | 0.8181327530642376 | 0.8181327530642376 |
| us_space_2025 | H2.strategy_excess | 0.9684945099546889 | 0.9684945099546889 |
| us_space_2025 | H2.buy_hold_excess | 1.1837865020405134 | 1.1837865020405134 |
| us_space_2025 | H3.n_second_order | 0 | 0 |
| us_space_2025 | H4.first_flag | 2026-03-06 | 2026-03-06 |
| us_space_2025 | H4.flag_lead_weeks_vs_peak | 12 | 12 |
| us_space_2025 | H4.exit_value_to_end | -0.23024245030405455 | -0.23024245030405455 |
| us_space_2025 | H4.exit_value_26w | -0.18183849964756416 | -0.18183849964756416 |
| us_space_2025 | H4.flag_weeks | 12 | 12 |
| us_space_2025 | H4.implied_growth_coverage_core | 0.831360946745562 | 0.831360946745562 |
| us_space_2025 | H4.blocked_by_missing_expectations | False | False |
| cn_optical_2025 | H1.attention_source | news_count | news_count |
| cn_optical_2025 | H1.attention_source_used | turnover | turnover |
| cn_optical_2025 | H1.first_weak_to_strong | 2025-06-13 | 2025-06-13 |
| cn_optical_2025 | H1.lead_weeks_vs_breakout | -5 | -5 |
| cn_optical_2025 | H1.car13_after_event | 1.1480658767981091 | 1.1480658767981091 |
| cn_optical_2025 | H2.capture_ratio | 0.7453642191718207 | 0.7453642191718207 |
| cn_optical_2025 | H2.strategy_excess | 1.6302287214595534 | 1.6302287214595534 |
| cn_optical_2025 | H2.buy_hold_excess | 2.1871572038578826 | 2.1871572038578826 |
| cn_optical_2025 | H3.n_second_order | 66 | 66 |
| cn_optical_2025 | H3.best_lag | 0 | 0 |
| cn_optical_2025 | H3.lag1_minus_lag0 | -0.510414533249808 | -0.510414533249808 |
| cn_optical_2025 | H3.next_week_beta | -0.0491018759444499 | -0.0491018759444499 |
| cn_optical_2025 | H3.next_week_t | -1.9990492995446971 | -1.9990492995446971 |
| cn_optical_2025 | H4.first_flag | 2025-06-27 | 2025-06-27 |
| cn_optical_2025 | H4.flag_lead_weeks_vs_peak | 51 | 51 |
| cn_optical_2025 | H4.exit_value_to_end | -2.0045586469258563 | -2.0045586469258563 |
| cn_optical_2025 | H4.exit_value_26w | -1.3126682487937589 | -1.3126682487937589 |
| cn_optical_2025 | H4.flag_weeks | 35 | 35 |
| cn_optical_2025 | H4.implied_growth_coverage_core | 0.9888888888888889 | 0.9888888888888889 |
| cn_optical_2025 | H4.blocked_by_missing_expectations | False | False |
| hk_ai_openclaw_2026 | H1.attention_source | news_count | news_count |
| hk_ai_openclaw_2026 | H1.attention_source_used | wiki_views | wiki_views |
| hk_ai_openclaw_2026 | H1.first_weak_to_strong | None | None |
| hk_ai_openclaw_2026 | H1.lead_weeks_vs_breakout | None | None |
| hk_ai_openclaw_2026 | H1.car13_after_event | None | None |
| hk_ai_openclaw_2026 | H2.capture_ratio | 0.2722436322644482 | 0.2722436322644482 |
| hk_ai_openclaw_2026 | H2.strategy_excess | 0.519892959860899 | 0.519892959860899 |
| hk_ai_openclaw_2026 | H2.buy_hold_excess | 1.9096606797983533 | 1.9096606797983533 |
| hk_ai_openclaw_2026 | H3.n_second_order | 0 | 0 |
| hk_ai_openclaw_2026 | H4.first_flag | None | None |
| hk_ai_openclaw_2026 | H4.flag_lead_weeks_vs_peak | None | None |
| hk_ai_openclaw_2026 | H4.exit_value_to_end | None | None |
| hk_ai_openclaw_2026 | H4.exit_value_26w | None | None |
| hk_ai_openclaw_2026 | H4.flag_weeks | 0 | 0 |
| hk_ai_openclaw_2026 | H4.implied_growth_coverage_core | 1.0 | 1.0 |
| hk_ai_openclaw_2026 | H4.blocked_by_missing_expectations | False | False |

decision: REJECT: expected metric did not move in any case (HK still 0 flag weeks, US identical). Cause: supply flags are still gated by ig_pct>=0.8 on own history with crowd_min_history_weeks=26; HK IPO'd 2026-01-09 so the percentile only exists from ~07-10, after both lockups. Knob reverted (config unchanged). next: crowd_min_history_weeks=13

## iter 03 — iter 2 showed the 26w own-history requirement blocks every flag for Jan-2026 IPOs; halve it; expect HK ig_pct to exist from ~April (still no ETF launch, so HK flag may stay 0); check CN/US do not flag even earlier
override: ['crowd_min_history_weeks=13']

| case | metric | prev | now |
|---|---|---|---|
| us_space_2025 | H1.attention_source | news_count | news_count |
| us_space_2025 | H1.attention_source_used | wiki_views | wiki_views |
| us_space_2025 | H1.first_weak_to_strong | None | None |
| us_space_2025 | H1.lead_weeks_vs_breakout | None | None |
| us_space_2025 | H1.car13_after_event | None | None |
| us_space_2025 | H2.capture_ratio | 0.8181327530642376 | 0.8181327530642376 |
| us_space_2025 | H2.strategy_excess | 0.9684945099546889 | 0.9684945099546889 |
| us_space_2025 | H2.buy_hold_excess | 1.1837865020405134 | 1.1837865020405134 |
| us_space_2025 | H3.n_second_order | 0 | 0 |
| us_space_2025 | H4.first_flag | 2026-03-06 | 2026-03-06 |
| us_space_2025 | H4.flag_lead_weeks_vs_peak | 12 | 12 |
| us_space_2025 | H4.exit_value_to_end | -0.23024245030405455 | -0.23024245030405455 |
| us_space_2025 | H4.exit_value_26w | -0.18183849964756416 | -0.18183849964756416 |
| us_space_2025 | H4.flag_weeks | 12 | 12 |
| us_space_2025 | H4.implied_growth_coverage_core | 0.831360946745562 | 0.831360946745562 |
| us_space_2025 | H4.blocked_by_missing_expectations | False | False |
| cn_optical_2025 | H1.attention_source | news_count | news_count |
| cn_optical_2025 | H1.attention_source_used | turnover | turnover |
| cn_optical_2025 | H1.first_weak_to_strong | 2025-06-13 | 2025-06-13 |
| cn_optical_2025 | H1.lead_weeks_vs_breakout | -5 | -5 |
| cn_optical_2025 | H1.car13_after_event | 1.1480658767981091 | 1.1480658767981091 |
| cn_optical_2025 | H2.capture_ratio | 0.7453642191718207 | 0.7453642191718207 |
| cn_optical_2025 | H2.strategy_excess | 1.6302287214595534 | 1.6302287214595534 |
| cn_optical_2025 | H2.buy_hold_excess | 2.1871572038578826 | 2.1871572038578826 |
| cn_optical_2025 | H3.n_second_order | 66 | 66 |
| cn_optical_2025 | H3.best_lag | 0 | 0 |
| cn_optical_2025 | H3.lag1_minus_lag0 | -0.510414533249808 | -0.510414533249808 |
| cn_optical_2025 | H3.next_week_beta | -0.0491018759444499 | -0.0491018759444499 |
| cn_optical_2025 | H3.next_week_t | -1.9990492995446971 | -1.9990492995446971 |
| cn_optical_2025 | H4.first_flag | 2025-06-27 | 2025-06-27 |
| cn_optical_2025 | H4.flag_lead_weeks_vs_peak | 51 | 51 |
| cn_optical_2025 | H4.exit_value_to_end | -2.0045586469258563 | -2.0045586469258563 |
| cn_optical_2025 | H4.exit_value_26w | -1.3126682487937589 | -1.3126682487937589 |
| cn_optical_2025 | H4.flag_weeks | 35 | 35 |
| cn_optical_2025 | H4.implied_growth_coverage_core | 0.9888888888888889 | 0.9888888888888889 |
| cn_optical_2025 | H4.blocked_by_missing_expectations | False | False |
| hk_ai_openclaw_2026 | H1.attention_source | news_count | news_count |
| hk_ai_openclaw_2026 | H1.attention_source_used | wiki_views | wiki_views |
| hk_ai_openclaw_2026 | H1.first_weak_to_strong | None | None |
| hk_ai_openclaw_2026 | H1.lead_weeks_vs_breakout | None | None |
| hk_ai_openclaw_2026 | H1.car13_after_event | None | None |
| hk_ai_openclaw_2026 | H2.capture_ratio | 0.2722436322644482 | 0.2722436322644482 |
| hk_ai_openclaw_2026 | H2.strategy_excess | 0.519892959860899 | 0.519892959860899 |
| hk_ai_openclaw_2026 | H2.buy_hold_excess | 1.9096606797983533 | 1.9096606797983533 |
| hk_ai_openclaw_2026 | H3.n_second_order | 0 | 0 |
| hk_ai_openclaw_2026 | H4.first_flag | None | None |
| hk_ai_openclaw_2026 | H4.flag_lead_weeks_vs_peak | None | None |
| hk_ai_openclaw_2026 | H4.exit_value_to_end | None | None |
| hk_ai_openclaw_2026 | H4.exit_value_26w | None | None |
| hk_ai_openclaw_2026 | H4.flag_weeks | 0 | 0 |
| hk_ai_openclaw_2026 | H4.implied_growth_coverage_core | 1.0 | 1.0 |
| hk_ai_openclaw_2026 | H4.blocked_by_missing_expectations | False | False |

decision: REJECT: no card metric moved in any case. Halving the history alone cannot create an HK flag (no theme-ETF launch -> the ETF leg is always false), and with supply off there is no other path. Lesson: problems B/E interact (supply flag needs an ig_pct that needs history) but the one-knob rule tests them separately -> recorded as untested interaction in SUMMARY, not patched with more knobs. Knob reverted. next: problem C on CN: confirm_with_revisions=true (proxy: reported TTM revenue growth decelerating)

## iter 04 — problem C: CN flags 51w before the peak while earnings keep accelerating (exit -2.00); require decelerating reported TTM revenue growth to confirm crowding; expect CN exit_value up, US lead not much worse
override: ['confirm_with_revisions=true']

| case | metric | prev | now |
|---|---|---|---|
| us_space_2025 | H1.attention_source | news_count | news_count |
| us_space_2025 | H1.attention_source_used | wiki_views | wiki_views |
| us_space_2025 | H1.first_weak_to_strong | None | None |
| us_space_2025 | H1.lead_weeks_vs_breakout | None | None |
| us_space_2025 | H1.car13_after_event | None | None |
| us_space_2025 | H2.capture_ratio | 0.8181327530642376 | 0.8181327530642376 |
| us_space_2025 | H2.strategy_excess | 0.9684945099546889 | 0.9684945099546889 |
| us_space_2025 | H2.buy_hold_excess | 1.1837865020405134 | 1.1837865020405134 |
| us_space_2025 | H3.n_second_order | 0 | 0 |
| us_space_2025 | H4.first_flag | 2026-03-06 | 2026-03-06 |
| us_space_2025 | H4.flag_lead_weeks_vs_peak | 12 | 12 |
| us_space_2025 | H4.exit_value_to_end | -0.23024245030405455 | -0.23024245030405455 |
| us_space_2025 | H4.exit_value_26w | -0.18183849964756416 | -0.18183849964756416 |
| us_space_2025 | H4.flag_weeks | 12 | 2 |
| us_space_2025 | H4.implied_growth_coverage_core | 0.831360946745562 | 0.831360946745562 |
| us_space_2025 | H4.blocked_by_missing_expectations | False | False |
| cn_optical_2025 | H1.attention_source | news_count | news_count |
| cn_optical_2025 | H1.attention_source_used | turnover | turnover |
| cn_optical_2025 | H1.first_weak_to_strong | 2025-06-13 | 2025-06-13 |
| cn_optical_2025 | H1.lead_weeks_vs_breakout | -5 | -5 |
| cn_optical_2025 | H1.car13_after_event | 1.1480658767981091 | 1.1480658767981091 |
| cn_optical_2025 | H2.capture_ratio | 0.7453642191718207 | 0.7453642191718207 |
| cn_optical_2025 | H2.strategy_excess | 1.6302287214595534 | 1.6302287214595534 |
| cn_optical_2025 | H2.buy_hold_excess | 2.1871572038578826 | 2.1871572038578826 |
| cn_optical_2025 | H3.n_second_order | 66 | 66 |
| cn_optical_2025 | H3.best_lag | 0 | 0 |
| cn_optical_2025 | H3.lag1_minus_lag0 | -0.510414533249808 | -0.510414533249808 |
| cn_optical_2025 | H3.next_week_beta | -0.0491018759444499 | -0.0491018759444499 |
| cn_optical_2025 | H3.next_week_t | -1.9990492995446971 | -1.9990492995446971 |
| cn_optical_2025 | H4.first_flag | 2025-06-27 | 2025-07-25 |
| cn_optical_2025 | H4.flag_lead_weeks_vs_peak | 51 | 47 |
| cn_optical_2025 | H4.exit_value_to_end | -2.0045586469258563 | -1.77253814922266 |
| cn_optical_2025 | H4.exit_value_26w | -1.3126682487937589 | -0.9010187210775873 |
| cn_optical_2025 | H4.flag_weeks | 35 | 23 |
| cn_optical_2025 | H4.implied_growth_coverage_core | 0.9888888888888889 | 0.9888888888888889 |
| cn_optical_2025 | H4.blocked_by_missing_expectations | False | False |
| hk_ai_openclaw_2026 | H1.attention_source | news_count | news_count |
| hk_ai_openclaw_2026 | H1.attention_source_used | wiki_views | wiki_views |
| hk_ai_openclaw_2026 | H1.first_weak_to_strong | None | None |
| hk_ai_openclaw_2026 | H1.lead_weeks_vs_breakout | None | None |
| hk_ai_openclaw_2026 | H1.car13_after_event | None | None |
| hk_ai_openclaw_2026 | H2.capture_ratio | 0.2722436322644482 | 0.2722436322644482 |
| hk_ai_openclaw_2026 | H2.strategy_excess | 0.519892959860899 | 0.519892959860899 |
| hk_ai_openclaw_2026 | H2.buy_hold_excess | 1.9096606797983533 | 1.9096606797983533 |
| hk_ai_openclaw_2026 | H3.n_second_order | 0 | 0 |
| hk_ai_openclaw_2026 | H4.first_flag | None | None |
| hk_ai_openclaw_2026 | H4.flag_lead_weeks_vs_peak | None | None |
| hk_ai_openclaw_2026 | H4.exit_value_to_end | None | None |
| hk_ai_openclaw_2026 | H4.exit_value_26w | None | None |
| hk_ai_openclaw_2026 | H4.flag_weeks | 0 | 0 |
| hk_ai_openclaw_2026 | H4.implied_growth_coverage_core | 1.0 | 1.0 |
| hk_ai_openclaw_2026 | H4.blocked_by_missing_expectations | False | False |

decision: ACCEPT: (a) CN exit_value_to_end -2.00 -> -1.77, exit_26w -1.31 -> -0.90, first flag 4w later; (b) US lead (12w) and exit unchanged, flag weeks 12 -> 2; HK unchanged; (c) smoke 8/8. CN is still a large false positive: the revenue-deceleration proxy is not consensus revisions. next: problem D: attention_source=github_stars_delta (only HK has it; others fall back unchanged)

## iter 05 — problem D: HK wiki attention gives no weak->strong; OpenClaw diffusion started on GitHub; expect HK first_weak_to_strong to appear with positive lead; US/CN fall back to the same sources (no change)
override: ['attention_source=github_stars_delta']

| case | metric | prev | now |
|---|---|---|---|
| us_space_2025 | H1.attention_source | news_count | github_stars_delta |
| us_space_2025 | H1.attention_source_used | wiki_views | wiki_views |
| us_space_2025 | H1.first_weak_to_strong | None | None |
| us_space_2025 | H1.lead_weeks_vs_breakout | None | None |
| us_space_2025 | H1.car13_after_event | None | None |
| us_space_2025 | H2.capture_ratio | 0.8181327530642376 | 0.8181327530642376 |
| us_space_2025 | H2.strategy_excess | 0.9684945099546889 | 0.9684945099546889 |
| us_space_2025 | H2.buy_hold_excess | 1.1837865020405134 | 1.1837865020405134 |
| us_space_2025 | H3.n_second_order | 0 | 0 |
| us_space_2025 | H4.first_flag | 2026-03-06 | 2026-03-06 |
| us_space_2025 | H4.flag_lead_weeks_vs_peak | 12 | 12 |
| us_space_2025 | H4.exit_value_to_end | -0.23024245030405455 | -0.23024245030405455 |
| us_space_2025 | H4.exit_value_26w | -0.18183849964756416 | -0.18183849964756416 |
| us_space_2025 | H4.flag_weeks | 2 | 2 |
| us_space_2025 | H4.implied_growth_coverage_core | 0.831360946745562 | 0.831360946745562 |
| us_space_2025 | H4.blocked_by_missing_expectations | False | False |
| cn_optical_2025 | H1.attention_source | news_count | github_stars_delta |
| cn_optical_2025 | H1.attention_source_used | turnover | turnover |
| cn_optical_2025 | H1.first_weak_to_strong | 2025-06-13 | 2025-06-13 |
| cn_optical_2025 | H1.lead_weeks_vs_breakout | -5 | -5 |
| cn_optical_2025 | H1.car13_after_event | 1.1480658767981091 | 1.1480658767981091 |
| cn_optical_2025 | H2.capture_ratio | 0.7453642191718207 | 0.7453642191718207 |
| cn_optical_2025 | H2.strategy_excess | 1.6302287214595534 | 1.6302287214595534 |
| cn_optical_2025 | H2.buy_hold_excess | 2.1871572038578826 | 2.1871572038578826 |
| cn_optical_2025 | H3.n_second_order | 66 | 66 |
| cn_optical_2025 | H3.best_lag | 0 | 0 |
| cn_optical_2025 | H3.lag1_minus_lag0 | -0.510414533249808 | -0.510414533249808 |
| cn_optical_2025 | H3.next_week_beta | -0.0491018759444499 | -0.0491018759444499 |
| cn_optical_2025 | H3.next_week_t | -1.9990492995446971 | -1.9990492995446971 |
| cn_optical_2025 | H4.first_flag | 2025-07-25 | 2025-07-25 |
| cn_optical_2025 | H4.flag_lead_weeks_vs_peak | 47 | 47 |
| cn_optical_2025 | H4.exit_value_to_end | -1.77253814922266 | -1.77253814922266 |
| cn_optical_2025 | H4.exit_value_26w | -0.9010187210775873 | -0.9010187210775873 |
| cn_optical_2025 | H4.flag_weeks | 23 | 23 |
| cn_optical_2025 | H4.implied_growth_coverage_core | 0.9888888888888889 | 0.9888888888888889 |
| cn_optical_2025 | H4.blocked_by_missing_expectations | False | False |
| hk_ai_openclaw_2026 | H1.attention_source | news_count | github_stars_delta |
| hk_ai_openclaw_2026 | H1.attention_source_used | wiki_views | github_stars_delta |
| hk_ai_openclaw_2026 | H1.first_weak_to_strong | None | None |
| hk_ai_openclaw_2026 | H1.lead_weeks_vs_breakout | None | None |
| hk_ai_openclaw_2026 | H1.car13_after_event | None | None |
| hk_ai_openclaw_2026 | H2.capture_ratio | 0.2722436322644482 | 0.2722436322644482 |
| hk_ai_openclaw_2026 | H2.strategy_excess | 0.519892959860899 | 0.519892959860899 |
| hk_ai_openclaw_2026 | H2.buy_hold_excess | 1.9096606797983533 | 1.9096606797983533 |
| hk_ai_openclaw_2026 | H3.n_second_order | 0 | 0 |
| hk_ai_openclaw_2026 | H4.first_flag | None | None |
| hk_ai_openclaw_2026 | H4.flag_lead_weeks_vs_peak | None | None |
| hk_ai_openclaw_2026 | H4.exit_value_to_end | None | None |
| hk_ai_openclaw_2026 | H4.exit_value_26w | None | None |
| hk_ai_openclaw_2026 | H4.flag_weeks | 0 | 0 |
| hk_ai_openclaw_2026 | H4.implied_growth_coverage_core | 1.0 | 1.0 |
| hk_ai_openclaw_2026 | H4.blocked_by_missing_expectations | False | False |

decision: REJECT: HK still no weak->strong. Reason visible in the data: OpenClaw star velocity peaked in Dec-2025 (+42.5k stars, vs +34.0k Jan, +22.7k Feb) i.e. BEFORE the window opens at the 2026-01-09 IPO; inside the window the series only decays, so a weak->strong transition cannot occur. GitHub attention led price by >= 1 month, but this replay (window = listing) cannot score it. Knob reverted. next: attention_source=turnover

## iter 06 — wiki views give no transition in US/HK; abnormal turnover is an exchange-native attention proxy available everywhere; expect US/HK first_weak_to_strong to appear; CN unchanged (already turnover)
override: ['attention_source=turnover']

| case | metric | prev | now |
|---|---|---|---|
| us_space_2025 | H1.attention_source | github_stars_delta | turnover |
| us_space_2025 | H1.attention_source_used | wiki_views | turnover |
| us_space_2025 | H1.first_weak_to_strong | None | 2026-04-24 |
| us_space_2025 | H1.lead_weeks_vs_breakout | None | -46 |
| us_space_2025 | H1.car13_after_event | None | -0.1393450041945128 |
| us_space_2025 | H2.capture_ratio | 0.8181327530642376 | 0.8181327530642376 |
| us_space_2025 | H2.strategy_excess | 0.9684945099546889 | 0.9684945099546889 |
| us_space_2025 | H2.buy_hold_excess | 1.1837865020405134 | 1.1837865020405134 |
| us_space_2025 | H3.n_second_order | 0 | 0 |
| us_space_2025 | H4.first_flag | 2026-03-06 | 2026-03-06 |
| us_space_2025 | H4.flag_lead_weeks_vs_peak | 12 | 12 |
| us_space_2025 | H4.exit_value_to_end | -0.23024245030405455 | -0.23024245030405455 |
| us_space_2025 | H4.exit_value_26w | -0.18183849964756416 | -0.18183849964756416 |
| us_space_2025 | H4.flag_weeks | 2 | 2 |
| us_space_2025 | H4.implied_growth_coverage_core | 0.831360946745562 | 0.831360946745562 |
| us_space_2025 | H4.blocked_by_missing_expectations | False | False |
| cn_optical_2025 | H1.attention_source | github_stars_delta | turnover |
| cn_optical_2025 | H1.attention_source_used | turnover | turnover |
| cn_optical_2025 | H1.first_weak_to_strong | 2025-06-13 | 2025-06-13 |
| cn_optical_2025 | H1.lead_weeks_vs_breakout | -5 | -5 |
| cn_optical_2025 | H1.car13_after_event | 1.1480658767981091 | 1.1480658767981091 |
| cn_optical_2025 | H2.capture_ratio | 0.7453642191718207 | 0.7453642191718207 |
| cn_optical_2025 | H2.strategy_excess | 1.6302287214595534 | 1.6302287214595534 |
| cn_optical_2025 | H2.buy_hold_excess | 2.1871572038578826 | 2.1871572038578826 |
| cn_optical_2025 | H3.n_second_order | 66 | 66 |
| cn_optical_2025 | H3.best_lag | 0 | 0 |
| cn_optical_2025 | H3.lag1_minus_lag0 | -0.510414533249808 | -0.510414533249808 |
| cn_optical_2025 | H3.next_week_beta | -0.0491018759444499 | -0.0491018759444499 |
| cn_optical_2025 | H3.next_week_t | -1.9990492995446971 | -1.9990492995446971 |
| cn_optical_2025 | H4.first_flag | 2025-07-25 | 2025-07-25 |
| cn_optical_2025 | H4.flag_lead_weeks_vs_peak | 47 | 47 |
| cn_optical_2025 | H4.exit_value_to_end | -1.77253814922266 | -1.77253814922266 |
| cn_optical_2025 | H4.exit_value_26w | -0.9010187210775873 | -0.9010187210775873 |
| cn_optical_2025 | H4.flag_weeks | 23 | 23 |
| cn_optical_2025 | H4.implied_growth_coverage_core | 0.9888888888888889 | 0.9888888888888889 |
| cn_optical_2025 | H4.blocked_by_missing_expectations | False | False |
| hk_ai_openclaw_2026 | H1.attention_source | github_stars_delta | turnover |
| hk_ai_openclaw_2026 | H1.attention_source_used | github_stars_delta | turnover |
| hk_ai_openclaw_2026 | H1.first_weak_to_strong | None | None |
| hk_ai_openclaw_2026 | H1.lead_weeks_vs_breakout | None | None |
| hk_ai_openclaw_2026 | H1.car13_after_event | None | None |
| hk_ai_openclaw_2026 | H2.capture_ratio | 0.2722436322644482 | 0.2722436322644482 |
| hk_ai_openclaw_2026 | H2.strategy_excess | 0.519892959860899 | 0.519892959860899 |
| hk_ai_openclaw_2026 | H2.buy_hold_excess | 1.9096606797983533 | 1.9096606797983533 |
| hk_ai_openclaw_2026 | H3.n_second_order | 0 | 0 |
| hk_ai_openclaw_2026 | H4.first_flag | None | None |
| hk_ai_openclaw_2026 | H4.flag_lead_weeks_vs_peak | None | None |
| hk_ai_openclaw_2026 | H4.exit_value_to_end | None | None |
| hk_ai_openclaw_2026 | H4.exit_value_26w | None | None |
| hk_ai_openclaw_2026 | H4.flag_weeks | 0 | 0 |
| hk_ai_openclaw_2026 | H4.implied_growth_coverage_core | 1.0 | 1.0 |
| hk_ai_openclaw_2026 | H4.blocked_by_missing_expectations | False | False |

decision: REJECT: US transition now exists but LAGS the breakout by 46w (2026-04-24, 5w before the 05-29 peak) with CAR13 -0.14; HK still none (turnover baseline needs 8w after a Jan IPO). Turnover attention behaves as a late-cycle/crowding indicator, not an entry trigger (matches SPEC H1 'if fail' branch). Knob reverted. next: attention_half_life_weeks=4 (faster popularity -> earlier transitions?)

## iter 07 — transitions lag breakouts (CN -5w); an 8w EWM half-life smooths away the onset; expect CN lead_weeks_vs_breakout to rise toward >=0; US/HK wiki may start producing transitions
override: ['attention_half_life_weeks=4']

| case | metric | prev | now |
|---|---|---|---|
| us_space_2025 | H1.attention_source | turnover | news_count |
| us_space_2025 | H1.attention_source_used | turnover | wiki_views |
| us_space_2025 | H1.first_weak_to_strong | 2026-04-24 | None |
| us_space_2025 | H1.lead_weeks_vs_breakout | -46 | None |
| us_space_2025 | H1.car13_after_event | -0.1393450041945128 | None |
| us_space_2025 | H2.capture_ratio | 0.8181327530642376 | 0.8181327530642376 |
| us_space_2025 | H2.strategy_excess | 0.9684945099546889 | 0.9684945099546889 |
| us_space_2025 | H2.buy_hold_excess | 1.1837865020405134 | 1.1837865020405134 |
| us_space_2025 | H3.n_second_order | 0 | 0 |
| us_space_2025 | H4.first_flag | 2026-03-06 | 2026-03-06 |
| us_space_2025 | H4.flag_lead_weeks_vs_peak | 12 | 12 |
| us_space_2025 | H4.exit_value_to_end | -0.23024245030405455 | -0.23024245030405455 |
| us_space_2025 | H4.exit_value_26w | -0.18183849964756416 | -0.18183849964756416 |
| us_space_2025 | H4.flag_weeks | 2 | 2 |
| us_space_2025 | H4.implied_growth_coverage_core | 0.831360946745562 | 0.831360946745562 |
| us_space_2025 | H4.blocked_by_missing_expectations | False | False |
| cn_optical_2025 | H1.attention_source | turnover | news_count |
| cn_optical_2025 | H1.attention_source_used | turnover | turnover |
| cn_optical_2025 | H1.first_weak_to_strong | 2025-06-13 | 2025-06-13 |
| cn_optical_2025 | H1.lead_weeks_vs_breakout | -5 | -5 |
| cn_optical_2025 | H1.car13_after_event | 1.1480658767981091 | 1.1480658767981091 |
| cn_optical_2025 | H2.capture_ratio | 0.7453642191718207 | 0.7453642191718207 |
| cn_optical_2025 | H2.strategy_excess | 1.6302287214595534 | 1.6302287214595534 |
| cn_optical_2025 | H2.buy_hold_excess | 2.1871572038578826 | 2.1871572038578826 |
| cn_optical_2025 | H3.n_second_order | 66 | 66 |
| cn_optical_2025 | H3.best_lag | 0 | 0 |
| cn_optical_2025 | H3.lag1_minus_lag0 | -0.510414533249808 | -0.510414533249808 |
| cn_optical_2025 | H3.next_week_beta | -0.0491018759444499 | -0.0491018759444499 |
| cn_optical_2025 | H3.next_week_t | -1.9990492995446971 | -1.9990492995446971 |
| cn_optical_2025 | H4.first_flag | 2025-07-25 | 2025-07-25 |
| cn_optical_2025 | H4.flag_lead_weeks_vs_peak | 47 | 47 |
| cn_optical_2025 | H4.exit_value_to_end | -1.77253814922266 | -1.77253814922266 |
| cn_optical_2025 | H4.exit_value_26w | -0.9010187210775873 | -0.9010187210775873 |
| cn_optical_2025 | H4.flag_weeks | 23 | 23 |
| cn_optical_2025 | H4.implied_growth_coverage_core | 0.9888888888888889 | 0.9888888888888889 |
| cn_optical_2025 | H4.blocked_by_missing_expectations | False | False |
| hk_ai_openclaw_2026 | H1.attention_source | turnover | news_count |
| hk_ai_openclaw_2026 | H1.attention_source_used | turnover | wiki_views |
| hk_ai_openclaw_2026 | H1.first_weak_to_strong | None | None |
| hk_ai_openclaw_2026 | H1.lead_weeks_vs_breakout | None | None |
| hk_ai_openclaw_2026 | H1.car13_after_event | None | None |
| hk_ai_openclaw_2026 | H2.capture_ratio | 0.2722436322644482 | 0.2722436322644482 |
| hk_ai_openclaw_2026 | H2.strategy_excess | 0.519892959860899 | 0.519892959860899 |
| hk_ai_openclaw_2026 | H2.buy_hold_excess | 1.9096606797983533 | 1.9096606797983533 |
| hk_ai_openclaw_2026 | H3.n_second_order | 0 | 0 |
| hk_ai_openclaw_2026 | H4.first_flag | None | None |
| hk_ai_openclaw_2026 | H4.flag_lead_weeks_vs_peak | None | None |
| hk_ai_openclaw_2026 | H4.exit_value_to_end | None | None |
| hk_ai_openclaw_2026 | H4.exit_value_26w | None | None |
| hk_ai_openclaw_2026 | H4.flag_weeks | 0 | 0 |
| hk_ai_openclaw_2026 | H4.implied_growth_coverage_core | 1.0 | 1.0 |
| hk_ai_openclaw_2026 | H4.blocked_by_missing_expectations | False | False |

decision: REJECT: no H1 metric moved (CN lead still -5w; US/HK wiki still no transition). Third consecutive REJECT (iters 5, 6, 7) -> STOP per LOOP.md section 2. Accepted mechanisms: expectations_engine=auto (iter 1), confirm_with_revisions=true (iter 4).

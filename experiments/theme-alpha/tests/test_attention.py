import numpy as np
import pandas as pd

from theme_alpha.themes.attention import STRONG, WEAK, classify_states, detect_transitions, ewm_popularity

W = pd.date_range("2020-01-03", periods=60, freq="W-FRI")


def test_emerging_topic_goes_weak_then_strong_and_fires_once():
    rng = np.random.default_rng(0)
    counts = pd.DataFrame(rng.poisson(10, (60, 10)).astype(float), index=W, columns=[f"C{i}" for i in range(10)])
    counts["C9"] = 1.0
    counts.loc[W[40]:, "C9"] = np.linspace(2, 60, 20)            # emergence
    st = classify_states(ewm_popularity(counts, 4), window_weeks=20, slope_window_weeks=4)
    seq = st["C9"].iloc[38:].to_numpy()
    assert WEAK in seq and STRONG in seq
    assert np.argmax(seq == WEAK) < np.argmax(seq == STRONG)
    ev = detect_transitions(st, cooldown_weeks=26)
    assert (ev["concept_id"] == "C9").sum() == 1


def test_no_state_before_concept_exists():
    counts = pd.DataFrame({"A": [5.0] * 30, "B": [np.nan] * 15 + [5.0] * 15}, index=W[:30])
    st = classify_states(ewm_popularity(counts, 4), window_weeks=10, slope_window_weeks=3)
    assert st["B"].iloc[:15].isna().all()

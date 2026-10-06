import numpy as np

from theme_alpha.validation.cpcv import cpcv_splits, selection_cpcv_paths
from theme_alpha.validation.dsr_pbo import deflated_sharpe, pbo_cscv
from theme_alpha.validation.stats import nw_tstat


def test_nw_t_detects_mean_and_not_noise():
    rng = np.random.default_rng(1)
    assert nw_tstat(rng.normal(0.5, 1, 500))[1] > 5
    assert abs(nw_tstat(rng.normal(0.0, 1, 500))[1]) < 3


def test_dsr_penalises_many_trials():
    rng = np.random.default_rng(2)
    r = rng.normal(0.05, 1, 520)
    few = deflated_sharpe(r, rng.normal(0, 0.02, 2))
    many = deflated_sharpe(r, rng.normal(0, 0.05, 1000))
    assert many < few


def test_pbo_high_for_pure_noise_low_for_real_edge():
    # PBO of a single noise matrix is itself noisy; its average over seeds must be ~0.5
    vals = [pbo_cscv(np.random.default_rng(s).normal(0, 1, (520, 20)), 10) for s in range(12)]
    assert 0.35 < np.mean(vals) < 0.65
    edge = np.random.default_rng(3).normal(0, 1, (520, 20)); edge[:, 0] += 0.4
    assert pbo_cscv(edge, 10) < 0.1


def test_cpcv_purge_and_paths():
    splits = cpcv_splits(100, n_groups=5, k_test=2, purge=3, embargo=3)
    assert len(splits) == 10
    for train, test_g, groups in splits:
        test = np.concatenate([groups[g] for g in test_g])
        assert not set(train) & set(test)
    import pandas as pd
    R = pd.DataFrame(rng_cols := np.random.default_rng(4).normal(0, 1, (100, 3)))
    P = selection_cpcv_paths(R, n_groups=5, k_test=2, purge=3, embargo=3)
    assert P.shape == (100, 4) and not P.isna().any().any()

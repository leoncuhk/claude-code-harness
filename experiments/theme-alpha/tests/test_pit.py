import numpy as np
import pandas as pd

from theme_alpha.data.pit import MembershipIndex, alive_mask, basket_returns

W = pd.date_range("2020-01-03", periods=10, freq="W-FRI")


def _mi():
    concepts = pd.DataFrame({"concept_id": ["C1"], "name": ["x"], "created_at": [W[2]]})
    mem = pd.DataFrame({"concept_id": ["C1"] * 6, "stock_id": list("ABCDEF"),
                        "in_date": [W[2]] * 5 + [W[5]], "out_date": [pd.NaT] * 4 + [W[4], pd.NaT]})
    return MembershipIndex(mem, concepts, list("ABCDEFG"))


def test_members_asof_respects_in_out_and_creation():
    mi = _mi()
    assert mi.members("C1", W[1]).size == 0                    # before creation
    assert set(mi.members("C1", W[2])) == {0, 1, 2, 3, 4}       # E in, F not yet
    assert set(mi.members("C1", W[4])) == {0, 1, 2, 3}          # E left at W[4] (out exclusive)
    assert set(mi.members("C1", W[5])) == {0, 1, 2, 3, 5}      # F joined


def test_basket_uses_previous_week_membership():
    mi = _mi()
    R = pd.DataFrame(0.0, index=W, columns=list("ABCDEFG"))
    R.loc[W[5], "F"] = 1.0                                       # F joins at W[5]; must NOT count in week 5
    b = basket_returns(R, mi, min_members=3)
    assert np.isnan(b.iloc[2, 0])                                # formed at W[1]: concept not alive
    assert b.loc[W[5], "C1"] == 0.0
    assert b.loc[W[6], "C1"] == 0.0


def test_alive_mask_min_age():
    a = alive_mask(W, _mi(), min_age_weeks=2)
    assert not a.loc[W[3], "C1"] and a.loc[W[4], "C1"]

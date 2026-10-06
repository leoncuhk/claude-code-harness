"""Low-visibility links between stocks and themes (H3).

Default link = news co-mention (PKU, JBF 2025: strongest spillover channel in China).
Optional link = text similarity of '主营业务' embeddings (Hoberg-Phillips TNIC analogue) -> implement
`text_similarity_edges` in Phase 1 and feed it through the same `ThemeLinks` interface.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..data.pit import MembershipIndex


class ThemeLinks:
    def __init__(self, edges: pd.DataFrame, window_weeks: int = 52):
        e = edges[["week", "stock_a", "stock_b", "n"]]
        sym = pd.concat([e, e.rename(columns={"stock_a": "stock_b", "stock_b": "stock_a"})], ignore_index=True)
        self.edges = sym.sort_values("week").reset_index(drop=True)
        self._weeks = self.edges["week"].to_numpy()
        self.window = pd.Timedelta(weeks=window_weeks)

    def weights_at(self, t: pd.Timestamp, mi: MembershipIndex) -> pd.DataFrame:
        """stock_id, concept_id, w  for stocks linked to concept members but NOT members themselves.
        w is normalised per stock (sums to 1). Uses edges in (t - window, t] only."""
        lo = np.searchsorted(self._weeks, np.datetime64(t - self.window), side="right")
        hi = np.searchsorted(self._weeks, np.datetime64(t), side="right")
        sub = self.edges.iloc[lo:hi]
        if sub.empty:
            return pd.DataFrame(columns=["stock_id", "concept_id", "w"])
        agg = sub.groupby(["stock_a", "stock_b"], as_index=False)["n"].sum()
        asof = mi.asof_table(t)
        if asof.empty:
            return pd.DataFrame(columns=["stock_id", "concept_id", "w"])
        x = agg.merge(asof, left_on="stock_b", right_on="stock_id")[["stock_a", "concept_id", "n"]]
        x = x.groupby(["stock_a", "concept_id"], as_index=False)["n"].sum()
        member_keys = set(zip(asof["stock_id"], asof["concept_id"]))
        keep = [(a, c) not in member_keys for a, c in zip(x["stock_a"], x["concept_id"])]
        x = x.loc[keep]
        if x.empty:
            return pd.DataFrame(columns=["stock_id", "concept_id", "w"])
        x["w"] = x["n"] / x.groupby("stock_a")["n"].transform("sum")
        return x.rename(columns={"stock_a": "stock_id"})[["stock_id", "concept_id", "w"]]


def text_similarity_edges(*args, **kwargs) -> pd.DataFrame:
    """Phase 1 TODO: embed each company's annual-report business description (as of its ann_date),
    keep top-k cosine neighbours per stock per year, emit rows (week, stock_a, stock_b, n=similarity)."""
    raise NotImplementedError

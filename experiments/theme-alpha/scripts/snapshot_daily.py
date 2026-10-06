"""Daily PIT snapshot (cron, after market close): concept membership + ETF list. TEMPLATE (UNTESTED).

Starts the forward-collected PIT history that no vendor API gives for free. Output:
  data/snapshots/YYYYMMDD/em_concepts.parquet      (board name/code)
  data/snapshots/YYYYMMDD/em_concept_members.parquet (snapshot_date, concept_id, stock_id)
  data/snapshots/YYYYMMDD/etf_list.parquet
Then data/scd.snapshots_to_scd(...) converts the history into membership SCD.

Candidate AKShare calls (verify names/columns against the installed version):
  ak.stock_board_concept_name_em()            -> concept boards (Eastmoney)
  ak.stock_board_concept_cons_em(symbol=...)  -> constituents of one board
  ak.fund_etf_spot_em()                       -> ETF universe
"""
from __future__ import annotations

import datetime as dt
import os
import time

import pandas as pd


def main() -> None:
    import akshare as ak  # optional dependency [data]
    day = dt.date.today().strftime("%Y%m%d")
    out = f"data/snapshots/{day}"
    os.makedirs(out, exist_ok=True)
    boards = ak.stock_board_concept_name_em()
    boards.to_parquet(f"{out}/em_concepts.parquet", index=False)
    rows = []
    for name in boards["板块名称"]:
        try:
            cons = ak.stock_board_concept_cons_em(symbol=name)
            rows += [(day, name, code) for code in cons["代码"]]
        except Exception as e:  # keep going; log failures for the audit
            rows.append((day, name, f"__ERROR__{type(e).__name__}"))
        time.sleep(0.3)
    pd.DataFrame(rows, columns=["snapshot_date", "concept_id", "stock_id"]).to_parquet(
        f"{out}/em_concept_members.parquet", index=False)
    ak.fund_etf_spot_em().to_parquet(f"{out}/etf_list.parquet", index=False)


if __name__ == "__main__":
    main()

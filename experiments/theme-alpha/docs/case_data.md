# Case Lab 数据来源与 PIT 处理（v1.2，2026-10-06 构建）

`scripts/fetch_case_data.py` 用免费网络数据源构建 `data/cases/<case>/`。这些都是**原型级**数据源，可以支撑反馈循环，但不能用于确认性检验。确认性检验需要换成 PIT 数据商。

## 1. 数据源

| 数据 | 来源 | PIT 处理 | 已知问题 |
|---|---|---|---|
| 日行情（A/港/美） | 腾讯 `web.ifzq.gtimg.cn/appstock/app/fqkline`（前复权） | 周五收盘取周线；上市前为 NaN | 没有涨跌停、停牌标记，A 股封板周未设 NaN（与 CLAUDE.md 规则 7 有偏差） |
| A 股财报 | 东方财富 `RPT_F10_FINANCE_MAINFINADATA`、现金流量表、资产负债表 | 按 `NOTICE_DATE` 做 as-of 连接；超过法定期限的日期改用期限日 | 数值为最新版本，可能包含重述 |
| 美股财报 | 东方财富 `RPT_USF10_FN_GMAININDICATOR`、`RPT_USSK_FN_CASHFLOW`、`RPT_USF10_FN_BALANCE` | 供应商会把旧期间的日期改写为后续重复披露它的那份报告的日期（例如 2025Q2 被标成 2026-08-10）。超过 10-Q 45+5 天或 10-K 90+15 天的日期，一律改用期限日 | 利润率用净利润率（源数据没有营业利润）；股数 = 净利润 / EPS |
| 港股财报 | 东方财富 `RPT_HKF10_FN_MAININDICATOR` | **没有公告日**，按上市规则期限推算：年报 +90 天，中报 +61 天，季报 +45 天 | 保守估计，实际发布更早（MiniMax 2025 年报实际 03-02 发布，这里按 03-31 处理） |
| 隐含预期 | `TwoStageReverseDCF`（FCF）、`SalesDrivenReverseDCF`（收入）、`auto` | 周收盘价 × 当时已公告的 TTM 财务数据 | 收入引擎的当前利润率截断在 [-100%, 60%]，ASTS 这类利润率约 -900% 的公司会无解 |
| ETF 上市（美） | Nasdaq 名称检索（space/satellite/orbit…）+ 腾讯首个交易日 | 上市日 = 首个交易日 | 只能检索到今天仍存续的 ETF（生存偏差） |
| ETF 上市（A 股/港股主题） | 天天基金基金目录。两种映射规则：① 名称规则，上市即计入；② 持仓规则，前十大持有 ≥ N 只核心股时计入 | 持仓规则在季报公开后才计入，按季末 +25 天 | 只覆盖 A 股上市的 ETF，不含港股上市 ETF |
| 第二梯队 | 主题 ETF 最近一期**已公开**的前十大持仓，剔除核心股 | 不在持仓集合内的周，收益设为 NaN | 美股没有 PIT 持仓源，第二梯队为空，H3 无法评估 |
| 注意力：维基 | Wikimedia pageviews REST（日度） | 按发生周计入 | 共享出口 IP 频繁 429，失败的条目记在 `meta.wiki_views_by_article` |
| 注意力：成交额异常 | 腾讯日线：成交量 × 收盘价 | 当周成交额 ÷ 此前 26 周中位数（至少 8 周历史） | 新股前 8 周没有基线 |
| 注意力：GitHub 星标 | OSSInsight 星标历史（按月采样的累计数） | 两次采样之间沿用**最近已知速率**，不向未来样本插值 | 月度分辨率 |
| 注意力：新闻 | — | — | **不可用**：GDELT 每次请求都返回 429，东方财富搜索接口返回无关结果 |
| 供给事件 | 案例 yaml 的 `supply_events`（IPO、解禁、指数纳入） | 均为事前公告的时间表 | SpaceX 的 IPO 日期在招股书公开前并不确知，提前 8 周窗口偏乐观 |

## 2. 与原始规格的偏差

1. **`news_count` 不存在。**`attention_source=news_count` 会按 `news_count → wiki_views → turnover` 的顺序回退，卡片中的 `H1.attention_source_used` 记录实际使用的源。
2. **`confirm_with_revisions` 是代理指标。**没有一致预期数据，改用"已公告 TTM 收入增速在放缓"（核心股中位数，13 周增速低于 13 周前的 13 周增速）。
3. **A 股封板周未设 NaN。**周频案例诊断受影响较小，但 H2/H3 的系统检验必须补上这一处理。
4. **案例数据与原始缓存。**两者都在 `data/` 下，不入库（`.gitignore`）。在同一份缓存上重跑 `fetch_case_data.py` 结果完全可复现。

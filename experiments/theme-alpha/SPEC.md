# SPEC — theme-alpha：主题生命周期错定价的可验证研究与实施

版本 v1.1（2026-10）｜市场：A 股为主；Case Lab 覆盖美股、港股｜执行者：Claude Code（规则见 `CLAUDE.md`，反馈循环见 `LOOP.md`）

> v1.1 变更：新增 §11 Case Lab（三个真实主题案例 + 反馈循环）；样本划分增加"主题留出"与"前向"两层，因为开发案例落在原时间留出期内。

---

## 0. 一页纸

**要回答的问题。**主题投资在 A 股能否在扣除成本后产生可重复的超额收益？如果能，钱来自主题生命周期的哪一段？

**投资论点。**主题会经历四个阶段：萌芽 → 扩散 → 拥挤 → 退潮。错定价在两端方向相反：

- 早期，信息模糊、关注有限，市场反应不足，价格扩散得慢，因而存在可交易的动量和溢出。
- 末期，市场过度外推。ETF 扎堆发行、隐含预期顶到历史高位，随后收益反转。

本项目把这条链拆成四个可证伪的假设，各自独立检验。最后只把通过检验的部分组装成一个跟踪误差受控的长仓主题叠加策略（overlay），借鉴 BlackRock THRO 的架构。

**差异化。**行业里的主题轮动系统（THRO、MSCI 情绪轮动）在择时上都收敛到"注意力 + 动量 + 过热约束"，但没有一家用隐含预期（反向 DCF）做估值约束。H4 把这一层补上。

| 假设 | 生命周期阶段 | 问题 | 主检验 | 关键门槛（预注册） |
|---|---|---|---|---|
| H1 | 萌芽 | 注意力"弱→强"跃迁是否领先主题篮子超额？ | 事件研究 + 安慰剂 | t ≥ 3，安慰剂 p < 0.01，扣费 CAR > 0 |
| H2 | 扩散 | 概念动量在论文发表（2022）后是否仍有效？ | 分段多空 + Fama-MacBeth | 发表后 t ≥ 2，长仓净 IR ≥ 0.3，FM t ≥ 2 |
| H3 | 扩散 | 新闻共现但不在概念板块里的股票，是否滞后跟涨？ | 周度 Fama-MacBeth + 十分位多空 | FM t ≥ 3，扣费多空 > 0 |
| H4 | 拥挤 | "ETF 发行 × 隐含增速高分位"过滤能否降低轮动的相对回撤？ | 选择型 CPCV 配对比较 | 相对回撤中位降幅 ≥ 20%，≥ 70% 路径改善 |

**成功的定义**分三级（详见 §3）：

- 研究成功：单个假设在验证期通过门槛。
- 策略成功：组合在一次性留出期达到净 IR ≥ 0.5、DSR ≥ 0.95、PBO ≤ 0.2。
- 实盘成功：13 周模拟盘与回测一致。

**Claude Code 的第一步**是 `make setup && make test && make smoke`。冒烟测试是"已知答案"测试：在植入效应的合成数据上，四个假设必须 PASS；在无效应的合成数据上，必须 FAIL。当前脚手架已通过（见 §10）。

---

## 1. 领域关键项目与逻辑（本项目借用什么、不借用什么）

| # | 项目 | 层 | 核心逻辑 | 本项目借用 | 不借用 / 注意 |
|---|---|---|---|---|---|
| 1 | **BERTrend**（rte-france；FuturED@ACL 2024；`pip install bertrend`） | 发现 | 按时间切片跑 BERTopic，余弦相似度 ≥ 0.7 跨片合并；热度 = 累计文档数，无更新时按 e^(-λΔt²) 衰减；滑窗内取第 10/50 百分位，结合斜率判定噪声/弱/强；零样本定向监控阈值 0.4–0.6 | 分类规则的原生实现（`themes/attention.py`）；零样本计数（`themes/zero_shot.py`）；E1 新主题提前量探索 | 累计热度不作为主变量（老的大主题会永远"强"），改为 EWM 预注册；LLM 解读不进入信号；包要求 Python ≥ 3.13，需独立环境（`themes/bertrend_bridge.py`） |
| 2 | **Zve 等**：离群点→新主题（LREC 2026；arXiv 2609.29183） | 发现 | 最初被判为噪声的部分文档会成为新主题的奠基成员；只用发布时信息即可预测，几何特征主导 | E1 的升级方向：嵌入空间离群点几何特征 | 只验证了"主题形成"，未验证收益 |
| 3 | **Bybee-Kelly-Manela-Xiu**（JF 2024）；**Narrative Asset Pricing**（RFS 2023） | 发现/因子 | 80 万篇 WSJ 文章 → 主题注意力份额，可追踪经济活动、预测大盘；LDA + IPCA + group lasso 构造叙事因子，样本外夏普优于特征因子 | `attention_share` 的定义；"主题即风险因子"用于归因 | 语料不同；本项目不估计因子模型（Phase 6） |
| 4 | **Bloomberg 业绩会主题本体**（arXiv 2507.07906） | 发现 | LLM 智能体抽取主题并构建层级本体（141 份纪要 → 3200 节点） | 未来可替代概念描述文本 | LLM 参数化前视；A 股业绩会稀缺 |
| 5 | **MSCI 主题暴露标准 / Strategy Exposure**（2026-07 方法论改用 LLM） | 映射 | 收入数据 + NLP/LLM 衡量公司与主题的经济联系；覆盖中国 A 股全指 | "暴露 = 经济联系"的定义；概念描述文本的写法 | 付费数据，不依赖 |
| 6 | **Hoberg-Phillips TNIC**（JPE 2016）；**Text-Based Industry Momentum**（JFQA 2018） | 映射/择时 | 年报产品描述相似度构建动态同行；不共享 SIC 的低可见度同行受冲击后动量大，SIC 同行动量小且短 | H3 的理论依据；`text_similarity_edges`（A 股用"主营业务"段落） | 美国数据库可用于 Phase 6 |
| 7 | **THEME**（arXiv 2508.16936） | 映射 | 层级对比学习微调股票嵌入，主题检索优于通用 LLM | Phase 6 映射升级 | 需要主题 ETF 成分作训练标签 |
| 8 | **新闻共现动量溢出**（北大，JBF 2025） | 映射/择时 | A 股新闻共现关联的动量溢出最强，能识别更多跨行业联系 | H3 的默认链接 | — |
| 9 | **Concept links and return momentum**（JBF 2022） | 择时 | A 股概念动量不被风险因子、个股动量、行业动量解释；概念越模糊、关注越少、高情绪之后越强 | H2 的复制与发表后衰减检验 | 不得使用回填的概念历史 |
| 10 | **BlackRock THRO** | 全栈 | 新闻/业绩会/券商篮子 → AI 主题；兴趣 + 动量 + 估值择时；盈利增长筛选；跟踪误差 3–5% | `portfolio/rotation.py` 的跟踪误差预算 overlay 架构 | 业绩仅 3 年，前两大持仓占约 17%，需归因 |
| 11 | **MSCI 多主题情绪轮动** | 择时 | 22 个子主题；文章数 + 情绪 + 热度变化 → 月度权重 | 注意力变化作为择时特征（扩展） | 指数商自报业绩 |
| 12 | **Morningstar 主题轮动研究**（2026-02） | 择时 | 主题超额持续性弱；动量轮动改善风险调整收益，但换手高 | H4 基准轮动设定；成本必须计入 | — |
| 13 | **Ben-David 等**（RFS 2023） | 拥挤 | 专业化 ETF 发行前成分股上涨，发行后 5 年风险调整约 -30% | H4 拥挤信号（ETF 发行） | — |
| 14 | **Mauboussin & Rappaport, Expectations Investing** | 估值 | 从股价反推隐含预期，押注预期修正 | `signals/expectations.py`；篮子隐含增速分位 | 负 FCF 需 NOPAT 回退（Phase 1） |
| 15 | **FINSABER**（KDD 2026；`pip install finsaber`） | 验证 | 20 年、宽股票池，控制生存、前视、数据窥探偏差；可记 LLM 成本 | 偏差清单；若引入 LLM 策略则用其做外部基准 | — |
| 16 | **LLM 前视研究**（FinCAD 2026；BlindTrade, ICLR-W 2026；Alpha Illusion 2026） | 验证 | LLM 会记住历史价格；静态基准优的模型实盘更差 | `llm_in_signal_path: false` 硬规则 | — |
| 17 | **AFML CPCV/DSR/PBO**（你现有框架）；**skfolio CombinatorialPurgedCV** | 验证 | 组合式净化交叉验证产生多条样本外路径 | `validation/` 合同不变即可替换 | — |
| 18 | **RD-Agent(Q) / Qlib**（NeurIPS 2025） | 因子迭代 | 研究-开发双阶段智能体，因子与模型联合优化 | Phase 6：把已通过的信号作为种子因子 | 每次自动迭代都计入 trials（DSR） |
| 19 | **anthropics/financial-services**（Claude 插件，DCF skill） | 工具 | 近 700 行的 DCF 建模约束 | 用其约束清单审查反向 DCF 实现 | — |
| 20 | **Tushare / AKShare / JoinQuant** | 数据 | 见 §4 | — | **Tushare `ths_member` 的 in_date/out_date 文档标注"暂无"→ 不是 PIT**；申万 `index_member` 有 in/out date；DC 概念板块 `dc_index` 数据最早 2024-12-20 |

---

## 2. 投资论点与逻辑链

```
萌芽 ──────────────► 扩散 ─────────────────────► 拥挤 ─────────────► 退潮
注意力从低位加速      价格动量延续；向低可见度        ETF扎堆发行；            反转
(信息模糊，反应不足)   关联股溢出(信息扩散慢)          隐含增速顶到历史高位       (外推修正)
   H1 入场触发          H2 主信号 / H3 卫星策略          H4 退出/回避过滤
```

**为什么 A 股可能有效：**

- 散户主导，注意力有限。
- 概念标签实时生成，例如"口罩"概念在 2020-04-04 就被创建，本身就是现成的主题标注。
- 做空受限，高估难以被纠正。

**为什么可能失效：**

- PIT 概念成分不可得，回测会系统性高估。
- 效应发表后被套利（McLean-Pontiff 型衰减）。
- 主题轮动换手高，成本吞噬收益。
- 涨跌停导致无法成交。
- 政策冲击带来体制切换。

这些都写成了检验条件或红旗（§4、§9）。

**实施形态**为长仓 overlay：

`total = 基准 + α·(主题组合 − 基准) − 成本`，α ∈ [0, 1]，按目标跟踪误差 4% 每次调仓重设。

α ≤ 1 意味着组合是基准与长仓主题篮子的混合，天然满足 A 股的做空约束。

---

## 3. 成功的定义（预注册，冻结后不得修改）

### L1 研究成功（单个假设）

在验证期（2021-01 至 2023-12）通过 `configs/hypotheses/h*.yaml` 中的全部 gates。新信号的门槛是 HLZ t ≥ 3；复制已发表效应（H2）的门槛是 t ≥ 2。

### L2 策略成功（组合，留出期一次性评估）

组合的定义取决于哪些假设通过（见下方决策矩阵）。全部满足才进入实盘：

| 指标 | 门槛 |
|---|---|
| 扣费后年化信息比率（相对基准） | ≥ 0.5 |
| Deflated Sharpe Ratio（试验次数取 `reports/trials.jsonl` 中该策略族的全部记录） | ≥ 0.95 |
| PBO（预注册参数网格，CSCV） | ≤ 0.2 |
| 最大相对回撤 | ≤ 8% |
| 年化交易成本 / 年化毛超额 | ≤ 1/3 |
| 已实现跟踪误差 | 2%–6% |

### L3 实盘成功（13 周模拟盘）

- 实时快照重建的信号与回测信号的秩相关 ≥ 0.95。
- 已实现超额落在回测分布的 95% 区间内。
- 实测滑点不高于假设值。

**止损：**实盘 26 周累计超额低于预期 -2σ，即停止。

### 决策矩阵

| 结果 | 动作 |
|---|---|
| H2 ✓，H4 ✓ | overlay v1：概念动量轮动 + 拥挤过滤 |
| 另外 H1 ✓ | v1.1：用注意力跃迁作为入场触发或加权 |
| H3 ✓ | 独立卫星策略（周频、高换手），先做容量与冲击成本评估 |
| H2 ✗，H1 ✓ | 仅用 H1 事件驱动的 overlay |
| 全部 ✗，且功效 ≥ 0.8 | 记录负结果，停止主题择时；反向 DCF 模块转用于个股研究 |
| ✗ 但功效 < 0.8 | 结论为"不确定"。延长数据（前向快照积累）后重测，不得改阈值 |

---

## 4. 数据与时点（PIT）纪律

### 4.1 数据源与 PIT 处理

| 数据 | 首选来源 | PIT 依据 | 风险 | 处理 |
|---|---|---|---|---|
| 日行情、复权、停牌、涨跌停 | Tushare `daily` / `adj_factor` / `suspend_d` / `stk_limit`；`stock_basic` 含退市 | 交易日 | 生存偏差 | 股票池必须含退市股；周末停牌或封板 → 当周收益 NaN |
| 基准 | 等权全市场，或中证全指 / 中证 800 | — | — | `configs/base.yaml: benchmark` |
| 概念列表与创建日 | 同花顺 `ths_index` 或东财板块 | `created_at` | 指数历史回填 | 只使用 `created_at` 之后、且满足形成窗的数据（`alive_mask(min_age)`） |
| **概念成分（关键）** | ① JoinQuant 按日期查询的历史成分；② 经核验的 SCD 导出；③ 前向快照 `snapshot_daily.py` → `data/scd.snapshots_to_scd` | in_date / out_date | Tushare `ths_member` 无纳入/剔除日期 | 若只能用③，H2/H3/H4 仅能用快照开始后的数据；H2 可先在概念指数层面检验 |
| 新闻 | Tushare `news` / `major_news` 等 | `published_at` | 历史深度不足 | Phase 1 审计覆盖率；不足则调整切分（必须在冻结前） |
| 财务 | `income` / `cashflow` / `balancesheet` / `fina_indicator` | `ann_date` | 用了报告期而非公告日 | 只按 `ann_date` 做 as-of 连接 |
| ETF | `fund_basic(market='E')` 的 list_date、业绩基准 | `list_date` | 主题映射主观 | 用同一个零样本匹配器把 ETF 名称/基准映射到概念 |
| 行业（控制变量） | 申万 `index_member` | in_date / out_date | — | H2/H3 稳健性控制 |

### 4.2 PIT 规则

- **R1** 周频面板，时间戳为当周最后一个交易日。t 期形成的信号只能交易 t+1 期收益。
- **R2** 篮子收益用 t-1 期的成分计算 t 期收益（`basket_returns`）。
- **R3** 概念在 `created_at` 之前不存在：没有注意力、没有收益，也不进入排序。
- **R4** 财务数据按 `ann_date` 连接；TTM 只能使用当时已公告的报表。
- **R5** 链接权重只使用 (t - 52 周, t] 的共现数据。
- **R6** 嵌入模型发布日期之前的样本标记为"可能被污染"。留出期必须完全晚于发布日期。
- **R7** LLM 不进入回测信号路径。
- **R8** 冻结之后，切分、阈值、参数网格一律不改。

### 4.3 样本切分（`configs/base.yaml`）

| 区间 | 时间 | 用途 |
|---|---|---|
| 发现期 | 2016-01 至 2020-12 | 允许探索 |
| 验证期 | 2021-01 至 2023-12 | 预注册的确认性检验 |
| 留出期 | 2024-01 至 2026-06 | 每个假设只能评估一次 |

H2 另按论文发表日 2022-01-01 切成"发表前/发表后"两段。

**v1.1 补充：**三个开发案例（§11）落在留出期内。评估留出期时，必须同时报告"剔除开发案例主题"与"不剔除"两个版本，并以前者为准。另设两层样本外：一是按注意力规则（不看收益）选出的**主题留出**；二是 2026-10 起的**前向模拟盘**。

---

## 5. 目录结构

```
theme-alpha/
├── CLAUDE.md                       # Claude Code 操作规则（必读）
├── SPEC.md                         # 本文件
├── LOOP.md                         # 反馈循环协议（Case Lab）
├── cases/                          # 开发案例：us_space_2025 / cn_optical_2025 / hk_ai_openclaw_2026
├── Makefile                        # setup / test / smoke / power / audit / freeze / h1..h4
├── pyproject.toml                  # 依赖；可选 [data] [nlp] [cv] [dev]
├── configs/
│   ├── base.yaml                   # 市场、切分、成本、隐含预期引擎、文本参数
│   ├── case_lab.yaml               # 反馈循环：frozen（不可改）与 mechanisms（每轮改一个）
│   ├── hypotheses/h1.yaml … h4.yaml  # 每个假设的参数与 gates（预注册）
│   └── prereg.lock                 # make freeze 生成的哈希
├── src/theme_alpha/
│   ├── data/
│   │   ├── bundle.py               # DataBundle + validate_bundle（唯一的研究输入对象）
│   │   ├── pit.py                  # MembershipIndex、basket_returns、alive_mask
│   │   ├── scd.py                  # 每日快照 → SCD（前向 PIT 收集）
│   │   ├── weekly.py               # 日 → 周转换、事件日期对齐
│   │   └── providers/
│   │       ├── base.py             # Market/Concept/News/Fundamental/ETF Provider 协议
│   │       ├── synthetic.py        # 植入/无效应的合成市场（已知答案测试）
│   │       └── tushare_provider.py # 模板（Phase 1 实现）
│   ├── themes/
│   │   ├── attention.py            # BERTrend 规则原生实现：EWM/经典热度、状态分类、跃迁事件
│   │   ├── zero_shot.py            # 零样本：新闻 → 概念文档数（仅当时存在的概念）
│   │   ├── linkage.py              # 共现链接权重（排除成员）；文本相似链接（TODO）
│   │   └── bertrend_bridge.py      # 与 BERTrend 包的文件交换（E1 探索）
│   ├── signals/
│   │   ├── crowding.py             # ETF 发行计数、篮子隐含增速、历史分位、拥挤标记
│   │   └── expectations.py         # 反向 DCF：FCF 两阶段 + 收入驱动（亏损公司）+ 外部计算器适配器
│   ├── portfolio/rotation.py       # 长仓主题 overlay，跟踪误差预算
│   ├── validation/
│   │   ├── stats.py                # NW t、Fama-MacBeth、块自助、IR、MDD
│   │   ├── cpcv.py                 # 选择型 CPCV 与路径重组
│   │   ├── dsr_pbo.py              # Deflated Sharpe、PBO (CSCV)
│   │   ├── trials.py               # 只追加的试验日志
│   │   └── prereg.py               # 冻结哈希、留出期一次性锁
│   ├── cases/                      # spec.py（案例定义）、replay.py（逐周回放）、diagnostics.py（固定诊断）
│   └── hypotheses/
│       ├── common.py               # HypothesisResult、gates 评估
│       ├── registry.py
│       ├── h1_attention_leadlag.py
│       ├── h2_concept_momentum_decay.py
│       ├── h3_spillover.py
│       └── h4_crowding_filter.py
├── scripts/
│   ├── smoke_test.py               # 植入 → PASS，无效应 → FAIL
│   ├── case_loop.py                # 反馈循环的一轮：回放全部开发案例，输出 prev→now 对照卡片
│   ├── fetch_case_data.py          # 模板：构建 data/cases/<case>/
│   ├── select_holdout_themes.py    # 模板：只用注意力数据按规则选主题留出
│   ├── power_analysis.py           # 功效与检验水平（可用真实数据校准）
│   ├── run_hypothesis.py           # 运行单个假设（含预注册检查、留出锁、试验日志）
│   ├── data_audit.py               # 覆盖率 + PIT 红旗
│   ├── build_bundle.py             # Phase 1 模板：provider → DataBundle
│   ├── snapshot_daily.py           # 每日快照（cron），积累前向 PIT 成分
│   └── freeze_prereg.py
├── tests/                          # 单元测试（PIT、注意力、统计、反向 DCF、SCD）
├── data/{raw,snapshots,processed}/ # 不入库
└── reports/                        # 结果 JSON、trials.jsonl、汇总报告
```

---

## 6. 数据接口

### 6.1 `DataBundle`（周频；所有假设只接收它）

| 字段 | 类型与形状 | 语义 / PIT 约束 |
|---|---|---|
| `stock_ret` | DataFrame[week × stock_id]，float | 当周复利总收益；NaN = 停牌或封板不可交易；含退市股 |
| `bench_ret` | Series[week] | 基准周收益；索引与 `stock_ret` 一致 |
| `concepts` | concept_id, name, created_at, description | `created_at` 为首次公开日期；description 用于零样本匹配 |
| `membership` | concept_id, stock_id, in_date, out_date | 历史 SCD；out_date 为 NaT 表示仍在；in_date ≥ created_at |
| `theme_docs` | week, concept_id, n_docs | 仅包含当周已存在的概念；由 `zero_shot.theme_doc_counts` 生成 |
| `comention` | week, stock_a, stock_b, n | 当周同一篇新闻中共同出现的股票对计数 |
| `etf_launches` | list_date, etf_id, concept_id | ETF 上市日与映射的概念 |
| `implied_growth` | DataFrame[week × stock_id] | 当周价格 × 当时已公告财务 → 反向 DCF 隐含增速 |

`validate_bundle` 每次运行前都会检查：索引排序与对齐、必需列、out < in 的行、成员早于概念创建（回填嫌疑）、晚于面板的事件、收益量级。

### 6.2 Provider 协议（`data/providers/base.py`）

| 协议 | 方法 | 要点 |
|---|---|---|
| `MarketProvider` | `daily_returns`, `benchmark` | 必须含退市股；`tradable` 字段 |
| `ConceptProvider` | `concepts`, `membership_scd` | 成分必须是历史 SCD，不得用今日快照 |
| `NewsProvider` | `news` | `published_at`、`stock_ids` 列表 |
| `FundamentalProvider` | `fundamentals_pit` | 以 `ann_date` 为键 |
| `ETFProvider` | `etf_list`, `etf_shares` | list_date、业绩基准文本 |

### 6.3 外部组件适配

- **隐含预期**：`ImpliedExpectationsEngine.implied(price, shares, net_debt, fcf_ttm, wacc, terminal_g, years) -> ImpliedResult(implied_growth, status)`。默认实现为 `TwoStageReverseDCF`；接入现有计算器用 `ExternalReverseDCF("pkg.module.implied_growth")`。
- **CPCV**：`selection_cpcv_paths(returns_by_config, n_groups, k_test, purge, embargo) -> DataFrame[week × path]`。可替换为你现有的 AFML 实现或 skfolio。

---

## 7. 信号定义

| 信号 | 定义 |
|---|---|
| 篮子收益 | `B[k,t]` = t-1 期成分在 t 期收益的等权均值；有效成员 ≥ 5 |
| 篮子超额 | `X[k,t] = B[k,t] − bench[t]` |
| EWM 热度（主） | `p[t] = p[t−1]·e^(−ln2/h) + n[t]`，h = 8 周 |
| 经典热度（次） | 有文档则累加；无文档则 `p[t] = p[t−1]·e^(−λ·Δt²)`（BERTrend 原式） |
| 状态 | 在 26 周窗口内汇总所有概念的热度，取 P10、P50。p < P10 为噪声；P10 ≤ p ≤ P50 且 6 周斜率 > 0 为弱信号；p > P50 为强信号 |
| H1 事件 | t-1 为弱、t 为强，且此前 26 周内从未为强 |
| 概念动量 | `S[k,t]` = 过去 J 周的 X 之和；概念存在时间须 ≥ J+1 周 |
| 链接权重 | `w[i,k] = Σ_{j∈成员_k(t)} n_ij / Σ_k(…)`，只算非成员 i，窗口 52 周 |
| 溢出信号 | `s[i,t] = Σ_k w[i,k]·X[k,t]` |
| 拥挤标记 | 近 26 周有 ETF 上市，且篮子隐含增速中位数 ≥ 其自身历史第 80 百分位（历史 ≥ 52 周） |
| overlay | `total = bench + α·(theme − bench) − cost`，`α = min(1, TE*/σ̂_active(52w))` |

---

## 8. 四个假设的检验协议

每个假设的实现在 `src/theme_alpha/hypotheses/h*_*.py`，参数与门槛在对应的 yaml 中。

### H1 注意力跃迁领先收益

- **H0**：跃迁后 13 周的超额收益（CAR）与同一概念随机日期的 CAR 没有差异。
- **构造**：零样本文档数 → EWM 热度 → 状态 → 跃迁事件。CAR 取事件后第 1 至 13 周的篮子超额之和；有效观测须 ≥ 80%。
- **检验**：
  - 按事件周聚合后计算 NW t（滞后 = H）。
  - 安慰剂：在同一概念中远离真实事件（> H 周）的日期随机抽取 500 次，p 值 = 安慰剂均值 ≥ 实际均值的比例。
  - 扣除一次往返成本。
- **门槛**：n_events ≥ 30；t ≥ 3；安慰剂 p < 0.01；扣费 CAR > 0。
- **稳健性（报告，计入 trials）**：经典热度；h ∈ {4, 12}；H ∈ {4, 26}；按概念模糊度和关注度分组。
- **若失败**：注意力可能只是同步指标而非领先指标。H1 降级为风控用途（注意力份额过高 → 拥挤），不作入场信号。

### H2 概念动量在发表后的存续

- **H0**：发表后多空均值 ≤ 0。
- **构造**：每 4 周调仓。按过去 4 周的篮子超额排序，取前 1/5 与后 1/5 的概念，持有 4 周。另外计算长仓腿（前 1/5 − 基准），并按实测换手扣费。
- **检验**：
  - 发表前、后两段分别计算 NW t，报告衰减比 = 1 − 发表后均值 / 发表前均值。
  - 发表后的股票层面 Fama-MacBeth：未来 4 周超额 ~ 概念动量 + 自身 4 周动量。
- **门槛**：发表后均值 > 0；t ≥ 2；长仓净 IR ≥ 0.3；FM 概念动量 t ≥ 2。
- **稳健性**：J ∈ {4, 13, 26}，K ∈ {4, 13}；加入申万行业动量控制；剔除涨停占比高的周。
- **若失败**：概念动量已被套利。H4 的基准轮动改用 H1 事件，或放弃轮动。

### H3 低可见度溢出

- **H0**：溢出信号对下周超额收益没有预测力。
- **构造**：对每个非成员股，用 52 周共现权重乘以当周概念超额，得到溢出信号；控制变量为自身当周收益和 12 周动量。
- **检验**：
  - 周度 Fama-MacBeth（NW 滞后 2）。
  - 每周在有链接的股票中做十分位多空，按两腿实测换手扣费。
- **门槛**：FM t ≥ 3；系数 > 0；扣费多空均值 > 0。
- **稳健性**：文本相似链接、两种链接的并集；剔除同申万行业的链接（更"低可见度"）；计算盈亏平衡成本。
- **若失败**：A 股溢出已被快速定价（游资、题材扩散快）。H3 只保留为 H1 的辅助特征。

### H4 拥挤 × 隐含预期过滤

- **H0**：过滤不降低相对回撤。
- **构造**：基准臂为动量主题轮动（参数网格：回看 {8, 13, 26} 周 × 持有前 {3, 5, 8} 个主题）加跟踪误差预算；过滤臂在同一网格上剔除被标记为拥挤的主题。
- **检验**：
  - 两臂各自做选择型 CPCV：每个切分在训练组上按 Sharpe 选参数，在测试组上记录收益，重组为 9 条路径。
  - 按路径配对比较相对最大回撤和 IR。
  - 全样本统计每个网格点的回撤改善。
  - 报告 PBO 与 DSR（用于 L2）。
- **门槛**：路径回撤降幅中位数 ≥ 20%；改善路径占比 ≥ 70%；IR 差中位数 ≥ -0.1；≥ 80% 的网格点回撤降幅 ≥ 10%。
- **若失败**：拥挤信号的时点过早（Ben-David 的证据是 5 年尺度）。改为降低仓位而非剔除，作为探索性试验重测。

### E1（探索，不设门槛）BERTrend 提前量

对验证期内新建的概念，比较 BERTrend 首次判为"弱"的周与概念创建日。中位提前量 > 0 说明文本能先于概念板块识别主题，可支撑 Phase 6 的"新主题"策略。

---

## 9. 验证协议总则

1. **已知答案优先。**任何新信号都先在合成数据上植入效应，证明能找到；再在无效应数据上证明不会误报。
2. **功效先于结论。**用真实数据校准合成市场的波动和规模，设定"现实效应量"（建议取文献报告值的一半，冻结前确定）。功效 < 0.8 的假设，其失败结论只能写"不确定"。
3. **预注册与冻结。**Phase 2 结束时 `make freeze` 并 `git tag prereg-v1`。冻结后修改任何配置，相关运行自动降级为探索性。
4. **试验计数。**所有运行写入 `trials.jsonl`；DSR 的试验数取同一策略族的全部记录，包括失败的。
5. **多重检验。**新信号用 t ≥ 3，复制用 t ≥ 2。四个假设的验证期结果另报 Holm 校正后的 p 值。
6. **留出期一次性。**由 `reports/HOLDOUT_USED_*` 强制执行，没有例外。
7. **成本与可交易性。**往返 30bp；封板或停牌不可成交。H3 必须报告盈亏平衡成本。
8. **LLM 规则**见 R7；嵌入模型规则见 R6。

---

## 10. 执行阶段（Claude Code 按序执行）

### Phase 0：环境与冒烟 ✅（脚手架已完成）

命令：`make setup && make test && make smoke`

**验收：**14 个单元测试通过；冒烟 8/8 符合预期；`make loop-check` 能输出对照卡片。当前实测结果：

| 数据 | H1 | H2 | H3 | H4 |
|---|---|---|---|---|
| 植入效应 | PASS（t = 3.9，安慰剂 p = 0.000，62 个事件） | PASS（发表后 t = 3.1，衰减比 0.52，净 IR 0.52） | PASS（FM t = 29.7） | PASS（回撤降幅中位 42%，9/9 路径改善） |
| 无效应 | FAIL（t = -0.9） | FAIL（t = -0.5） | FAIL（t = 0.2） | FAIL（回撤降幅中位 -10%） |

小规模功效检查（每格 4 次模拟）：

- H1：效应量 0.5 倍时功效 0.5，1 倍时 1.0。
- H2：效应量 1 倍时功效仅 0.5。合成市场只有 40 个概念、约 4.5 年的发表后窗口，**H2 是功效上的约束瓶颈**；真实数据约 400 个概念，需在 Phase 2 校准后重测。
- 两者在无效应数据上的误报率均为 0。

### Phase 1：数据

1. 实现 `tushare_provider.py`，或新增 jqdata provider。确定 PIT 概念成分来源（§4.1 的 ①②③）并写入审计。
2. 立即部署 `snapshot_daily.py` 为每日定时任务，无论①②是否可用。前向快照是唯一完全可控的 PIT 来源。
3. 实现 `build_bundle.py`：
   - 新闻 → `zero_shot.theme_doc_counts`
   - 新闻 → 共现边
   - ETF → 概念映射
   - 财务（ann_date）× 周价格 → 隐含增速（含 NOPAT 回退）
4. 运行 `make audit`。

**验收：**`validate_bundle` 为空；审计红旗为空或已书面说明处理方式；隐含增速覆盖率 ≥ 50%。

### Phase 2：校准与功效 → 冻结

1. `python scripts/power_analysis.py --calibrate-from data/processed/bundle --h H1,H2,H3,H4 --n-sims 20`
2. 对功效 < 0.8 的假设，调整设计（加长样本、放粗频率、减少分组），并在冻结前写入 yaml。
3. `make freeze`，然后 `git tag prereg-v1`。

**验收：**每个假设在现实效应量下的功效 ≥ 0.8，或已在 `reports/power.md` 中标注为"不确定"。

### Phase 2.5：Case Lab 反馈循环（详见 `LOOP.md`）

1. `make loop-check` 确认循环框架可用（合成案例）。
2. 为三个开发案例实现 `fetch_case_data.py`，跑 iter 0 基线。
3. 按 LOOP.md 循环：每轮只改一个机制旋钮，三个案例都不变差且冒烟 8/8 才接受。
4. 停止后写 `reports/loop/SUMMARY.md`，然后把被接受的机制写进 `configs/`，再执行 `make freeze`。

**验收：**SUMMARY 完成；所有轮次在 trials 日志中；冒烟仍为 8/8。

**状态（2026-10-06，MVP）：**已用免费网络源完成三个案例的数据构建（`docs/case_data.md`），跑完 iter 0–7。接受 `expectations_engine=auto` 与 `confirm_with_revisions=true`（代理），之后连续 3 轮 REJECT 而停止。结论见 `reports/loop/SUMMARY.md`。`make freeze` 尚未执行（人工关卡）。

### Phase 3：发现期探索 → 验证期确认

1. 发现期可自由探索，运行时加 `--exploratory`。
2. 验证期按 H2 → H4 → H1 → H3 的顺序，每个假设只跑预注册的主设定（稳健性设定照常记录）。
3. 生成 `reports/validation_summary.md`，包含每个假设的指标、gates、Holm p 值，以及决策矩阵的落点。

**验收：**汇总报告完成；所有运行都在 trials 日志中。

### Phase 4：组装与留出期

1. 按决策矩阵组装 overlay，配置写入 `configs/strategy.yaml`，然后冻结。
2. 每个入选假设各跑一次 `--split holdout --unlock-holdout`，策略整体跑一次。
3. 对照 L2 门槛。

**验收：**L2 全部满足才进入 Phase 5。否则记录负结果，回到决策矩阵。

### Phase 5：模拟盘（13 周）

每日快照 → 每周重建信号 → 模拟成交（涨跌停、停牌规则与回测一致）→ 每周对照回测分布。

**验收：**L3。

### Phase 6（可选扩展）

- 美股/港股：Hoberg-Phillips TNIC 数据库 + EDGAR + 主题 ETF 资金流。
- 映射升级：THEME 式嵌入微调。
- E1 新主题策略：BERTrend 或离群点预测。
- 因子迭代：RD-Agent(Q)，所有迭代计入 trials。

---

## 11. Case Lab：用真实主题跑反馈循环

**目的。**把前面的每一层讨论放到具体主题上检验，并让 agent 通过反馈循环（做 → 看 → 调 → 再做）改进机制。系统检验（§8）回答"平均而言是否有效"；Case Lab 回答"在哪里失效、为什么失效"。

| 案例 | 市场 | 生命周期特征 | 重点检验 |
|---|---|---|---|
| `us_space_2025` 商业航天 | 美股 | 2025-10 加速；2026 年 3–5 月 6 只新 ETF 上市、单月流入 13 亿美元；6-12 SpaceX 上市当日板块下跌，此后一个月 UFO 约 -26% | H4 教科书案例：ETF 扎堆 + 隐含预期极高 + 巨型新股抽血 |
| `cn_optical_2025` 光通信/CPO | A 股 | 2025 全年中际旭创 +428%、新易盛 +410%、天孚通信 +284%，业绩同步兑现 | H4 的误报风险：拥挤但预期仍在上修；H2、H3（上游滞后） |
| `hk_ai_openclaw_2026` 智谱/MiniMax | 港股 | 2-1 至 3-10 分别 +186%/+157%；MiniMax 3 月见顶后回撤 77%，智谱 6 月前涨近 20 倍 | 另类注意力（GitHub 星标、token 份额）；供给冲击（解禁比例差异）；同主题内分化 |

**新增机制（为案例而生，均可在循环中开关）：**

- `SalesDrivenReverseDCF`：亏损公司的收入驱动反向 DCF。
- 同行横截面分位：替代新上市公司缺失的自身历史。
- 供给事件：IPO、解禁、指数纳入，均为事前已知、PIT 合法的信息。
- 一致预期修正确认。
- 多种注意力源。

**规则：**见 `LOOP.md`。最重要的三条：

1. 一次只改一处。
2. 从一个案例发现的改动，必须在三个案例上都不变差。
3. 案例事实（`known_events`）只做标注，不得进入信号。

---

## 12. 已知局限与风险

1. **PIT 概念成分是最大的单点风险。**没有可靠的历史成分，H2/H3/H4 的历史回测会高估；前向快照至少需要积累 1–2 年才有统计意义。
2. **合成数据的效应量远大于现实。**特别是 H3（t ≈ 30）。冒烟测试只证明"检验能找到效应、不会误报"，不证明真实世界存在效应；现实效应量由 Phase 2 决定。
3. **新闻数据的深度和来源结构会随时间变化**（来源增减），文档数可能有结构断点。用注意力份额而非绝对计数，并在审计中检查断点。
4. **A 股涨跌停与 T+1** 使周频模拟仍偏乐观。H3 的盈亏平衡成本若低于 50bp，视为不可实施。
5. **嵌入模型的参数化前视**比生成式 LLM 弱，但不为零。留出期必须晚于模型发布日期。
6. **H3 运行速度**：真实规模下需要缓存与向量化（见 `CLAUDE.md`）。

---

## 13. 参考

- BERTrend: arXiv 2411.05930；github.com/rte-france/BERTrend；pypi.org/project/bertrend
- Zve et al.: arXiv 2609.29183（2026）；From Noise to Signal, LREC 2026
- Bybee, Kelly, Manela, Xiu, Business News and Business Cycles, JF 79(5), 2024；Bybee, Kelly, Su, Narrative Asset Pricing, RFS 2023
- Gupta, Bhowmik, Gunow, Agentic Retrieval of Topics and Insights from Earnings Calls, arXiv 2507.07906
- MSCI Thematic Exposure Standard；MSCI Strategy Exposure Calculation Methodology（2026-07）
- Hoberg & Phillips, JPE 124 (2016)；Text-Based Industry Momentum, JFQA 53(6) (2018)
- Lee et al., THEME, arXiv 2508.16936
- Diamond Cuts Diamond: News Co-mention Momentum Spillover Prevails in China, JBF 2025
- Concept links and return momentum, JBF 134 (2022)
- BlackRock THRO Summary Prospectus（2025-11-28）；Tomorrow's themes, today（2025-05）；Navigating thematic investing with THRO（2025-08）
- Morningstar Indexes, Thematic Investing: Performance and Rotation Insights（2026-02）
- Ben-David, Franzoni, Kim, Moussawi, Competition for Attention in the ETF Space, RFS 36(3) (2023)
- Mauboussin & Rappaport, Expectations Investing（2021 修订版）
- Li et al., FINSABER, arXiv 2505.07078（KDD 2026）；github.com/waylonli/FINSABER
- FinCAD, arXiv 2605.24564；BlindTrade, arXiv 2603.17692；The Alpha Illusion, arXiv 2605.16895
- skfolio CombinatorialPurgedCV；Bailey & López de Prado, Deflated Sharpe Ratio (2014)；Bailey et al., PBO (2017)
- Li et al., R&D-Agent-Quant, NeurIPS 2025；github.com/microsoft/RD-Agent
- github.com/anthropics/financial-services
- Tushare 文档：ths_member（doc_id=261）、index_member（doc_id=182）、dc_index
- 三个开发案例的事实来源：见 `cases/*.yaml` 的 `sources` 字段

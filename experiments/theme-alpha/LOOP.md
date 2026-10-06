# LOOP.md — 反馈循环协议（Case Lab）

**反馈循环 = 做一件事 → 看结果 → 根据结果调整 → 再做一次。**

Agent 用三个真实主题作为开发案例，反复执行这个循环。每一轮只改一处，每一轮都留下记录。

---

## 1. 为什么需要单独的 Case Lab

三个开发案例全部落在原 SPEC 的留出期（2024-01 至 2026-06）或之后。如果直接在上面反复调整，留出期就被"用掉"了。所以样本做了三层划分：

| 层 | 内容 | 允许反馈循环？ |
|---|---|---|
| 开发案例 | `us_space_2025`、`cn_optical_2025`、`hk_ai_openclaw_2026` | 允许，随意迭代 |
| 主题留出 | 同期其他主题，由 `select_holdout_themes.py` **只用注意力数据**按规则选出（看收益之前） | 不允许，冻结后一次性评估 |
| 前向 | 2026-10 起的模拟盘 | 不允许，只观察 |

SPEC 中 H1–H4 在 A 股全概念上的系统检验，评估留出期时要同时报告"剔除开发案例主题"与"不剔除"两个版本。

---

## 2. 每一轮怎么做

```
① 计划   读上一轮的卡片（reports/loop/ITERATIONS.md），写下：
          - 观察到什么（引用具体指标）
          - 要改哪一个机制旋钮，为什么
          - 预期哪个指标、往哪个方向变
② 执行   python scripts/case_loop.py --iter N --set <knob>=<value> --note "<理由>"
          若旋钮影响数据构建（如 expectations_engine），先重跑 fetch_case_data.py
③ 观察   读新卡片的 prev → now 对照表
④ 判断   ACCEPT 的三个条件必须同时满足：
          a) 预期的指标按预期方向变化
          b) 另外两个案例的同类指标没有变差
          c) make smoke 仍为 8/8（检验框架没被破坏）
          否则 REJECT，把旋钮恢复原值
⑤ 记录   在卡片末尾填写 decision 行；ACCEPT 才修改 configs/case_lab.yaml
⑥ 下一轮
```

**停止条件**（满足任一即停）：

- 连续 3 轮 REJECT
- 达到 12 轮
- 发现数据问题（此时先修数据，修完从 iter 0 重新跑基线）

停下之后，运行 `make freeze`，然后评估主题留出（一次性）。

---

## 3. 防过拟合护栏

1. **一次只改一处。**`case_loop.py` 会拒绝多个 `--set`。
2. **只能改机制，不能改门槛。**`frozen` 下的键改不了；`configs/hypotheses/*.yaml` 的 gates 在循环里也不改。
3. **从一个案例得出的改动，必须在三个案例上都不变差。**只在一个案例上变好、其他变差的改动，就是在拟合那个案例。
4. **每轮都计入 `trials.jsonl`。**最终策略的 DSR 按全部轮次惩罚，包括被 REJECT 的。
5. **`known_events` 只做标注。**任何信号都不得读取它；里程碑（突破、峰值）用了事后信息，只用于评估。
6. **第二梯队名单不得手挑。**只能用案例 yaml 里写好的 PIT 规则（新闻共现、当时的 ETF 持仓或概念成分）生成。
7. **负结果照样记录。**被 REJECT 的改动是下一个人避免重复踩坑的依据。

---

## 4. 固定诊断指标（卡片里的每一行）

| 假设 | 指标 | 含义 |
|---|---|---|
| H1 | `first_weak_to_strong`、`lead_weeks_vs_breakout` | 注意力跃迁比价格突破（从低点起 +20%）早几周；正数 = 领先 |
| H1 | `car13_after_event` | 跃迁后 13 周核心篮子的超额收益 |
| H2 | `capture_ratio` | 时间序列动量（过去 4 周超额 > 0 才持有）捕获的超额 ÷ 买入持有的超额 |
| H3 | `best_lag`、`lag1_minus_lag0`、`next_week_t` | 第二梯队是否滞后核心股 1 周以上跟随 |
| H4 | `first_flag`、`flag_lead_weeks_vs_peak` | 拥挤标记比峰值早几周；负数 = 峰值之后才标记 |
| H4 | `exit_value_to_end`、`exit_value_26w` | 在首次标记时退出的价值（正数 = 避开了下跌，负数 = 错过了上涨） |
| H4 | `blocked_by_missing_expectations` | 隐含增速覆盖率不足，导致标记根本无法触发 |

---

## 5. 起步路线：每个案例最可能先暴露的问题

以下是基于案例事实的**待检验预期**，不是结论，由循环来证实或否定。

**iter 0：基线。**全部默认设置，三个案例各跑一次，记录卡片。

**预期问题 A：亏损公司算不出隐含预期。**太空股（如 ASTS）和两家大模型公司 FCF 为负，默认 FCF 引擎会返回 `non_positive_fcf`，导致 H4 被 `blocked`。
- 候选改动：`expectations_engine=auto`（FCF ≤ 0 时改用收入驱动的反向 DCF，`SalesDrivenReverseDCF`）。
- 预期：太空和 AI 案例的覆盖率上升，H4 开始能触发；光通信案例不受影响。

**预期问题 B：新上市公司没有足够历史。**MiniMax、智谱 2026 年 1 月才上市，`own_history` 分位需要 26 周，3 月的峰值前根本无法标记。
- 候选改动：`crowd_percentile_basis=peer_cross_section`。
- 预期：AI 案例的 `flag_lead_weeks_vs_peak` 由"无"变为正数。需要检查光通信案例是否因此过早标记。

**预期问题 C：业绩兑现型主题的误报。**光通信核心三家 2025 年全年分别 +428%/+410%/+284%，同时业绩持续上修（中际旭创 2025 年归母净利 +109%）。若拥挤标记在年中触发，`exit_value` 会是很大的负数。
- 候选改动：`confirm_with_revisions=true`（只有一致预期开始下修时才确认拥挤）。需要先接入一致预期数据。
- 预期：光通信 `exit_value` 回升，同时太空案例的提前量不应明显变差。

**预期问题 D：新闻注意力可能滞后于价格。**OpenClaw 的扩散首先发生在开发者社区：GitHub 星标、OpenRouter token 份额。
- 候选改动：`attention_source=github_stars_delta` 或 `token_share`（仅 AI 案例有这些源；其他案例回退到 news_count）。
- 预期：AI 案例的 `lead_weeks_vs_breakout` 变大。

**预期问题 E：供给冲击是可预知的拥挤信号。**MiniMax 首批解禁约 44.85%，而智谱约 5.76%，解禁日 MiniMax -18%；太空主题见顶与 SpaceX 上市同步。锁定期到期日和 IPO 日期都在事前公告，属于 PIT 合法信息。
- 候选改动：`use_supply_events=true`。
- 预期：AI 和太空案例 H4 的 `exit_value_26w` 上升。光通信案例只有减持事件且规模小，应无影响。

**特别注意：同一主题内的分化。**智谱与 MiniMax 同属一个主题，一个年内涨近 20 倍，一个从高点回撤 77%。如果循环最后发现主题层面的信号无法区分二者，这本身就是结论：主题信号只决定"看哪里"，个股层面的隐含预期与供给才决定"买谁"。把它写进最终报告，不要用更多旋钮去"修"。

---

## 6. Agent 的执行指令（可直接粘贴给 Claude Code）

> 读 CLAUDE.md、SPEC.md、LOOP.md。先 `make loop-check` 确认循环框架可用。然后为三个开发案例实现 `scripts/fetch_case_data.py`，跑 iter 0 基线。之后严格按 LOOP.md §2 的步骤循环：每轮只改一个机制旋钮，在卡片末尾填写 ACCEPT/REJECT 和理由，直到满足停止条件。最后生成 `reports/loop/SUMMARY.md`，内容包括：每个被接受的改动、它在三个案例上的效果、被拒绝的改动，以及主题信号在哪些地方失效。

---
name: valueinvest-assistant
description: "Use when 用户要跑 ValueInvest 基本面研究（四视角 + 多空两轮辩论 + 强制结论 + 合规门 + 单文件 HTML 报告）。脚本取数、subagent 并行、verify_run 判合规、render_report 出分享件。"
license: MIT
---

# ValueInvest-Assistant —— 基本面价值投资研究流程（agent 编排版）

本 SKILL 是 ValueInvest-Assistant 的流程与纪律定义，配套脚本在**本仓库根目录**。

**定位：观测层，不是判据层** —— 输出是附加视角，不参与量化因子池判定，不推翻任何既有结论；与既有结论冲突时并列保留，交人判断。

```
REPO=<本仓库根目录>        # 被 agent 加载时：skill 的 base directory 就是本仓库根目录，直接用它
PY=<你的 python>           # 需 akshare/pandas/requests/mistune，见 requirements.txt
```

## 何时用

用户说"用 ValueInvest 跑 `<代码>`"、"四视角 + 多空辩论研究 `<公司>`"、"出一份价值投资研究报告"。

A股 / 港股 / 美股都直接跑 `datapack.py`（美股走 SEC EDGAR XBRL + Nasdaq 路径）。只有在脚本明确报"不支持该代码"，或需要港股 5 年年报序列时，才改用外部年报路径补取。

## 六步（每步都有落地工件，缺一即 FAIL）

```bash
RD=$REPO/runs/<代码>-$(date +%Y%m%d)
```

### ① 取数（确定性，禁止 LLM 编数字）
```bash
$PY $REPO/datapack.py <代码> $RD          # → facts.md + facts.json，自带股本/市值/PE 互验
```
- 取数失败会**明确报缺**（`## ⚠️ 缺口`），缺口处禁止脑补。
- 港股只到快照级：`参考财报序列` 会出现在缺口里，需另走年报路径补。
- 美股需 `VALUEINVEST_SEC_UA="Your Name your@email.com"`（SEC 要求，否则 403）。
- 任何「元/亿元/百万」换算都在脚本内完成并写进「脚本级验算」段——单位 bug 只有这一节能当场抓住。

### ② 四视角（4 个 subagent 并行，同一份 facts，互相看不见）
按 `prompts.md` A 节的角色契约派 4 个子任务，各自写进运行目录：
`01-business.md`（段永平/商业模式）、`02-financial.md`（巴菲特/财务估值）、`03-industry.md`（芒格/行业竞争）、`04-risk.md`（李录/风险与管理层）。
每份结尾必须有 `**结论**` / `**评分** X/5` / `**最不确定的一点**`。**必须同批派发**。
`02-financial.md` 的三情景估值必须调用 `$REPO/tools/financial_rigor.py three-scenario`，禁止心算。

**子 Agent 一律把报告写进文件，只回传 ≤15 行摘要**；后续批次只传**文件路径**，绝不搬全文——8 份报告全文会淹没父会话上下文，而它们本来就在磁盘上。

### ③ 多空两轮辩论（本框架唯一真正新增的机制，见 `prompts.md` B/C 节）
- **第 1 轮**：多头、空头**各自独立**读 `facts.md` + `01~04`，写 `05-bull-r1.md` / `06-bear-r1.md`，各 ≥5 条带出处证据，并写"我的建仓/回避条件"。两个子任务同批并行。
- **第 2 轮**：把**对方第 1 轮**喂回去，写 `07-bull-r2.md` / `08-bear-r2.md`，固定四段：对方最强一条 / 我的反驳（≥3 条带出处）/ **最强反对意见** / **立场是否改变**。同批并行。
- 子任务不能再派子任务：第 2 轮必须等第 1 轮八个工件落盘后，由主会话再派一批；**期间不要轮询日志或产物**。

### ④ 决策与风控（主 agent 本体做，不外包）
按 `prompts.md` D 节写 `09-decision.md`：强制结论（通过/不通过/灰色）→ 分歧地图 + 裁决理由 → 三档价格区间（激进/稳健/保守，给区间不给点）→ 风控检查（仓位上限/集中度/止损或回避理由）→ 数据核验（引 `financial_rigor.py cross-validate` 输出原文）→ 反偏见声明（信息丰富度 A/B/C + 数据截止日 + 缺口）。
同时补全 `meta.json` 的 `stages`（facts 阶段由脚本写入）：`{"analysts":{...},"debate_r1":{...},"debate_r2":{...},"decision":{...}}`。

### ⑤ 合规门（不准跳过）
```bash
$PY $REPO/verify_run.py $RD
```
退出码 0 = PASS 可发布；非 0 = 打回，按打印的 ❌ 逐项补齐后重跑校验。

### ⑥ 渲染单文件 HTML（分享件）
```bash
$PY $REPO/render_report.py $RD            # → $RD/report.html，单文件自包含，双击可开
```
- **先过 ⑤ 再渲染**；渲染是**只读**的，跑一半的运行也能渲染（缺的阶段标"未产出"，不编内容）。
- 结论/评分/分歧收敛从 `meta.json` 取，三档区间照抄 `09-decision.md` 原文，渲染器**不重算任何数字**。
- 产物自包含（CSS 内联、无 Plotly/CDN）：离线可分享。要真图表或 PDF 时再说，别提前引 Plotly/Quarto。
- 改了渲染器先跑 `render_report.py --selftest`（断言自包含 + 关键内容在位 + 缺件降级 + 三档抽取），过了再渲染真报告。

## 维护与扩展规则

- **先做资产映射，再动手**：新增组件前先看 `tools/` 与上游仓库里是否已有等价物——四视角、checklist、分层价格、交叉验证都已存在，本框架只补了**辩论层**。已明确砍掉的 5 个组件（Qlib 因子层 / LangGraph-CrewAI / finance-agent-mcp-server / vectorbt / 因子衰减状态机）及逐条理由见 `README.md`。
- **合规门要先证明它会拦**：往 `verify_run.py` 加新判据后，先在一个只跑到中途的运行目录上跑一遍，确认那项判 ❌ 再依赖它。一个从来不会 FAIL 的门等于没门。
- 改了 `datapack.py` 先跑 `datapack.py --verify <run_dir>`；改了渲染器先跑 `--selftest`（本地 11 项全绿是第一道防线）。
- **本地解释器比 CI 新**：本地开发用 3.12、CI 跑 3.11，所以不要在 f-string 表达式里写反斜杠（如 `f"{x.removesuffix('</p>\n')}"`）——3.12 允许、3.11 直接 SyntaxError。这类"本机绿、CI 红"的问题交给 CI 当第二道防线，别指望本地自检发现。

## 纪律

- 强制结论：三选一，不接受"视情况而定"；分层建议给**区间**不给点。
- 一切结论与其**适用范围**捆绑：写明在什么前提下成立、什么条件下失效。
- 报告头部标数据截止日；AI 置信度 ≠ 投资确定性（信息稀缺标的必须降级声明）。
- 子 Agent 报的"你的数据有问题"要认真查——本框架首跑就是多头 R1 抓出了事实包的口径错误。

## 实测踩过的坑（别再踩）

| 坑 | 处理 |
|---|---|
| 股息率只取最近一次派息会低估近一半（有公司中期+年报两次派息） | 脚本改为**近 12 个月实付合计**（TTM），并同时打印单次口径作对照 |
| 单位陷阱：净利与 EPS 同为"元"，反推股本多乘 1e8，PE 互验算成 0 | 金额一律在 facts.md 里转亿元，且在脚本内完成换算并写进「脚本级验算」段 |
| 行情接口可达性会漂移（某数据源可能被本网稳定切断，偶发成功会骗人） | 主源 + 备源并存、取数带重试；**改源前先跑探针**，别照搬别人的可达性结论 |
| SEC `companyfacts` 滞后于最新申报（缓存最新只到上一财年） | 美股路径：年报走 companyfacts + 最新季报走 10-Q 原文；事实包同时给 FY / TTM / 单季年化三个 PE 口径（只报一个是误导） |
| 子 Agent 引用 facts 之外的数据（批价、合同负债、税收条文） | 这是分工设计（facts 管数字，联网管时效事实），但二级转引必须标 ⚠️ 待核 |
| 报告之间出现"ROE 6.8% vs RoTCE 13%"式矛盾 | 先对齐期间再比大小（两者分别是不同期间），把基准期间摆出来再谈贵贱 |
| 辩论第 2 轮必须把对手第 1 轮喂回去 | 否则不会出现"立场是否改变"的真让步 |
| **本机 `python3` 可能是 3.9**（agent 运行环境不一定是你的开发环境；实测 DSH 的 bash 里 `python3` = 3.9.25） | `Path \| None` 这类 PEP 604 注解在 3.9 上会在 **import 阶段**就 `TypeError`（脚本一行都没跑）。脚本已加 `from __future__ import annotations` 兜底；真实取数路径仍需 **Python 3.11+**（见 requirements.txt）。排查"在别的环境跑不动"先报解释器版本 |

## 美股路径要点

1. **SEC 要规范 UA**：`<应用名> <邮箱>`（`VALUEINVEST_SEC_UA`）——用 `localhost` 之类邮箱会 403。
2. **CIK 自动查**：脚本从 `sec.gov/files/company_tickers.json` 取；补零用 `f"{int(cik):010d}"`，别手拼。
3. **第二来源用注入通道**：脚本不自己抓聚合站（常被 429/403/Cloudflare 挡），把第二来源的值写成 JSON 后
   `$PY datapack.py <代码> $RD --cross-check $RD/cross_check_<源>.json`；拿不到就落进 `## ⚠️ 缺口`，**不允许静默假装已双源**。
4. **XBRL 取数坑**：年度值按"约一年区间（300~400 天）+ form=10-K"过滤，不要用 `frame.startswith('CY')`（会命中季度帧）。

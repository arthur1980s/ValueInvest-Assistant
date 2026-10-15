# ValueInvest-Assistant

[![selftest](https://github.com/arthur1980s/ValueInvest-Assistant/actions/workflows/selftest.yml/badge.svg)](https://github.com/arthur1980s/ValueInvest-Assistant/actions/workflows/selftest.yml)  ![license](https://img.shields.io/badge/license-MIT-blue.svg)

**多视角对抗、强制给结论、工程化验证的价值投资研究框架** —— 以 Skill 形态交付，任何兼容 agent（Hermes / Claude Code / Codex 等）都能加载调用，最终产出一份**单文件、离线可开**的 HTML 研究报告。

> **定位：观测层 + 展示层，不是判据层。** 输出是附加视角，不参与量化因子池判定、不推翻任何既有结论；与既有结论冲突时并列保留，交人判断。只读、不推翻、不判定。

```
标的代码 ──► ① 确定性取数 ──► ② 四视角并行分析 ──► ③ 多空两轮辩论 ──► ④ 决策与风控
  (A股/港股/美股)   facts.md/json     4 个子 agent        2 轮对抗          强制结论 + 三档价格
                                                                              │
                                          report.html ◄── ⑥ 渲染 ◄── ⑤ 合规门（PASS 才发布）
```

---

## 1. 它解决什么问题

让 LLM 写研究报告，默认产物是**一份很长的报告**：观点平衡、措辞漂亮、没有结论，数字无法追溯，读完之后你不知道该买还是不该买。

本框架用四条硬约束把"长报告"逼成"可决断的研究结论"：

| 硬约束 | 做法 | 落地工件 |
|---|---|---|
| 数字不许 LLM 编 | 取数全部由脚本完成，A股/港股/美股各有一条可回溯的来源链，并自带股本/市值/PE 互验 | `datapack.py` → `facts.md` / `facts.json` |
| 观点必须对抗 | 四视角并行（互相看不见）+ 多空两轮辩论（第 2 轮把对手第 1 轮喂回去） | `01~04*.md`、`05~08*.md` |
| 必须给结论 | 强制三选一（通过 / 不通过 / 灰色），三档价格区间（激进/稳健/保守），禁止"视情况而定" | `09-decision.md` |
| 合规门会拦人 | 缺出处、缺结论、缺价格区间、缺风控、没用契约术语 → 判 FAIL 打回 | `verify_run.py`（退出码非 0） |

**合规门真的会拦**：AT&T 那一轮，多头第 2 轮报告内容充足但没有写出契约术语"最强反对意见"，`verify_run.py` 判 FAIL 打回，补齐后才 PASS。一个从来不会 FAIL 的门等于没门。

---

## 2. 快速开始

```bash
git clone https://github.com/arthur1980s/ValueInvest-Assistant.git
cd ValueInvest-Assistant
pip install -r requirements.txt            # akshare / pandas / requests / mistune

export VALUEINVEST_SEC_UA="Your Name your@email.com"   # 仅美股需要（SEC 要求，否则 403）
PY=python

# ① 取数 → facts.md + facts.json（自带互验，含"脚本级验算"段）
$PY datapack.py T runs/T-$(date +%Y%m%d)

# ② ③ 由 agent 按 prompts.md 的契约派子任务写工件（见 SKILL.md 六步）
# ④ 决策与风控由主 agent 写 09-decision.md

# ⑤ 合规门：缺结论/出处/价格区间/风控 一律 FAIL
$PY verify_run.py runs/T-$(date +%Y%m%d)

# ⑥ 渲染：单文件自包含 HTML，双击可开
$PY render_report.py runs/T-$(date +%Y%m%d)
$PY render_report.py --selftest            # 渲染器自检（10 项）
```

**示例运行**

- [`runs/T-20261014/`](runs/T-20261014/) —— 美股 AT&T（NYSE: T），数据截止 2026-10-14，合规门 PASS，结论「不通过（现价 $22.85 不建仓）」
- [`runs/VZ-20261014/`](runs/VZ-20261014/) —— 美股 Verizon（NYSE: VZ），数据截止 2026-10-14，合规门 PASS，结论「灰色地带 —— 现价 $44.42 不建仓，$40.00 及以下转为通过（分层）」，含 `09-verification-basis.txt`（核验原文）

两份都可以直接双击 `report.html` 查看成品。发布前已对本机路径/环境名做了脱敏，并由 CI 第 7 步持续检查（禁止本机路径、环境名、私有仓库名与私有邮箱进入本仓）。

### 自检与 CI（范围边界）

```bash
python render_report.py --selftest   # 渲染器自检：11 项断言
python verify_run.py runs/T-20261014 # 合规门
python datapack.py --verify runs/T-20261014   # 事实包离线结构校验
```

CI（[`.github/workflows/selftest.yml`](.github/workflows/selftest.yml)）在每次 push / PR 到 `main` 时跑 **6 步**，判据**预先注册**：

1. 语法编译（`py_compile`，不装依赖，先暴露语法错）；2. `pip install -r requirements.txt`（验证文档化环境可在干净 runner 复现）；3. 渲染器自检 11 项；4. 合规门 PASS；5. 事实包离线结构校验；6. 确定性计算工具可执行。

**6 步全绿 = PASS；任一步非 0 = FAIL，不自动重试；超时 10 分钟 = FAIL（防挂死）。**

> **CI 的边界（不要误读 badge）**：CI 只跑**随仓库发布的示例运行**（`runs/T-20261014`、`runs/VZ-20261014`），**不跑**任何联网取数、不跑全量数据管道、不跑多标的批量分析。它证明的是"**代码可运行 + 示例可复现**"，**不是**"框架在全量数据上正确"。后者只能在本地按 `SKILL.md` 的六步手动跑（第一步就是本地 11 项全绿，CI 是第二道防线）。badge 只反映最近一次 push 的结果。

支持范围：

| 市场 | 深度 | 来源 |
|---|---|---|
| A股 | 全量（行情 / 估值分位 / 6 年财报 / 分红 / 主营） | akshare（新浪为主、腾讯为备；东财部分接口不稳） |
| 港股 | 快照级（估值分位 / 分红 / 关键财务）；5 年财报序列需另取年报 | akshare |
| 美股 | 一手年报 + 季报（SEC EDGAR XBRL + 10-Q 原文）+ Nasdaq 行情 | SEC / Nasdaq API |

---

## 3. 复用的开源项目（明确说明）

**本仓库不是任何上游项目的 GitHub Fork**，是独立发布的框架 + Skill。它孵化在 `xbtlin/ai-berkshire` 的工作目录内，并按下面的方式复用了开源成果——**实际复制了代码的只有一项，其余为方法论借鉴**。

| 项目 | Star（2026-10-16） | 许可 | 本项目取用的是什么 | 复用方式 |
|---|---|---|---|---|
| [xbtlin/ai-berkshire](https://github.com/xbtlin/ai-berkshire) | 16,754 | MIT | 四大师视角对抗、强制给结论、分层价格建议、数据交叉验证的方法论骨架；**`tools/financial_rigor.py` 原样复制**（475 行，作为确定性计算工具：市值/估值交叉验证、三情景估值） | **复制代码（1 个文件，已保留上游版权声明）** + 方法论复用 |
| [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) | 111,339 | Apache-2.0 | 多智能体分层协作、"正反双方共享同一份证据"的多空辩论机制 → 本框架的 ③辩论层（`prompts.md` B/C 节） | **仅借鉴思想，未复制代码** |
| [virattt/ai-hedge-fund](https://github.com/virattt/ai-hedge-fund) | 64,011 | MIT | 投资者人格化 Agent、各自立场不重叠、分歧显式化 → 本框架的四个角色契约与"分歧地图" | **仅借鉴思想，未复制代码** |
| [HKUDS/Vibe-Trading](https://github.com/HKUDS/Vibe-Trading) | 35,567 | MIT | 工程纪律（审计层、数字角色声明与核验、准出把关）→ `verify_run.py` 合规门的思路 | **仅借鉴思想，未复制代码** |
| [quarto-dev/quarto-cli](https://github.com/quarto-dev/quarto-cli) | 6,091 | MIT/其他 | 原方案的报告渲染层（Quarto Dashboards） | **未采用**：`embed-resources: true` 本质就是内联资源，用 `render_report.py`（stdlib + mistune）即可，不为它引入 Quarto CLI + pandoc |

**明确不引入**（评估后判定与本框架目标不合）：[microsoft/qlib](https://github.com/microsoft/qlib)（49,381★）与 [microsoft/RD-Agent](https://github.com/microsoft/RD-Agent)（14,946★）的因子生成侧——目标是 3~10 年基本面判断，日频价量因子与之无关，且两者与本框架完全解耦；另有若干组件经评估后未引入（LangGraph/CrewAI、finance-agent-mcp-server、vectorbt、因子衰减状态机）。

> `tools/financial_rigor.py` 的头部已写明来源与许可。若你重新分发本项目，请一并保留 `LICENSE`（MIT）与 [`NOTICE`](NOTICE) 中的上游版权声明。

---

## 4. 文件结构

```
ValueInvest-Assistant/
├── SKILL.md            # agent 技能入口：触发条件、六步流程、纪律、实测坑
├── prompts.md          # 角色契约 + 辩论规则 + 决策/风控契约 + 观测层纪律（本框架唯一真正新增的机制）
├── datapack.py         # ① 确定性取数 → facts.md/json（A股/港股/美股；自带股本/市值/PE 互验）
├── verify_run.py       # ⑤ 合规门：缺结论/出处/价格区间/风控 一律 FAIL
├── render_report.py    # ⑥ 运行目录 → 单文件自包含 HTML（只读）；--selftest 自检
├── tools/
│   └── financial_rigor.py   # 第三方代码（xbtlin/ai-berkshire, MIT）：确定性计算工具
├── .github/workflows/  # 轻量自检 CI（6 步，只跑示例，不联网）
├── runs/T-20261014/    # 示例运行（美股 AT&T，合规门 PASS，含 report.html）
├── runs/VZ-20261014/   # 示例运行（美股 Verizon，结论「灰色地带」，含核验原文）
├── requirements.txt
├── NOTICE              # 第三方代码来源与版权声明
└── LICENSE
```

一次运行的全部工件：

```
runs/<代码>-<YYYYMMDD>/
  meta.json          # 阶段状态 + 数据截止日 + 缺口清单（含结论/评分，供渲染器引用）
  facts.md facts.json
  01-business.md 02-financial.md 03-industry.md 04-risk.md       # 四视角
  05-bull-r1.md 06-bear-r1.md 07-bull-r2.md 08-bear-r2.md        # 两轮辩论
  09-decision.md 09-verification-basis.txt                        # 决策与核验
  report.html                                                     # 单文件分享件
```

---

## 5. 四个分析视角与辩论机制

| 视角 | 大师 | 核心问题 |
|---|---|---|
| 商业模式分析师 | 段永平 | 这是不是一门好生意？（收入结构、定价权、转换成本、10 年后差异化还在吗） |
| 财务估值分析师 | 巴菲特 | 这价格买的是什么？（ROE/现金流趋势、盈利质量、估值分位、三情景内在价值） |
| 行业竞争分析师 | 芒格 | 护城河有多深、多久被削平？（对手份额、替代品威胁、历史失败案例类比） |
| 风险与管理层分析师 | 李录 | 什么会让我永久亏钱？（资本配置记录、治理红旗、监管、最坏情景本金损失） |

辩论第 2 轮为固定四段结构，缺一即 FAIL：

1. 对方最强的一条（复述 + 为什么它真的强）
2. 我的反驳（≥3 条，每条带出处；反驳不了的要承认）
3. **最强反对意见**（镜子测试：若我错了，最可能错在哪个假设）
4. **立场是否改变**（是/否 + 幅度，必须写清是被哪条证据推动的）

---

## 6. 边界（必须与结论一起引用）

- 框架**不做判据**：不与量化因子池的结论互相覆盖；冲突时并列保留，交人判断。
- **AI 输出置信度 ≠ 投资确定性**；信息稀缺标的在报告中必须降级声明。
- 事实包只保证"数字有出处、缺口被明说"，不保证任何信息优势或超额收益。
- 本项目是研究工具，**不构成投资建议**；使用者自行承担决策后果。
- 已知缺口：港股 5 年财报序列本脚本不取；美股第二独立来源常被反爬挡（429/403/Cloudflare），拿不到时会**明确标注单源**，不假装双源。

---

## 7. 实测记录

| 运行 | 标的 | 结果 |
|---|---|---|
| `runs/T-20261014`（本仓库示例） | AT&T（NYSE: T） | 合规门 PASS，结论"不通过（现价 $22.85 不建仓）"；多空第 2 轮**双方独立收敛**到同一判断 |
| 贵州茅台 600519 | A股 | 首跑即由多头第 1 轮抓出事实包口径错误（股息率单次口径 2.22% vs TTM 4.12%），脚本已修 |
| 腾讯 00700 | 港股 | 快照级取数通过；5 年财报序列明确报缺 |
| 花旗集团 C | 美股 | 首个美股标的；发现 SEC companyfacts 滞后，改为"年报 + 最新 10-Q 原文"，并列 FY/TTM/单季年化三个 PE 口径 |
| Verizon VZ | 美股 | **已跑完并随仓库发布**（`runs/VZ-20261014`）：四视角均分 3.0，两轮辩论后多头 3.5→3.0、空头 2.0→2.5，结论「灰色地带」；两个任务前提错误（不存在的合作、与 10-K 不符的债务数字）被分析师独立核实纠正 |

> 除 `runs/T-20261014` 与 `runs/VZ-20261014` 外，上述运行为开发期记录，完整工件未随本仓库发布。

---

## 8. 许可

MIT（见 [`LICENSE`](LICENSE)）。仓库内含一份来自 `xbtlin/ai-berkshire` 的 MIT 代码（`tools/financial_rigor.py`），其版权声明保留在 [`NOTICE`](NOTICE) 与该文件头部。

English README: [`README_EN.md`](README_EN.md)

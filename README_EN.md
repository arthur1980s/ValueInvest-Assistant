# ValueInvest-Assistant

[![selftest](https://github.com/arthur1980s/ValueInvest-Assistant/actions/workflows/selftest.yml/badge.svg)](https://github.com/arthur1980s/ValueInvest-Assistant/actions/workflows/selftest.yml)  ![license](https://img.shields.io/badge/license-MIT-blue.svg)

**A value-investing research framework with adversarial multi-perspective analysis, a forced verdict, and engineering-grade verification** — shipped as an agent *Skill* (works with Hermes / Claude Code / Codex and any compatible agent) and producing a **single-file, offline-openable HTML research report**.

> **Positioning: an observation + presentation layer, not a decision layer.** Its output is a supplementary perspective. It does not participate in any quantitative factor-pool decision, and it never overrides an existing conclusion — when it conflicts with one, both are kept side by side for a human to judge. Read-only, non-overriding, non-adjudicating.

```
ticker ──► ① deterministic data ──► ② 4 perspectives ──► ③ 2-round debate ──► ④ decision & risk
           (US / HK / A-share)      facts.md/json        4 sub-agents in parallel   forced verdict
                                                                                  3-tier price range
                                                     report.html ◄── ⑥ render ◄── ⑤ compliance gate
```

---

## 1. What problem it solves

Ask an LLM for an equity research report and by default you get **a long report**: balanced-sounding, well-worded, conclusion-free, with untraceable numbers — after reading it you still don't know whether to buy.

Four hard constraints turn "a long report" into "a decision-bearing research conclusion":

| Constraint | How | Artifact |
|---|---|---|
| Numbers are never written by an LLM | All data is fetched by scripts with a traceable source chain per market, plus built-in share-count / market-cap / PE cross-checks | `datapack.py` → `facts.md` / `facts.json` |
| Every view must be contested | 4 analysts in parallel (blind to each other) + 2 rounds of bull/bear debate (round 2 is fed the opponent's round 1) | `01~04*.md`, `05~08*.md` |
| A verdict is mandatory | Forced three-way choice (pass / fail / grey), three price tiers (aggressive / balanced / conservative), "it depends" is rejected | `09-decision.md` |
| The gate must be able to fail you | Missing citation, verdict, price range, risk checks, or contract wording → FAIL, sent back | `verify_run.py` (non-zero exit) |

**The gate really does block work.** In the AT&T run the bull's round-2 report was substantive but never used the contract term "strongest objection"; `verify_run.py` failed it and sent it back. A gate that never fails is not a gate.

---

## 2. Quick start

```bash
git clone https://github.com/arthur1980s/ValueInvest-Assistant.git
cd ValueInvest-Assistant
pip install -r requirements.txt            # akshare / pandas / requests / mistune

export VALUEINVEST_SEC_UA="Your Name your@email.com"   # US market only (SEC requires it, else 403)

# ① fetch data → facts.md + facts.json (with built-in cross-checks)
python datapack.py T runs/T-$(date +%Y%m%d)

# ② ③ dispatched by your agent per the contracts in prompts.md (see SKILL.md)
# ④ the decision layer is written by the lead agent → 09-decision.md

# ⑤ compliance gate
python verify_run.py runs/T-$(date +%Y%m%d)

# ⑥ render one self-contained HTML file
python render_report.py runs/T-$(date +%Y%m%d)
python render_report.py --selftest            # renderer self-check (10 assertions)
```

**Example runs**

- [`runs/T-20261014/`](runs/T-20261014/) — AT&T Inc. (NYSE: T), cutoff 2026-10-14, gate PASS, verdict "fail — no entry at $22.85"
- [`runs/VZ-20261014/`](runs/VZ-20261014/) — Verizon (NYSE: VZ), cutoff 2026-10-14, gate PASS, verdict "grey zone — no entry at $44.42; a pass (tiered) below $40.00", including `09-verification-basis.txt` (raw verification output)

Open either `report.html` directly in a browser. Machine paths / environment names were redacted before publishing and are checked continuously by CI step 7 (no local paths, environment names, private repo names or private emails may enter this repo).

### Self-check & CI (scope boundary)

```bash
python render_report.py --selftest   # renderer self-check: 11 assertions
python verify_run.py runs/T-20261014 # compliance gate
python datapack.py --verify runs/T-20261014   # offline fact-pack structure check
```

CI ([`.github/workflows/selftest.yml`](.github/workflows/selftest.yml)) runs **6 steps** on every push / PR to `main`, with the acceptance criteria **pre-registered**:

1. syntax compile (`py_compile`, no deps, fails fast on syntax errors); 2. `pip install -r requirements.txt` (proves the documented environment resolves on a clean runner); 3. renderer self-check (11 assertions); 4. compliance gate PASS; 5. offline fact-pack structure check; 6. deterministic calculation tool executable.

**All 6 green = PASS; any non-zero = FAIL, no automatic retry; 10-minute timeout = FAIL (anti-hang).**

> **What CI does *not* mean:** it only runs the **example runs shipped in the repo** (`runs/T-20261014`, `runs/VZ-20261014`) — no network fetching, no full data pipeline, no multi-ticker batch. It proves "**code runs + example reproduces**", **not** "the framework is correct on full data"; the latter is a manual six-step run per `SKILL.md` (local self-check green is the first line of defence, CI is the second). The badge reflects only the most recent push.

Coverage:

| Market | Depth | Source |
|---|---|---|
| A-shares (CN) | Full: quote / valuation percentile / 6y financials / dividends / business mix | akshare (Sina primary, Tencent fallback) |
| Hong Kong | Snapshot level: valuation percentile / dividends / key financials; a 5-year statement series needs annual reports fetched separately | akshare |
| US | Primary 10-K + latest 10-Q (SEC EDGAR XBRL) + Nasdaq quotes | SEC / Nasdaq API |

---

## 3. Open-source projects reused (stated explicitly)

**This repository is not a GitHub fork of any upstream project** — it is an independently published framework + Skill. It was developed inside the working tree of `xbtlin/ai-berkshire` and reuses open-source work as follows. **Exactly one item reuses code; the rest borrow ideas only.**

| Project | Stars (2026-10-16) | License | What was taken | How |
|---|---|---|---|---|
| [xbtlin/ai-berkshire](https://github.com/xbtlin/ai-berkshire) | 16,754 | MIT | Methodology skeleton (four master perspectives, forced verdicts, tiered price advice, cross-validation) and **`tools/financial_rigor.py` copied verbatim** (475 lines of deterministic calculation: market-cap / valuation cross-validation, three-scenario valuation) | **Code copied (one file, upstream copyright retained)** + methodology reuse |
| [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) | 111,339 | Apache-2.0 | Multi-agent layered collaboration; bull/bear debate where both sides share the same evidence → layer ③ (`prompts.md` sections B/C) | **Ideas only, no code copied** |
| [virattt/ai-hedge-fund](https://github.com/virattt/ai-hedge-fund) | 64,011 | MIT | Persona-based investor agents with non-overlapping stances and explicit disagreement mapping | **Ideas only, no code copied** |
| [HKUDS/Vibe-Trading](https://github.com/HKUDS/Vibe-Trading) | 35,567 | MIT | Engineering discipline: audit layer, numeric-role declaration and verification, release gating → the idea behind `verify_run.py` | **Ideas only, no code copied** |
| [quarto-dev/quarto-cli](https://github.com/quarto-dev/quarto-cli) | 6,091 | MIT/other | The original plan's report layer (Quarto Dashboards) | **Not adopted:** `embed-resources: true` is just resource inlining; `render_report.py` (stdlib + mistune) does it without pulling in Quarto CLI + pandoc |

**Explicitly not included** (evaluated and rejected as a poor fit): the factor-generation side of [microsoft/qlib](https://github.com/microsoft/qlib) (49,381★) and [microsoft/RD-Agent](https://github.com/microsoft/RD-Agent) (14,946★) — the target is 3–10 year fundamental judgement, daily price/volume factors are irrelevant to it, and those two are fully decoupled from this framework. Also not adopted: LangGraph/CrewAI, finance-agent-mcp-server, vectorbt and the factor-decay state machine.

> `tools/financial_rigor.py` carries a provenance header. If you redistribute this project, keep [`LICENSE`](LICENSE) (MIT) and the upstream copyright notice in [`NOTICE`](NOTICE).

---

## 4. Repository layout

```
ValueInvest-Assistant/
├── SKILL.md            # agent skill entry: triggers, the six steps, discipline, field-tested pitfalls
├── prompts.md          # role contracts + debate rules + decision/risk contract + observation-layer discipline
├── datapack.py         # ① deterministic fetch → facts.md/json (US/HK/A; built-in cross-checks)
├── verify_run.py       # ⑤ compliance gate
├── render_report.py    # ⑥ run dir → single self-contained HTML (read-only); --selftest
├── tools/
│   └── financial_rigor.py   # third-party (xbtlin/ai-berkshire, MIT): deterministic calculation
├── .github/workflows/  # lightweight self-check CI (6 steps, examples only, no network)
├── runs/T-20261014/    # example run (AT&T), gate PASS, includes report.html
├── runs/VZ-20261014/   # example run (Verizon), verdict "grey zone", includes verification basis
├── requirements.txt
├── NOTICE              # third-party provenance & copyright
└── LICENSE
```

Artifacts produced by one run:

```
runs/<TICKER>-<YYYYMMDD>/
  meta.json          # stage status + data cutoff + gaps (verdict/scores consumed by the renderer)
  facts.md facts.json
  01-business.md 02-financial.md 03-industry.md 04-risk.md       # four perspectives
  05-bull-r1.md 06-bear-r1.md 07-bull-r2.md 08-bear-r2.md        # two debate rounds
  09-decision.md 09-verification-basis.txt                        # decision + verification basis
  report.html                                                     # single-file deliverable
```

---

## 5. The four perspectives and the debate mechanism

| Perspective | Master | Core question |
|---|---|---|
| Business-model analyst | Duan Yongping | Is this a good business? (revenue mix, pricing power, switching costs, is the differentiation still there in 10 years) |
| Financial & valuation analyst | Warren Buffett | What am I buying at this price? (ROE/cash-flow trends, earnings quality, valuation percentile, three-scenario intrinsic value) |
| Industry & competition analyst | Charlie Munger | How deep is the moat, how fast is it eroded? (share shifts, substitute threats, historical analogies) |
| Risk & management analyst | Li Lu | What would make me lose money permanently? (capital-allocation record, governance red flags, regulation, worst-case loss) |

Round 2 of the debate has a fixed four-part structure; missing any part fails the gate:

1. The opponent's strongest point (restated, and why it is genuinely strong)
2. My rebuttal (≥3 items, each with a citation; concede what you cannot rebut)
3. **Strongest objection** (mirror test: if I am wrong, which assumption is most likely wrong)
4. **Did my stance change** (yes/no + magnitude, and which piece of evidence drove it)

---

## 6. Boundaries (must be cited together with any conclusion)

- The framework **does not adjudicate**: it never overrides quantitative factor-pool conclusions; conflicts are kept side by side for a human to judge.
- **AI confidence ≠ investment certainty**; low-information names must be flagged as such in the report.
- The fact pack only guarantees "every number has a source and every gap is stated" — no information edge, no excess return.
- Research tool only, **not investment advice**; you own your decisions.
- Known gaps: a 5-year HK statement series is not fetched here; US second-source data is often blocked by anti-scraping (429/403/Cloudflare) and is then **explicitly labelled single-source** rather than silently faked.

---

## 7. Field record

| Run | Ticker | Outcome |
|---|---|---|
| `runs/T-20261014` (example in this repo) | AT&T (NYSE: T) | Gate PASS; verdict "fail — no entry at $22.85"; both debate sides **independently converged** on the same call |
| Kweichow Moutai 600519 | A-share | First run: the bull's round-1 report caught a fact-pack definition error (dividend yield 2.22% single-payment vs 4.12% TTM); script fixed |
| Tencent 00700 | HK | Snapshot-level fetch passed; the 5-year statement series was explicitly reported as a gap |
| Citigroup C | US | First US name; exposed the SEC companyfacts lag, switched to "10-K + latest 10-Q text", now reports FY/TTM/single-quarter-annualised PEs side by side |
| Verizon VZ | US | **Completed and published** (`runs/VZ-20261014`): analyst average 3.0; after two rounds the bull moved 3.5→3.0 and the bear 2.0→2.5; verdict "grey zone"; two false task premises were independently refuted by the analysts |

> Except for `runs/T-20261014` and `runs/VZ-20261014`, the runs above are development records; their full artifacts are not published here.

---

## 8. License

MIT — see [`LICENSE`](LICENSE). The repository contains one MIT-licensed file from `xbtlin/ai-berkshire` (`tools/financial_rigor.py`); its copyright notice is retained in the file header and in [`NOTICE`](NOTICE).

中文说明: [`README.md`](README.md)

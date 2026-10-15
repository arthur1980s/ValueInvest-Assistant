# 事实包 T（US）

- 标的：**AT&T INC.**（CIK 732717）
- 生成时间：2026-10-15 21:28:56
- 数据来源：见文末 sources；**本文件所有数字由脚本取数，禁止 LLM 改写**

## 行情与估值快照

| 项 | 值 |
|---|---|
| price | 23.05 |
| price_date | 2026-10-14 |
| price_adj | unadjusted(实际成交价) |
| currency | USD |
| shares_out_sec | 7000577201 |
| market_cap | 161363304483.05002 |
| market_cap_unit | USD |
| ret_1y_pct | -11.8 |
| ret_5y_pct | 14.6 |
| high_5y | 29.79 |
| low_5y | 13.43 |
| pct_below_5y_high | 22.6 |

## 估值（自建：SEC EPS × Nasdaq 财年末收盘价；来源可回溯）

| 指标 | 值 |
|---|---|
| pe_fy_end | {"current_on_latest_fy_eps": 7.6, "pct_in_available_years": 25.0, "min": 6.16, "max": 15.93, "median": 8.98, "years_covered": [2016, 2025]} |
| dividend_yield_pct | 4.82 |
| dps_latest_fy | 1.11 |
| dps_fy | 2025 |
| dps_quarters_reported | 4 |
| pe_on_latest_quarter_annualized | {"quarter_eps": 0.66, "annualized_eps": 2.64, "pe": 8.73, "note": "单季年化，波动的 Markets 业务会被放大，仅作边界参考"} |
| pe_on_ttm_eps | {"ttm_eps": 3.02, "pe": 7.63, "formula": "上一财年 EPS 3.04 − 上年同期半年 1.22 + 本期半年 1.2（全部来自 SEC 10-K/10-Q）"} |

> ⚠️ 业态说明：美股通用：行业专属指标（银行的 CET1/效率比率/净息差、电信的折旧摊销/资本开支强度、工业的自由现金流口径等）在 10-K 正文而非 XBRL，本脚本不取；OCF 须结合业态解读（银行含贷款投放、电信受大额 capex 支配），不与工商企业简单比较。

## 年度财报（近 6 期，来自 SEC 10-K；金额单位＝**百万美元**）

| 财年 | 营收净额 | 净利(含少数股东) | 普通股净利 | 摊薄EPS | 股东权益 | 总资产 | 经营现金流 | 每股分红 | 股本 |
|---|---|---|---|---|---|---|---|---|---|
| 2025 | 125,648 | 21,953 | 21,889 | 3.04 | None | 420,198 | 40,284 | 1.11 | 7,001 |
| 2024 | 122,336 | 10,948 | 10,746 | 1.49 | None | 394,795 | 38,771 | 1.11 | 7,178 |
| 2023 | 122,428 | 14,400 | 14,192 | 1.97 | None | 407,060 | 38,314 | 1.11 | 7,153 |
| 2022 | 120,741 | -8,524 | -8,727 | -1.13 | None | 402,853 | None | 1.11 | 7,130 |
| 2021 | 134,038 | 20,081 | 19,874 | 2.73 | None | 551,622 | 41,957 | 2.36 | 7,143 |
| 2020 | 143,050 | -5,176 | -5,369 | -0.75 | None | 525,761 | 43,130 | 2.08 | 7,132 |

- XBRL 标签（实际使用，便于复核）：`{"revenue_net": "Revenues", "np": "NetIncomeLoss", "np_common": "NetIncomeLossAvailableToCommonStockholdersBasic", "ocf": "NetCashProvidedByUsedInOperatingActivities", "assets": "Assets", "goodwill": "Goodwill", "eps_diluted": "EarningsPerShareDiluted", "dividends_per_share": "CommonStockDividendsPerShareDeclared（季度去重后按财年加总）", "shares_out": "EntityCommonStockSharesOutstanding"}`

## 股本（三路推导，供交叉验证）

```json
{"sec_shares_outstanding": 7000577201, "from_np_common_over_eps": 7200328947.0}
```

## 脚本级验算

- 季度口径来源: {"note": "SEC companyfacts 滞后于最新申报；季度/TTM 数据取自 2026-07-22 申报的 10-Q 原文（0000732717-26-000297）"}
- 股本两路互验（SEC outstanding vs 普通股净利/EPS）: {"a": 7000577201, "b": 7200328947.0, "diff_pct": 2.85, "verdict": "一致"}
- 市值自算: {"note": "price × SEC 股本 = 161.36B USD；第二独立市值来源不可得时不得声称已双源验证"}

## ⚠️ 缺口（脚本明确报缺，禁止脑补）

- 每股分红 2026 仅含 1 个季度（XBRL 未逐季申报全部季度）⇒ 该年 DPS 与据此算出的股息率被**低估**，勿直接当年度分红额使用
- 第二独立来源（跨源互验）：yfinance 429 / macrotrends 403 / stockanalysis Cloudflare —— 需在报告中标注为单源
- 股东权益（StockholdersEquity）未从 XBRL 取到（公司可能用其他标签）⇒ 本包不算 PB，估值须另取账面

## sources

- financials: SEC EDGAR XBRL companyfacts（10-K 年度）
- price: Nasdaq API api.nasdaq.com/api/quote/<sym>/historical
- second_source: 见 cross_check（若缺则本包为单源：SEC 一手 + Nasdaq 行情）

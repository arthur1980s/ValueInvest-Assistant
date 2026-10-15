# 事实包 VZ（US）

- 标的：**VERIZON COMMUNICATIONS INC**（CIK 732712）
- 生成时间：2026-10-15 21:31:23
- 数据来源：见文末 sources；**本文件所有数字由脚本取数，禁止 LLM 改写**

## 行情与估值快照

| 项 | 值 |
|---|---|
| price | 44.42 |
| price_date | 2026-10-14 |
| price_adj | unadjusted(实际成交价) |
| currency | USD |
| shares_out_sec | 4217684168 |
| market_cap | 187349530742.56 |
| market_cap_unit | USD |
| ret_1y_pct | 9.5 |
| ret_5y_pct | -15.0 |
| high_5y | 55.51 |
| low_5y | 10.5999 |
| pct_below_5y_high | 20.0 |

## 估值（自建：SEC EPS × Nasdaq 财年末收盘价；来源可回溯）

| 指标 | 值 |
|---|---|
| pe_fy_end | {"current_on_latest_fy_eps": 10.9, "pct_in_available_years": 40.0, "min": 7.35, "max": 15.4, "median": 12.73, "years_covered": [2016, 2025]} |
| dividend_yield_pct | 4.68 |
| dps_latest_fy | 2.08 |
| dps_fy | 2025 |
| dps_quarters_reported | 3 |
| pe_on_latest_quarter_annualized | {"quarter_eps": 0.92, "annualized_eps": 3.68, "pe": 12.07, "note": "单季年化，波动的 Markets 业务会被放大，仅作边界参考"} |
| pe_on_ttm_eps | {"ttm_eps": 3.84, "pe": 11.57, "formula": "上一财年 EPS 4.06 − 上年同期半年 2.34 + 本期半年 2.12（全部来自 SEC 10-K/10-Q）"} |

> ⚠️ 业态说明：美股通用：行业专属指标（银行的 CET1/效率比率/净息差、电信的折旧摊销/资本开支强度、工业的自由现金流口径等）在 10-K 正文而非 XBRL，本脚本不取；OCF 须结合业态解读（银行含贷款投放、电信受大额 capex 支配），不与工商企业简单比较。

## 年度财报（近 6 期，来自 SEC 10-K；金额单位＝**百万美元**）

| 财年 | 营收净额 | 净利(含少数股东) | 普通股净利 | 摊薄EPS | 股东权益 | 总资产 | 经营现金流 | 每股分红 | 股本 |
|---|---|---|---|---|---|---|---|---|---|
| 2025 | 138,191 | 17,174 | None | 4.06 | None | 404,258 | 37,137 | 2.08 | 4,218 |
| 2024 | 134,788 | 17,506 | None | 4.14 | None | 384,711 | 36,912 | 2.02 | 4,210 |
| 2023 | 133,974 | 11,614 | None | 2.75 | None | 380,255 | 37,475 | 1.98 | 4,204 |
| 2022 | 136,835 | 21,256 | None | 5.06 | None | 379,680 | 37,141 | 1.94 | 4,200 |
| 2021 | 133,613 | 22,065 | None | 5.32 | None | 366,596 | 39,539 | 1.91 | 4,198 |
| 2020 | 128,292 | 17,801 | None | 4.3 | None | 316,481 | 41,768 | 1.87 | 4,138 |

- XBRL 标签（实际使用，便于复核）：`{"revenue_net": "Revenues", "np": "NetIncomeLoss", "ocf": "NetCashProvidedByUsedInOperatingActivities", "assets": "Assets", "goodwill": "Goodwill", "eps_diluted": "EarningsPerShareDiluted", "dividends_per_share": "CommonStockDividendsPerShareDeclared（季度去重后按财年加总）", "shares_out": "EntityCommonStockSharesOutstanding"}`

## 股本（三路推导，供交叉验证）

```json
{"sec_shares_outstanding": 4217684168, "from_np_common_over_eps": null}
```

## 脚本级验算

- 季度口径来源: {"note": "SEC companyfacts 滞后于最新申报；季度/TTM 数据取自 2026-07-31 申报的 10-Q 原文（0000732712-26-000046）"}
- 市值自算: {"note": "price × SEC 股本 = 187.35B USD；第二独立市值来源不可得时不得声称已双源验证"}

## ⚠️ 缺口（脚本明确报缺，禁止脑补）

- 每股分红 2026 仅含 1 个季度（XBRL 未逐季申报全部季度）⇒ 该年 DPS 与据此算出的股息率被**低估**，勿直接当年度分红额使用
- 每股分红 2025 仅含 3 个季度（XBRL 未逐季申报全部季度）⇒ 该年 DPS $2.08 与据此算出的股息率 4.68% 被**低估**，实际全年 DPS 更高，勿直接当年度分红额使用
- 股东权益（StockholdersEquity）未从 XBRL 取到（公司可能用其他标签）⇒ 本包不算 PB，估值须另取账面

## sources

- financials: SEC EDGAR XBRL companyfacts（10-K 年度）
- price: Nasdaq API api.nasdaq.com/api/quote/<sym>/historical
- second_source: 见 cross_check（若缺则本包为单源：SEC 一手 + Nasdaq 行情）

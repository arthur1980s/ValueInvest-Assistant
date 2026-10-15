# Verizon（VZ）商业模式分析

**视角**：商业模式分析师（段永平视角）
**报告日期**：2026-10-15 | **价格**：$44.42 (facts.md: price, 2026-10-14)
**数据纪律**：基础数字仅取自 facts.md（引用标注 `facts.md: 字段`）；其余公司事实逐条挂 URL 取证。无证据的表述一律降级为"推测"。

---

## 一、收入结构：钱从哪里来

### 1.1 分部结构（FY2025，10-K 正文）

| 分部 | FY2025 营收 | 占比 | 同比 | FY2024 营收 |
|---|---|---|---|---|
| Consumer（消费者：无线+家庭宽带+设备） | $106,807M | 77% | +3.8% | $102,904M |
| Business（企业/政府/批发） | $29,069M | 21% | −1.6% | $29,531M |
| Corporate and other | $2,642M | 1.9% | +1.3% | $2,609M |
| 消除项 | ($327M) | — | — | ($256M) |
| **合计** | **$138,191M** | 100% | **+2.5%** | $134,788M |

来源：[10-K FY2025 分部收入表](https://www.sec.gov/Archives/edgar/data/732712/000073271226000007/vz-20251231.htm)（Consolidated Operating Revenues 表）。合计与 facts.md: 2025 营收净额 138,191 完全一致。

**结构要点**：
- 77% 收入来自消费者分部——本质是"向美国消费者收月租"的生意。
- 企业分部（21%）在**萎缩**（−1.6%），10-K 明确把 Global Enterprise 的 networking/传统数据语音收入下降归因于"secular pressures in the marketplace"（[FY2022 10-K 同口径表述](https://www.sec.gov/Archives/edgar/data/732712/000073271223000012/vz-20221231.htm)）——传统企业通信（专线、语音、组网）是被技术替代的存量业务，不是增长引擎。

### 1.2 消费者分部内部（FY2025，4Q25 财报附表）

| 收入项 | FY2025 | 同比 |
|---|---|---|
| 无线服务（月租，全公司口径） | $83,703M | +2.0% |
| 无线设备（卖手机） | $25,470M | +9.7% |
| 无线其他 | $4,116M | +14.4% |
| 消费者 Fios 收入 | ≈$11,678M（四季加总） | 基本持平 |

来源：[VZ 4Q25 Financial Statements PDF](https://www.verizon.com/about/sites/default/files/2026-01/vz_4q25_fs_013026.pdf)、[4Q25 FOI 附表](https://www.verizon.com/about/sites/default/files/2026-01/vz_4q25_foi_013026.pdf)（Consumer 分部表：Wireless service revenue $83,703 vs $82,073；Fios revenue 四季 $2,896/$2,924/$2,937/$2,921）。

**结论**：真正产生现金流的资产是**无线月租（$83.7B）+ 家庭宽带**；设备收入是过手生意（毛利薄、随换机周期波动）。无线服务收入只增长 2%——这是典型的**存量成熟市场**增速。

### 1.3 用户与单用户价值（2025-12-31，4Q25 FOI）

| 指标 | 2024 年末 | 2025 年末 |
|---|---|---|
| 消费者无线零售连接（含 FWA） | 115.26M | **115.90M** |
| 其中 postpaid | 95.12M | 95.68M |
| 消费者总宽带连接 | 10.01M | **10.86M** |
| 其中 Fios 光纤 | 7.14M | 7.33M |
| 其中 FWA | 2.71M | 3.41M |
| Fios 视频 | 2.68M | **2.44M**（持续萎缩） |

来源：[4Q25 FOI](https://www.verizon.com/about/sites/default/files/2026-01/vz_4q25_foi_013026.pdf)（Consumer - Selected Operating Statistics 连接数表）。10-K 另给出全公司口径：约 **147M 无线零售连接**（116M 消费者 + 31M 企业 postpaid）、约 14M 宽带连接（[10-K FY2025](https://www.sec.gov/Archives/edgar/data/732712/000073271226000007/vz-20251231.htm)）。

- **ARPU/ARPA**：消费者 postpaid 无线 ARPA（按户）从 2024Q1 的 $141.31 升至 2025Q4 的 **$147.36**；预付费 ARPU 稳定在 ~$32.9。来源同上（FOI Revenue Statistics 表）。
- **churn**：postpaid 无线月流失率从 2025Q1 的 1.52% 恶化至 2025Q4 的 **1.64%**（手机口径 1.27%）——流失率在**上升**，不是下降。来源同上。
- **2025 全年 postpaid 手机净增**：Q1−356K、Q2−51K、Q3−7K、Q4+551K，全年约 +137K，即**接近零增长**；公司自己的 2026 指引是"75 万至 100 万 postpaid 手机净增，约为 2025 实际值的 2–3 倍"——反证 2025 全年净增只有 25–33 万量级，且公司把 2026 的改善定义为"step function change"。来源：[4Q25 新闻稿](https://www.verizon.com/about/news/verizon-delivers-2025-financial-guidance-highest-quarterly-net-adds)、[4Q25 FOI](https://www.verizon.com/about/sites/default/files/2026-01/vz_4q25_foi_013026.pdf)。

**增长引擎切换**：无线基本盘不涨人（净增≈0），靠 ARPA 提价 + FWA 宽带（2025 全年 FWA 净增约 71.6 万，从 2.71M 到 3.41M）撑收入。视频（Fios 2.44M 且在缩）是明确的衰退业务。

### 1.4 并购：增长越来越靠买

- **Frontier**：2024-09 签约（纯现金，$38.50/股，较未受影响价溢价 37%），2026-01-20 完成交割，交易规模约 **$200 亿企业价值**。交割后光纤覆盖扩至 31 州+华盛顿特区、约 3000 万家庭/企业 passings，FWA+光纤宽带连接合计超 **1630 万**。来源：[Frontier 新闻稿](https://newsroom.frontier.com/press-release/frontier-stockholders-approve-acquisition-by-verizon)、[Verizon 交割监管批准稿](https://www.verizon.com/about/news/verizon-and-frontier-regulatory-approval)、[10-K FY2025](https://www.sec.gov/Archives/edgar/data/732712/000073271226000007/vz-20251231.htm)（Recent Developments）、[4Q25 新闻稿](https://www.verizon.com/about/news/verizon-delivers-2025-financial-guidance-highest-quarterly-net-adds)。
- 此前：2021-11 收购 TracFone（约 $42B 对价量级，含 57.6M 库藏股约 $3.0B，[FY2022 10-K Note 3/14](https://www.sec.gov/Archives/edgar/data/732712/000073271223000012/vz-20221231.htm)）；2026-01-30 又完成收购 Starry（多住户 FWA，[10-K FY2025](https://www.sec.gov/Archives/edgar/data/732712/000073271226000007/vz-20251231.htm)）。

**段永平式点评**：一家成熟到无线用户净增归零的公司，连续三年用并购（TracFone→Frontier→Starry）制造增长。并购不是商业模式的一部分，是**内生增长枯竭的替身**。Frontier 买入的是铜网+光纤，其中铜网是负资产（折旧、维护、流失），"3000 万 passings"里有多少能变成光纤付费用户，10-K 自己也只说"expected to provide opportunities"——这是推测，不是承诺。

---

## 二、定价权：来源与边界

**定价权来源（可验证的三条）**：

1. **频谱+网络是准公共品，区域上接近独占**。美国无线市场三家（VZ/AT&T/T-Mobile）+ 一家 MVNO 巨头（T-Mobile 的 T‑Mobile 与 Verizon 互有 MVNO 协议）。Verizon 与 Charter/Comcast 签有长期 MVNO 协议（[4Q25 新闻稿](https://www.verizon.com/about/news/verizon-delivers-2025-financial-guidance-highest-quarterly-net-adds)）——意味着它的网络资产在零售之外还能批发变现。频谱是稀缺管制资源，新进入者无法复制。
2. **postpaid 月费持续提价且用户接受**：ARPA 一年 +$6（$141.31→$147.36，[4Q25 FOI](https://www.verizon.com/about/sites/default/files/2026-01/vz_4q25_foi_013026.pdf)），同期 churn 从 1.52% 升到 1.64%——**提价与流失上升并存**，说明定价权有边界：提价能收，但收的代价是流失加速。
3. **家庭宽带靠独家光纤走廊**：Fios 在其 9 个中东部州+华盛顿特区是光纤独家或主导（[FY2022 10-K](https://www.sec.gov/Archives/edgar/data/732712/000073271223000012/vz-20221231.htm) 描述其 100% 光纤网络区域）；Frontier 交割后覆盖 31 州，但 Frontier 区域同样有 AT&T 光纤/Comcast 有线竞争——**这不是新垄断，是买来的份额**。

**定价权的反证（可反驳点）**：
- 2025 年公司为抢量推出"4 线 $100/月"等促销（CNBC 报道，[链接](https://www.cnbc.com/2026-01-30/verizon-vz-q4-earnings.html)）——需要打折才能维持净增，这是**定价权正在被侵蚀**的直接证据，与"行业最佳网络"的叙事并存。
- 10-K 自己承认 wireless service revenue 增长"expected to be approximately flat in 2026"（[4Q25 新闻稿](https://www.verizon.com/about/news/verizon-delivers-2025-financial-guidance-highest-quarterly-net-adds) 指引）——提价红利已接近打满。

**判定**：有区域垄断属性、有真实但**递减**的定价权。这不是"提价没人走"的生意，是"提价走一批、促销留一批"的存量拉锯。

---

## 三、转换成本 / 网络效应 / 规模效应：逐条验证

### 3.1 转换成本：**部分成立**

- 成立的部分：设备融资计划（36 个月分期，[FY2022 10-K](https://www.sec.gov/Archives/edgar/data/732712/000073271223000012/vz-20221231.htm)）把用户锁 3 年；多线家庭套餐（户均 2.95 部，[4Q25 FOI](https://www.verizon.com/about/sites/default/files/2026-01/vz_4q25_foi_013026.pdf)）提高整户迁移摩擦；eSIM/号码携带在美国仍有流程摩擦。
- 不成立的部分：churn 1.64%（月）≈ 年化 ~16%——**每年约 1/6 的 postpaid 用户在换网**。真有强转换成本的话，这个数字不会是这个量级。转换成本是"摩擦"，不是"墙"。

### 3.2 网络效应：**弱（仅通话网络的传统效应）**

- 经典电话网络效应（"所有人都用你才能接到电话"）在语音时代成立，在数据时代已被削弱：跨网通话/短信互通，VoIP/WhatsApp 等 OTT 进一步绕开运营商。
- 真正的"网络效应"在**对手那边**：T‑Mobile 2020 与 Sprint 合并后拥有全美国最大的频谱组合，其"美国最大网络"的品牌定位直接打击 Verizon 的核心卖点（网络质量）。Verizon 自己 2025 年的应对是促销+品牌重塑（Visible 等，[4Q25 新闻稿](https://www.verizon.com/about/news/verizon-delivers-2025-financial-guidance-highest-quarterly-net-adds)）——这是**守势**动作。
- 判定：Verizon 没有现代意义上的网络效应护城河。它的"网络"是**基础设施资产**，护城河来自**资本壁垒+频谱管制**，不来自用户互连。

### 3.3 规模效应：**成立，但是双刃剑**

- 成立：147M 连接摊薄网络成本；2025 capex $17.0B（[10-K FY2025](https://www.sec.gov/Archives/edgar/data/732712/000073271226000007/vz-20251231.htm)），OCF $37.1B（facts.md: 2025 经营现金流 37,137）→ FCF $20.1B（[4Q25 新闻稿](https://www.verizon.com/about/news/verizon-delivers-2025-financial-guidance-highest-quarterly-net-adds)）——规模确实转化为现金。
- 双刃：capex 占营收 12.3%、FCF 只占 OCF 的 54%——**规模效应的大部分被折旧和再投资吃掉**，股东拿到的 FCF 是"剩"出来的。对比工商企业（capex 占营收 3–5%），电信的规模效应**以持续的巨额资本消耗为代价**，这正是 facts.md 业态说明强调的。
- 2026 指引 capex 降至 $16.0–16.5B（[4Q25 新闻稿](https://www.verizon.com/about/news/verizon-delivers-2025-financial-guidance-highest-quarterly-net-adds)）——管理层在主动压资本开支换 FCF，但这意味着网络质量护城河在**投资收缩**中缓慢贬值（推测，需 2–3 年网络质量第三方测量验证）。

---

## 四、净利质量：2021/2022 为什么"虚高"（回应 facts.md 提示）

facts.md 显示 2021 净利 $22,065M、2022 净利 $21,256M，明显高于 2023 的 $11,614M。从 [FY2022 10-K](https://www.sec.gov/Archives/edgar/data/732712/000073271223000012/vz-20221231.htm)（Special Items 章节）查明：

| 年份 | 一次性/非经常项目（税前） |
|---|---|
| 2021 | Verizon Media 出售净收益 $706M + 出售 Apollo 合伙权益收益 ~$1.0B + 养老金精算收益 $2.4B；**减**：提前偿债成本 $3.5B、频谱牌照损失 $223M |
| 2022 | 养老金精算收益 **$1.7B**（其中 $7.0B 来自贴现率从 2.9%→5.2% 的会计调整，被 $5.5B 投资回报差异抵回大半）；**减**：提前偿债成本 $1.2B |

**结论**：2021/2022 的净利高点 = **媒体资产处置收益 + 利率驱动的养老金会计收益**，与经营无关。剔除后，核心经营（EBITDA）2021 $48.4B、2022 $47.9B、2025 $50.0B——六年里只涨了 3%。这才是这门生意的真实斜率。

---

## 五、10 年后差异化还在吗？

**答案：部分在，但比现在薄。**

- **还在的**：
  1. 频谱牌照的物理稀缺性 10 年后仍是进入壁垒（新玩家买不到足够频谱覆盖全国）；
  2. 147M 连接 + 1630 万光纤/FWA 连接（[4Q25 新闻稿](https://www.verizon.com/about/news/verizon-delivers-2025-financial-guidance-highest-quarterly-net-adds)）构成的双网资产，10 年后依然是全美前三的固定+移动组合；
  3. 企业/政府客户（21% 收入，含公共部门、物联网）对网络供应商的粘性在 10 年尺度上依然强（专线迁移是年级别的工程）。

- **变薄的**：
  1. **"网络质量第一"的品牌差异化已被 T‑Mobile 追平并反超叙事**——Verizon 2025 年靠促销抢量（[CNBC](https://www.cnbc.com/2026-01-30/verizon-vz-q4-earnings.html)）本身就是承认：它必须用价格防守，而价格防守是差异化流失的信号。
  2. 5G 之后，**无线技术代差周期拉长**（4G→5G 用了 10 年没有改变用户选择格局），未来 6G/卫星（T‑Mobile 与 Starlink 合作）对"覆盖"维度的差异化是降维打击（推测，基于行业公开信息，无 VZ 一手证据）。
  3. 固定宽带端，Frontier 的铜网资产 10 年后大概率是负担（光改成本），不是差异化。

**段永平式判定**：10 年后 Verizon 还在，但它的"好生意"属性取决于**提价权能否跑赢流失+资本开支**，而不是网络有多先进。它更像**公用事业**（收月租、重资产、弱成长、高分红），不像消费品牌（定价权随品牌复利增长）。

---

## 六、财务画像（facts.md 数字 + 取证补充）

| 项 | 值 | 来源 |
|---|---|---|
| 市值 | $187.35B | facts.md: market_cap |
| 5 年 PE 区间 | 7.35–15.4（中位 12.73），当前 10.9 | facts.md: pe_fy_end |
| TTM EPS / PE | $3.84 / 11.57 | facts.md: pe_on_ttm_eps |
| FY2025 营收 / 净利 / EPS | $138,191M / $17,174M / $4.06 | facts.md |
| FY2025 OCF / FCF | $37,137M / $20.1B | facts.md / [4Q25 新闻稿](https://www.verizon.com/about/news/verizon-delivers-2025-financial-guidance-highest-quarterly-net-adds) |
| FY2025 capex | $17,011M | [10-K FY2025](https://www.sec.gov/Archives/edgar/data/732712/000073271226000007/vz-20251231.htm) |
| 总债务 | 无担保债务 $131.1B（2025Q4），净无担保债务 $110.1B，净债/调整 EBITDA = 2.2x | [4Q25 新闻稿](https://www.verizon.com/about/news/verizon-delivers-2025-financial-guidance-highest-quarterly-net-adds) |
| 股息 | FY2025 申报 3 季 $2.08（facts.md 注明缺 Q4，实际更高）；4.68%（低估口径） | facts.md: dps_latest_fy / dividend_yield_pct |
| 2026 指引 | 调整 EPS $4.90–4.95（+4–5%），OCF $37.5–38.0B，capex $16.0–16.5B，FCF ≥$21.5B | [4Q25 新闻稿](https://www.verizon.com/about/news/verizon-delivers-2025-financial-guidance-highest-quarterly-net-adds) |

**股东回报的算术**：$20B FCF 对 $187B 市值 ≈ 10.7% FCF 收益率（2025 实际），加上 ~4.7% 股息（若股息由 FCF 支付则与 FCF 收益率有重叠——股息 $8.8B 量级占 FCF 的 ~44%），股东真实现金回报大约在 7–9% 区间（口径说明：股息未单列 FCF 扣减，此处为粗略边界，非精确值，标注为**推测**）。

---

## 七、这是不是一门好生意？（段永平式总评）

**好生意的三个标准，逐条打分**：

1. **差异化**：有（频谱+网络规模+区域光纤独家），但是**资产型差异化**，不是品牌型差异化。资产会折旧、会被追赶。→ **中等**
2. **定价权**：有但递减（ARPA +4%/年 与 churn 上升并存，促销抢量常态化）。→ **中等偏下**
3. **资本效率**：差。capex 12.3% 营收、FCF 仅 OCF 的 54%、债务 $131B。每一美元经营利润要先喂饱网络再轮到股东。→ **差**

**合成判断**：这是**一门"还行"的生意，不是"好"的生意**。它的正确参照系是公用事业（AT&T、电力、水务），不是消费品牌。它的特点：
- 需求刚性强（手机+宽带是必需品）→ 现金流可预测性高 ✓
- 但增长靠并购、提价空间接近打满、流失率上升 → 成长性弱 ✗
- 资本密集、折旧吞噬利润 → 股东回报被压薄 ✗
- 管理层 2025 年换帅（CEO Dan Schulman，2025-10 上任）并宣布裁员 13,000+（[CNBC](https://www.cnbc.com/2026-01-30/verizon-vz-q4-earnings.html)）→ 处于**经营拐点**，2026 指引（EPS +4–5%）是"turnaround"叙事，尚未被 2–3 个季度的执行验证（推测）。

**我最可能错在哪**：我把"促销抢量+churn 上升"读成定价权侵蚀，但如果 2026 年 postpaid 净增真做到 75–100 万（公司指引）且 churn 回落到 1.4% 以下，说明 2025 是**管理层失误的一次性低谷**而非结构性流失，那这门生意的定价权评级要上调，10 年差异化判断也要更乐观。反之，如果 Frontier 交割后 FCF 因光改 capex 反弹而达不到 $21.5B，则"公用事业现金奶牛"的叙事会被证伪。这两个都是可证伪的。

---

**结论**：Verizon 是一门现金流可预测但资本密集、增长靠并购、定价权递减的成熟公用事业型生意——10 年后差异化仍在但更薄，它值"稳定现金回报"的钱，不值"成长"的钱；当前 10.9x PE 处于 5 年区间中位下方（facts.md: pe_fy_end），定价合理但未到"明显便宜"。

**评分**：3 / 5（5=行业最优生意+合理价，1=生意本身有致命缺陷）

**最不确定的一点**：2025 年的 churn 上升（1.52%→1.64%）和促销依赖，到底是 Schulman 换帅期的**一次性低谷**（2026 净增 75–100 万可验证），还是 T‑Mobile 频谱优势下的**结构性流失**——这一条决定这门生意是 3 分还是 2 分。

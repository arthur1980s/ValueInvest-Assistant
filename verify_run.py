#!/usr/bin/env python3
"""ValueInvest 运行目录合规校验（不联网、纯 stdlib）。

检查一次研究运行是否产出"契约要求"的工件，而不是产出"看起来很长的报告"。
判据（硬性，缺一即 FAIL）：
  facts.md/json 存在；meta.json 记录数据截止日与阶段状态
  01~04 分析师报告：每份含结论行 + 评分 + ≥1 数据引用
  05/06 辩论第一轮：各 ≥5 条带出处的证据
  07/08 辩论第二轮：含"最强反对意见" + 立场是否改变
  09 决策：强制结论（通过/不通过/灰色）+ ≥3 档价格区间 + 风控检查 + 数据核验记录

用法：python3 verify_run.py <run_dir>
"""
import json
import re
import sys
from pathlib import Path

ANALYSTS = {"01-business.md": "商业模式(段永平)", "02-financial.md": "财务估值(巴菲特)",
            "03-industry.md": "行业竞争(芒格)", "04-risk.md": "风险管理层(李录)"}
DEBATE1 = {"05-bull-r1.md": "多头", "06-bear-r1.md": "空头"}
DEBATE2 = {"07-bull-r2.md": "多头反驳", "08-bear-r2.md": "空头反驳"}
CITE = re.compile(r"(出处|来源|数据源|SOURCE|facts\.md|年报|财报|官网|公告)")


def nonempty(p: Path, minlen: int) -> bool:
    return p.exists() and len(p.read_text(encoding="utf-8").strip()) >= minlen


def check(rd: Path):
    res, fails = [], []

    def ok(cond, name, detail=""):
        res.append((("✅" if cond else "❌"), name, detail))
        if not cond:
            fails.append(name)
        return cond

    ok(nonempty(rd / "facts.md", 400) and nonempty(rd / "facts.json", 200), "facts 事实包存在")
    if (rd / "meta.json").exists():
        m = json.loads((rd / "meta.json").read_text(encoding="utf-8"))
        ok(bool(m.get("data_cutoff")) and bool(m.get("stages")), "meta.json 有 data_cutoff + stages",
           f"cutoff={m.get('data_cutoff')} stages={m.get('stages')}")
    else:
        ok(False, "meta.json 存在")

    for f, role in ANALYSTS.items():
        p = rd / f
        txt = p.read_text(encoding="utf-8") if p.exists() else ""
        ok(nonempty(p, 800) and "结论" in txt and re.search(r"评分|打分|\d\s*/\s*5", txt) and CITE.search(txt),
           f"{role}报告({f})", f"{len(txt)}字")

    for f, role in DEBATE1.items():
        txt = (rd / f).read_text(encoding="utf-8") if (rd / f).exists() else ""
        n = len(re.findall(r"^\s*[-*\d]", txt, re.M))
        ok(nonempty(rd / f, 500) and n >= 5 and CITE.search(txt), f"{role}第一轮({f})", f"条目{n}")
    for f, role in DEBATE2.items():
        txt = (rd / f).read_text(encoding="utf-8") if (rd / f).exists() else ""
        ok(nonempty(rd / f, 400) and "最强反对意见" in txt and ("立场" in txt or "是否改变" in txt),
           f"{role}第二轮({f})", f"{len(txt)}字")

    d = (rd / "09-decision.md").read_text(encoding="utf-8") if (rd / "09-decision.md").exists() else ""
    ok(bool(re.search(r"强制结论|结论[:：]\s*(通过|不通过|灰色|买入|回避|观望)", d)), "决策含强制结论")
    ok(len(re.findall(r"(激进|稳健|保守)", d)) >= 3, "决策含 ≥3 档分层建议")
    ok(len(re.findall(r"\d+(\.\d+)?\s*[-~至]\s*\d+(\.\d+)?", d)) >= 3, "决策含 ≥3 个价格区间")
    ok(bool(re.search(r"风控|仓位|集中度|止损", d)), "决策含风控检查")
    ok(bool(re.search(r"核验|验算|financial_rigor|交叉验证", d)), "决策含数据核验记录")

    w = max(len(x[1]) for x in res) + 2
    print(f"运行目录: {rd}")
    for status, name, detail in res:
        print(f"  {status} {name:<{w}} {detail}")
    print(f"\n判决: {'✅ PASS（可发布）' if not fails else '❌ FAIL（打回，缺: ' + ', '.join(fails) + '）'}")
    return 1 if fails else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(check(Path(sys.argv[1]).expanduser()))

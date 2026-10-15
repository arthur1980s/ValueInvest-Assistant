#!/usr/bin/env python3
"""ValueInvest 报告渲染：运行目录 → 单文件自包含 HTML（双击可开、离线可分享）。

设计取舍（替代原方案的 Quarto Dashboards）：
  - Quarto 的 embed-resources: true 本质就是「把 CSS/JS 内联」，本脚本用 stdlib + mistune 直接做到，
    省掉 Quarto CLI + pandoc 依赖；渲染引擎用已安装的 mistune 3.x（表格默认支持）。
  - 图表不引 Plotly（自包含得内联 ~3.5MB JS），评分/区间用纯 CSS 条形；要真图时再议。
  - 只读运行目录，不改任何工件；缺文件的运行（跑到中途）也能渲染，缺项显式标注。

用法：
  python render_report.py <run_dir> [-o report.html]
  python render_report.py --selftest
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ANALYSTS = [("01-business.md", "① 商业模式", "段永平视角"),
            ("02-financial.md", "② 财务估值", "巴菲特视角"),
            ("03-industry.md", "③ 行业竞争", "芒格视角"),
            ("04-risk.md", "④ 风险与管理层", "李录视角")]
DEBATE_R1 = [("05-bull-r1.md", "多头 · 第1轮", "bull"), ("06-bear-r1.md", "空头 · 第1轮", "bear")]
DEBATE_R2 = [("07-bull-r2.md", "多头 · 第2轮", "bull"), ("08-bear-r2.md", "空头 · 第2轮", "bear")]
REQUIRED = [f for f, _, _ in ANALYSTS] + [f for f, _, _ in DEBATE_R1] + [f for f, _, _ in DEBATE_R2] + ["09-decision.md"]

CSS = """
:root{--ink:#16191d;--mut:#6b7280;--line:#e5e7eb;--bg:#fff;--soft:#f7f8fa;
--pass:#0f7b46;--fail:#b42318;--grey:#a15c07;--bull:#0f7b46;--bear:#b42318}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);line-height:1.65;
font:15px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans CJK SC","PingFang SC","Microsoft YaHei",sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:32px 24px 80px}
h1{font-size:26px;margin:0 0 4px}h2{font-size:19px;margin:40px 0 12px;padding-bottom:6px;border-bottom:2px solid var(--line)}
h3{font-size:16px;margin:20px 0 8px}h4{font-size:14px;margin:14px 0 6px;color:var(--mut)}
a{color:#0b5cad}
code,pre{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:12.5px}
pre{background:var(--soft);border:1px solid var(--line);border-radius:6px;padding:10px;overflow-x:auto}
code{background:var(--soft);padding:1px 4px;border-radius:3px}
table{border-collapse:collapse;width:100%;margin:10px 0;font-size:13.5px;display:block;overflow-x:auto}
th,td{border:1px solid var(--line);padding:6px 9px;text-align:left;vertical-align:top}
th{background:var(--soft);font-weight:600;white-space:nowrap}
blockquote{margin:10px 0;padding:8px 14px;border-left:3px solid #d0d5dd;background:var(--soft);color:#3f4650}
hr{border:0;border-top:1px solid var(--line);margin:24px 0}
.sub{color:var(--mut);font-size:13.5px}
.hdr{border-bottom:1px solid var(--line);padding-bottom:16px}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
.chip{border:1px solid var(--line);border-radius:999px;padding:3px 11px;font-size:12.5px;background:var(--soft)}
.chip.pass{color:var(--pass);border-color:#bfe3cf;background:#f0faf4}
.chip.fail{color:var(--fail);border-color:#f3c9c5;background:#fdf3f2}
.chip.grey{color:var(--grey);border-color:#f0dcb5;background:#fdf8ee}
.verdict{margin:20px 0 6px;padding:16px 18px;border-radius:10px;border:1px solid var(--line);background:var(--soft)}
.verdict .big{font-size:20px;font-weight:700}
.verdict.fail{border-color:#f3c9c5;background:#fdf3f2}.verdict.pass{border-color:#bfe3cf;background:#f0faf4}
.verdict.grey{border-color:#f0dcb5;background:#fdf8ee}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin:14px 0}
.card{border:1px solid var(--line);border-radius:9px;padding:12px 14px;background:#fff}
.card .k{font-size:12.5px;color:var(--mut)}
.card .v{font-size:17px;font-weight:650;margin-top:3px;word-break:break-word}
.bar{height:8px;border-radius:99px;background:var(--line);overflow:hidden;margin-top:8px}
.bar>i{display:block;height:100%;background:#344054}
.bar.bull>i{background:var(--bull)}.bar.bear>i{background:var(--bear)}.bar.analyst>i{background:#3b6ea5}
.block{border:1px solid var(--line);border-radius:9px;margin:12px 0;overflow:hidden}
.block>.bh{display:flex;justify-content:space-between;gap:10px;align-items:baseline;
padding:9px 14px;background:var(--soft);border-bottom:1px solid var(--line);font-weight:600;font-size:14px}
.block>.bb{padding:4px 16px 14px}
details{border:1px solid var(--line);border-radius:9px;margin:12px 0;overflow:hidden}
details>summary{cursor:pointer;padding:10px 14px;background:var(--soft);font-weight:600;font-size:14px}
details>.dbody{padding:4px 16px 14px;border-top:1px solid var(--line)}
.tier{border-left:3px solid var(--line);padding:2px 0 2px 12px;margin:8px 0}
.tier b{font-size:14px}
.todo{color:var(--grey);background:#fdf8ee;border:1px dashed #e3c88f;border-radius:8px;padding:8px 12px;font-size:13px}
footer{margin-top:48px;padding-top:16px;border-top:1px solid var(--line);color:var(--mut);font-size:12.5px}
@media print{.wrap{max-width:none;padding:0}details{break-inside:avoid}details>.dbody{display:block!important}}
"""


HEAD = re.compile(r"^(#+)(\s)", re.M)


def md(text: str, demote: int = 0) -> str:
    """markdown → html。demote>0 时把标题降级，避免报告内小标题抢占结构层级。
    围栏代码块（```…```）不参与降级，否则会改写里面的注释。"""
    if demote:
        chunks = text.split("```")
        for i in range(0, len(chunks), 2):
            chunks[i] = HEAD.sub(lambda m: "#" * min(6, len(m.group(1)) + demote) + m.group(2), chunks[i])
        text = "```".join(chunks)
    import mistune
    return mistune.html(text)


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def inline(text: str) -> str:
    """单行 markdown → HTML 片段：去掉 mistune 包裹的 <p>...</p>。
    （不要写成 f-string 里的 removeprefix('</p>\\n')——反斜杠在 f-string 表达式里
    只有 Python 3.12+ 允许，3.11 会 SyntaxError。CI 就是靠这条抓到的。）"""
    h = md(text).strip()
    return h[3:-4] if h.startswith("<p>") and h.endswith("</p>") else h


def read(rd: Path, name: str) -> str | None:
    p = rd / name
    return p.read_text(encoding="utf-8") if p.exists() else None


def score_num(s: str | None) -> float | None:
    """从 '3.5/5 灰色偏通过' 这类串里取分值。"""
    if not s:
        return None
    m = re.search(r"(\d+(?:\.\d+)?)\s*/\s*5", s)
    if m:
        return float(m.group(1))
    m = re.search(r"(\d+(?:\.\d+)?)", s)
    return float(m.group(1)) if m else None


VERDICT_WORDS = [("不通过", "fail"), ("不建仓", "fail"), ("回避", "fail"), ("卖出", "fail"), ("不建议", "fail"),
                 ("灰色", "grey"), ("观望", "grey"),
                 ("通过", "pass"), ("买入", "pass"), ("建仓", "pass")]


def verdict_class(v: str) -> str:
    """按结论里**最先出现**的判定词上色（同一位置取更长的词，如「不建仓」优先于「建仓」）。
    不要只看包含关系：'灰色地带——现价不建仓；$40 以下转为通过' 这类混合结论会判错色。"""
    hits = [(v.find(w), -len(w), c) for w, c in VERDICT_WORDS if w in v]
    return min(hits)[2] if hits else "grey"


def tiers(text: str | None) -> list[tuple[str, str]]:
    """从 09-decision.md 抽 激进/稳健/保守 三档（原文照搬，不重算）。
    表格行（| 档 | 区间 | 条件 |）会去掉单元格分隔符，避免卡片里露出裸竖线。"""
    out, seen = [], set()
    for line in (text or "").splitlines():
        for lab in ("激进", "稳健", "保守"):
            if lab in line and lab not in seen and re.search(r"\d", line):
                body = line.replace("**", "").strip()
                if body.startswith("|"):
                    cells = [c.strip() for c in body.strip("|").split("|")]
                    cells = [c for i, c in enumerate(cells) if not (i == 0 and c.startswith(lab))]
                    body = " ｜ ".join(c for c in cells if c)
                else:
                    body = re.sub(r"^[\s>*\-•]+", "", body)
                out.append((lab, body))
                seen.add(lab)
    return sorted(out, key=lambda x: ("激进", "稳健", "保守").index(x[0]))


def block(title: str, meta_line: str, body_md: str | None, css_class: str = "", score: str | None = None) -> str:
    if body_md is None:
        return (f'<div class="block"><div class="bh"><span>{esc(title)}</span>'
                f'<span class="sub">{esc(meta_line)}</span></div>'
                f'<div class="bb"><div class="todo">未产出（该阶段未完成或不适用）</div></div></div>')
    sc = score_num(score) if score else None
    bar = ""
    if sc is not None:
        bar = f'<div class="bar {css_class}"><i style="width:{min(sc, 5) / 5 * 100:.1f}%"></i></div>'
    return (f'<div class="block"><div class="bh"><span>{esc(title)}'
            f'{"　" + esc(score) if score else ""}</span>'
            f'<span class="sub">{esc(meta_line)}</span></div>{bar}'
            f'<div class="bb">{md(body_md, 2)}</div></div>')


def render(rd: Path) -> str:
    meta = {}
    if (rd / "meta.json").exists():
        try:
            meta = json.loads((rd / "meta.json").read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            meta = {"_meta_error": f"meta.json 解析失败：{e}"}
    stages = meta.get("stages", {}) or {}
    ticker = meta.get("ticker") or rd.name.split("-")[0]
    company = meta.get("company") or ticker
    cutoff = meta.get("data_cutoff") or "未标注"
    gaps = meta.get("gaps", []) or []

    decision_md = read(rd, "09-decision.md")
    verdict = (stages.get("decision") or {}).get("verdict") or ""
    if not verdict and decision_md:
        m = re.search(r"(?:强制结论|结论)[^\n]{0,80}", decision_md)
        verdict = m.group(0) if m else ""
    if not verdict:
        verdict = "无结论（运行未完成）" if not decision_md else "结论未在 meta.json 标注"
    vcls = verdict_class(verdict)

    scores = (stages.get("analysts") or {}).get("scores", {}) or {}
    r1 = (stages.get("debate_r1") or {}).get("scores", {}) or {}
    r2 = (stages.get("debate_r2") or {}).get("scores", {}) or {}
    present = [f for f in REQUIRED if (rd / f).exists()]
    missing = [f for f in REQUIRED if not (rd / f).exists()]
    done = [f for f in REQUIRED if (rd / f).stat().st_size > 200] if all(
        (rd / f).exists() for f in REQUIRED) else present

    nums = [n for n in (score_num(s) for s in scores.values()) if n is not None]
    avg = f"{sum(nums) / len(nums):.2f}/5" if nums else "—"

    # ---- 头部 + 值框
    parts = [
        '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">',
        f'<meta name="viewport" content="width=device-width,initial-scale=1">',
        f'<title>ValueInvest 研究报告 · {esc(ticker)}</title>',
        f"<style>{CSS}</style></head><body><div class='wrap'>",
        '<div class="hdr"><h1>ValueInvest 研究报告 · ', esc(company), f'（{esc(ticker)}）</h1>',
        f'<div class="sub">市场 {esc(meta.get("market") or "—")} ｜ 数据截止 {esc(cutoff)} ｜ '
        f'运行目录 {esc(rd.name)} ｜ 渲染于 {datetime.now():%Y-%m-%d %H:%M}</div>',
        '<div class="chips">',
        f'<span class="chip">工件 {len(present)}/{len(REQUIRED)}</span>',
        f'<span class="chip {"pass" if len(present) == len(REQUIRED) else "grey"}">'
        f'{"全部阶段已产出" if not missing else "缺 " + "、".join(missing)}</span>',
        f'<span class="chip">缺口 {len(gaps)} 条</span>' if gaps else '<span class="chip pass">事实包无缺口</span>',
        "</div></div>",
        f'<div class="verdict {vcls}"><div class="sub">强制结论（来自 09-decision.md / meta.json）</div>',
        f'<div class="big">{esc(verdict)}</div></div>',
    ]
    if meta.get("_meta_error"):
        parts.append(f'<div class="todo">{esc(meta["_meta_error"])}</div>')
    cards = [("公司 / 代码", f"{company}（{ticker}）"), ("市场", meta.get("market") or "—"),
             ("数据截止", cutoff), ("四视角均分", avg),
             ("阶段进度", f"{len(present)}/{len(REQUIRED)}"),
             ("缺口", f"{len(gaps)} 条" if gaps else "无")]
    parts.append('<div class="cards">' + "".join(
        f'<div class="card"><div class="k">{esc(k)}</div><div class="v">{esc(v)}</div></div>'
        for k, v in cards) + "</div>")

    if gaps:
        parts.append('<h2>⚠️ 事实包缺口（不得脑补，引用时须一并声明）</h2><ul>'
                     + "".join(f"<li>{inline(g)}</li>" for g in gaps) + "</ul>")

    # ---- ① 四视角
    parts.append("<h2>① 四个分析视角（同一份事实包，互相不可见）</h2>")
    for f, title, role in ANALYSTS:
        txt = read(rd, f)
        at = (stages.get("analysts") or {}).get("at", "")
        parts.append(block(f"{title}（{role}）", f"{f} ｜ {at}" if txt else f"{f} ｜ 未产出",
                           txt, "analyst", scores.get(f[:-3])))

    # ---- ② 辩论
    parts.append("<h2>② 多空两轮对抗</h2>")
    for label, group, stage in (("第 1 轮 · 各自独立成稿", DEBATE_R1, "debate_r1"),
                                ("第 2 轮 · 对手第 1 轮已回喂", DEBATE_R2, "debate_r2")):
        parts.append(f"<h3>{label}</h3>")
        for f, title, cls in group:
            txt = read(rd, f)
            parts.append(block(title, f"{f} ｜ " + ((stages.get(stage) or {}).get("at", "") or "未产出"),
                               txt, cls, (r1 if stage == "debate_r1" else r2).get(f[:-3])))
        note = (stages.get(stage) or {}).get("divergence") or (stages.get(stage) or {}).get("convergence")
        if note:
            tag = "分歧地图" if stage == "debate_r1" else "收敛情况"
            parts.append(f'<div class="card"><div class="k">{tag}（meta.json）</div>'
                         f'<div class="v" style="font-size:14px;font-weight:400">{esc(note)}</div></div>')

    # ---- ③ 决策
    parts.append("<h2>③ 决策与风控</h2>")
    ts = tiers(decision_md)
    if ts:
        parts.append('<div class="cards">' + "".join(
            f'<div class="card"><div class="k">{esc(lab)}档</div>'
            f'<div class="v" style="font-size:14px;font-weight:400">{md(body)}</div></div>' for lab, body in ts)
            + "</div><div class='sub'>三档区间照抄 09-decision.md 原文，本渲染器不重算。</div>")
    elif decision_md:
        parts.append('<div class="todo">09-decision.md 未抽出 激进/稳健/保守 三档——'
                     '渲染器按行匹配标签，请核对原文措辞。</div>')
    if decision_md:
        parts.append(f'<details open><summary>决策全文（09-decision.md）</summary><div class="dbody">{md(decision_md, 2)}</div></details>')
    else:
        parts.append('<div class="todo">决策层未产出。</div>')

    # ---- 事实包
    facts = read(rd, "facts.md")
    parts.append("<h2>④ 事实包（数字只由 datapack.py 产生）</h2>")
    if facts:
        parts.append(f'<details><summary>facts.md（{len(facts)} 字符）</summary><div class="dbody">{md(facts, 2)}</div></details>')
    else:
        parts.append('<div class="todo">facts.md 缺失——取数层未跑或被移动。</div>')
    if (rd / "facts.json").exists():
        parts.append(f'<div class="sub">同目录另有 facts.json（{((rd / "facts.json").stat().st_size) / 1024:.1f} KB，供程序引用）。</div>')

    parts.append('<footer>'
                 '<b>定位声明：观测层，不是判据层。</b>本文档不参与量化因子池判定、不推翻任何既有结论，'
                 '与既有结论冲突时并列保留、交人判断。AI 输出置信度 ≠ 投资确定性。'
                 '结论必须与其适用范围捆绑引用（写明前提与失效条件）；缺失项已在文中显式标注，未做任何填充。<br>'
                 f'生成：ValueInvest（render_report.py）｜ 数据截止 {esc(cutoff)} ｜ 单文件自包含，无外部依赖。'
                 "</footer></div></body></html>")
    return "".join(parts)


def selftest() -> int:
    """渲染真实运行目录并断言「自包含 / 关键内容在位」。"""
    repo = Path(__file__).resolve().parent
    rd = repo / "runs" / "T-20261014"
    assert rd.exists(), f"自测需要一个真实运行目录：{rd}"
    out = Path(tempfile.mkdtemp()) / "selftest.html"
    out.write_text(render(rd), encoding="utf-8")
    doc = out.read_text(encoding="utf-8")
    checks = [
        (len(doc) > 20000, "输出不是空壳"),
        (doc.startswith("<!DOCTYPE html>") and doc.rstrip().endswith("</html>"), "HTML 结构闭合"),
        ("<style>" in doc and "</style>" in doc, "CSS 已内联"),
        (not re.search(r'<link[^>]+stylesheet|<script[^>]+src=|<img[^>]+src=', doc), "无外部资源引用（自包含）"),
        ("不通过（现价" in doc or "不通过" in doc, "强制结论在位"),
        ("事实包" in doc and "01-business.md" in doc and "09-decision.md" in doc, "章节与工件名在位"),
        ("<table>" in doc, "表格渲染成功（mistune）"),
        ("定位声明：观测层" in doc, "观测层边界声明在位"),
    ]
    bad = [n for ok, n in checks if not ok and n]
    for ok, n in checks:
        if n:
            print(f"  {'✅' if ok else '❌'} {n}")
    # 缺文件降级：渲染一个空目录不得抛异常
    empty = Path(tempfile.mkdtemp()) / "ZZZ-1"
    empty.mkdir()
    d2 = render(empty)
    ok2 = "无结论（运行未完成）" in d2 and len(d2) > 3000
    print(f"  {'✅' if ok2 else '❌'} 中途/空运行目录可降级渲染")
    # 三档抽取：表格行不得把裸竖线带进卡片，且必须按 激进/稳健/保守 排序
    tt = tiers("| 档位 | 价格区间 | 条件 |\n|---|---|---|\n| 保守 | $13 - 15 | 前提 |\n| 激进 | $19 - 20 | 前提 |\n")
    ok3 = ([l for l, _ in tt] == ["激进", "保守"] and "|" not in "".join(b for _, b in tt)
           and tt[0][1].startswith("$19"))
    print(f"  {'✅' if ok3 else '❌'} 三档抽取（去竖线 + 排序）")
    # 结论上色：按最先出现的判定词，混合结论（灰色+不建仓+通过）不得判成绿
    vc = [verdict_class("不通过（现价 $22.85 不建仓）"),
          verdict_class("灰色地带 —— 现价 $44.42 不建仓; $40.00 及以下转为通过(分层)"),
          verdict_class("通过（分层建仓）"), verdict_class("")]
    ok4 = vc == ["fail", "grey", "pass", "grey"]
    print(f"  {'✅' if ok4 else '❌'} 结论上色（混合结论取首个判定词）")
    if bad or not ok2 or not ok3 or not ok4:
        print(f"\n自测 FAIL: {bad or ['空目录降级' if not ok2 else '三档抽取' if not ok3 else '结论上色']}")
        return 1
    print(f"\n自测 PASS（{len(doc) / 1024:.1f} KB 单文件）")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="ValueInvest 运行目录 → 单文件自包含 HTML")
    ap.add_argument("run_dir", nargs="?", help="runs/<ticker>-<YYYYMMDD>")
    ap.add_argument("-o", "--out", help="输出路径（默认 <run_dir>/report.html）")
    ap.add_argument("--selftest", action="store_true", help="用真实运行目录做一次自包含自检")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.run_dir:
        ap.error("需要 run_dir（或用 --selftest）")
    rd = Path(a.run_dir).expanduser()
    if not rd.is_dir():
        print(f"❌ 不是目录: {rd}", file=sys.stderr)
        return 2
    out = Path(a.out).expanduser() if a.out else rd / "report.html"
    out.write_text(render(rd), encoding="utf-8")
    print(f"✅ {out}  ({out.stat().st_size / 1024:.1f} KB, 单文件自包含)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

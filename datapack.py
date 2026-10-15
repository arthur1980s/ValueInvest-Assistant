#!/usr/bin/env python3
"""ValueInvest 事实包（fact pack）构建器 —— 为辩论层提供有出处的确定性数字。

设计原则：数字来自脚本、不来自 LLM。所有分析 Agent 与多空辩论共读同一份
facts.json / facts.md，避免"多头一套数、空头另一套数"的假辩论。

用法：
    python datapack.py 600519 <run_dir>          # A股
    python datapack.py 00700   <run_dir>         # 港股
    python datapack.py T       <run_dir>         # 美股（SEC EDGAR XBRL + Nasdaq）
    python datapack.py T <run_dir> --cross-check <run_dir>/cross_check_<源>.json
    python datapack.py --verify <run_dir>        # 离线结构自检

美股路径需要给 SEC 一个可联系的 User-Agent（否则 403），用环境变量提供：
    export VALUEINVEST_SEC_UA="Your Name your@email.com"

依赖：akshare + pandas（A股/港股）、requests（美股）。见 requirements.txt。
"""
from __future__ import annotations   # 让 `Path | None` 这类 PEP 604 注解在 Python 3.9 上也能加载
                                      # （本机默认 python3 可能是 3.9，没有这行会在 import 阶段就 TypeError）
import argparse
import json
import os
import re
import socket
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path

warnings.filterwarnings("ignore")
socket.setdefaulttimeout(25)


def retry(fn, n=4, delay=2.0):
    """akshare 到东财/百度/巨潮的连接会被本网间歇性切断，重试窗口是必需的。"""
    last = None
    for i in range(n):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001 - 任何取数异常都重试
            last = e
            time.sleep(delay * (i + 1))
    raise last

SOURCES = {
    "price": "akshare stock_zh_a_daily/stock_zh_a_hist_tx (前复权；东财 hist 接口在本网被断，故新浪为主、腾讯为备)",
    "valuation": "akshare stock_zh_valuation_baidu (百度股市通)",
    "financials": "akshare stock_financial_abstract (交易所口径，按期)",
    "ratios": "akshare stock_financial_analysis_indicator",
    "dividend": "akshare stock_dividend_cninfo (巨潮资讯)",
    "business": "akshare stock_zyjs_ths (同花顺)",
    "hk_snapshot": "akshare stock_hk_financial_indicator_em",
    "hk_dividend": "akshare stock_hk_dividend_payout_em",
}


def _num(x):
    try:
        if x is None:
            return None
        f = float(x)
        return None if f != f else f  # NaN -> None
    except (TypeError, ValueError):
        return None


def classify(ticker: str) -> str:
    t = ticker.strip().upper()
    if t.endswith(".HK"):
        t = t[:-3]
    if re.fullmatch(r"\d{6}", t) and t[0] in "0369":
        return "A"
    if re.fullmatch(r"\d{1,5}", t):
        return "HK"
    if re.fullmatch(r"[A-Z]{1,5}([.-][A-Z]{1,2})?", t):
        return "US"
    return "UNKNOWN"


def build_a(ticker: str) -> dict:
    import akshare as ak

    out = {"ticker": ticker, "market": "A", "sources": SOURCES, "missing": [], "verification": []}

    # ---- 价格（新浪前复权为主，腾讯为备；历史序列统一前复权口径）----
    import pandas as pd

    def a_price():
        pref = "sh" if ticker[0] in "56" else ("bj" if ticker[0] == "8" else "sz")
        sym = pref + ticker
        end = datetime.now().strftime("%Y%m%d")
        try:
            df = retry(lambda: ak.stock_zh_a_daily(symbol=sym, start_date="20150101", end_date=end, adjust="qfq"))
            df = df.rename(columns={"date": "日期", "close": "收盘", "high": "最高", "low": "最低"})
            return df, "sina 新浪 stock_zh_a_daily(qfq)"
        except Exception:
            df = retry(lambda: ak.stock_zh_a_hist_tx(symbol=sym, start_date="20150101", end_date=end, adjust="qfq"))
            df = df.rename(columns={"date": "日期", "close": "收盘", "high": "最高", "low": "最低"})
            return df, "tencent 腾讯 stock_zh_a_hist_tx(qfq)"

    hist, px_src = a_price()
    hist["日期"] = pd.to_datetime(hist["日期"])
    hist = hist.dropna(subset=["收盘"]).sort_values("日期")
    price = _num(hist["收盘"].iloc[-1])
    out["sources"]["price"] = px_src
    out["snapshot"] = {"price": price, "price_date": str(hist["日期"].iloc[-1].date()), "price_adj": "qfq",
                       "outstanding_share": _num(hist["outstanding_share"].iloc[-1]) if "outstanding_share" in hist.columns else None}
    last = hist["日期"].iloc[-1]
    y1 = hist[hist["日期"] >= last - pd.Timedelta(days=365)]
    y5 = hist[hist["日期"] >= last - pd.Timedelta(days=365 * 5)]
    out["price_stats"] = {
        "ret_1y_pct": round((price / _num(y1["收盘"].iloc[0]) - 1) * 100, 1) if len(y1) else None,
        "ret_5y_pct": round((price / _num(y5["收盘"].iloc[0]) - 1) * 100, 1) if len(y5) else None,
        "cagr_5y_pct": round(((price / _num(y5["收盘"].iloc[0])) ** 0.2 - 1) * 100, 1) if len(y5) else None,
        "high_5y": _num(y5["最高"].max()), "low_5y": _num(y5["最低"].min()),
        "pct_below_5y_high": round((1 - price / _num(y5["最高"].max())) * 100, 1),
    }

    # ---- 估值与市值（百度股市通）----
    def baidu(indicator, period):
        df = retry(lambda: ak.stock_zh_valuation_baidu(symbol=ticker, indicator=indicator, period=period))
        v = df["value"].astype(float)
        return df, v

    mkt = None
    try:
        df, v = baidu("总市值", "近一年")
        mkt = _num(v.iloc[-1])
        out["snapshot"]["market_cap"] = mkt
        out["snapshot"]["market_cap_unit"] = "亿元"
    except Exception as e:
        out["missing"].append(f"总市值: {type(e).__name__}")
    band = {}
    for label, ind in (("pe_ttm", "市盈率(TTM)"), ("pb", "市净率")):
        try:
            df, v = baidu(ind, "近十年")
            cur = _num(v.iloc[-1])
            band[label] = {
                "current": cur,
                "pct_10y": round((v <= cur).mean() * 100, 1),
                "min_10y": _num(v.min()), "max_10y": _num(v.max()),
                "median_10y": _num(v.median()),
            }
        except Exception as e:
            out["missing"].append(f"{label}: {type(e).__name__}")
    for label, ind, p in (("pe_ttm_5y", "市盈率(TTM)", "近五年"), ("pb_5y", "市净率", "近五年")):
        try:
            df, v = baidu(ind, p)
            cur = _num(v.iloc[-1])
            band[label] = {"pct_in_window": round((v <= cur).mean() * 100, 1),
                           "min": _num(v.min()), "max": _num(v.max()), "median": _num(v.median())}
        except Exception:
            pass
    out["valuation"] = band

    # ---- 财报（年度序列 + 最新一期）----
    fa = retry(lambda: ak.stock_financial_abstract(symbol=ticker))
    periods = [c for c in fa.columns if re.fullmatch(r"\d{8}", str(c))]
    annuals = sorted([p for p in periods if p.endswith("1231")], reverse=True)[:6]
    latest = sorted(periods, reverse=True)[0]
    keys = [("营业总收入", "revenue"), ("归母净利润", "np_parent"), ("净利润", "np"),
            ("扣非净利润", "np_deducted"), ("股东权益合计(净资产)", "equity"),
            ("经营现金流量净额", "ocf"), ("净资产收益率(ROE)", "roe"),
            ("毛利率", "gross_margin"), ("销售净利率", "net_margin"), ("资产负债率", "debt_ratio"),
            ("基本每股收益", "eps"), ("每股净资产", "bvps"),
            ("每股企业自由现金流量", "fcf_ps"), ("商誉", "goodwill")]

    def pull(period):
        row = {}
        for _, r in fa.iterrows():
            for name, key in keys:
                if r["指标"] == name:
                    row.setdefault(key, _num(r.get(period)))
        return row

    out["financials_annual"] = {p: pull(p) for p in annuals}
    out["financials_latest_interim"] = {"period": latest, **pull(latest)}

    # 成长性（用年度口径，跨期同比）
    def cagr(key, years):
        a, b = out["financials_annual"].get(annuals[0], {}).get(key), out["financials_annual"].get(annuals[years], {}).get(key)
        if a and b and b > 0 and a > 0:
            return round(((a / b) ** (1 / years) - 1) * 100, 1)
        return None
    out["growth"] = {"revenue_cagr_5y_pct": cagr("revenue", 5), "np_parent_cagr_5y_pct": cagr("np_parent", 5),
                     "revenue_yoy_latest_annual_pct": None}
    try:
        y0, y1_ = out["financials_annual"][annuals[0]]["revenue"], out["financials_annual"][annuals[1]]["revenue"]
        out["growth"]["revenue_yoy_latest_annual_pct"] = round((y0 / y1_ - 1) * 100, 1)
    except Exception:
        pass

    # ---- 股本三路推导 + 市值两源互验（不心算，脚本给数）----
    ann = out["financials_annual"].get(annuals[0], {})
    shares = {
        "sina_outstanding_share": out["snapshot"].get("outstanding_share"),
        "from_market_cap_over_price": round(mkt * 1e8 / price, 0) if (mkt and price) else None,
        # 归母净利与每股收益同为「元」，直接相除即股本（勿再乘 1e8）
        "from_np_over_eps": round(ann["np_parent"] / ann["eps"], 0) if (ann.get("np_parent") and ann.get("eps")) else None,
    }
    out["shares"] = shares
    vals = [v for v in shares.values() if v]
    if len(vals) >= 2:
        spread = (max(vals) - min(vals)) / max(vals) * 100
        out["verification"].append({"check": f"股本 {len(vals)} 路互验", "values": shares, "spread_pct": round(spread, 2),
                                    "verdict": "一致" if spread <= 1 else ("存在差异，需核对(期间股本变动/口径)" if spread <= 5 else "重大差异，须查原始财报")})
    if mkt and price and shares["sina_outstanding_share"]:
        cap_sina = price * shares["sina_outstanding_share"] / 1e8
        err = abs(cap_sina - mkt) / mkt * 100
        out["verification"].append({"check": "市值两源互验（新浪价×股本 vs 百度总市值）",
                                    "sina_cap_yi": round(cap_sina, 2), "baidu_cap_yi": mkt, "diff_pct": round(err, 2),
                                    "verdict": "一致" if err <= 1 else ("存在差异" if err <= 5 else "重大差异，须查原始财报")})
    if mkt and ann.get("np_parent"):
        out["verification"].append({"check": "市值/PE 互验", "implied_pe_from_annual_np": round(mkt * 1e8 / ann["np_parent"], 2),
                                    "note": "由总市值与最近年度归母净利反算 PE，应与估值分位中的当前 PE(TTM) 同量级（TTM≠年度，允许差异）"})

    # ---- 分红（巨潮）----
    try:
        dv = retry(lambda: ak.stock_dividend_cninfo(symbol=ticker))
        dv = dv.dropna(subset=["派息比例"])
        rows = []
        for _, r in dv.tail(8).iterrows():
            rows.append({"report": str(r.get("报告时间")), "per10_cash": _num(r.get("派息比例")),
                         "ex_date": str(r.get("除权日"))})
        out["dividends"] = rows
        # 股息率按 TTM 口径：年度 + 中期/季度分红都要计（只取单次会低估近一半）
        d = dv.dropna(subset=["派息比例", "除权日"]).copy()
        d["除权日"] = pd.to_datetime(d["除权日"], errors="coerce")
        d = d.dropna(subset=["除权日"]).sort_values("除权日")
        if len(d) and price:
            ttm = d[d["除权日"] >= pd.Timestamp.now() - pd.Timedelta(days=365)]
            out["dividend"] = {"ttm_per_share": round(_num(ttm["派息比例"].sum()) / 10, 2),
                               "ttm_n_payments": int(len(ttm)),
                               "last_single_per_share": round(_num(d["派息比例"].iloc[-1]) / 10, 2),
                               "last_ex_date": str(d["除权日"].iloc[-1].date())}
            out["dividend_yield_pct_ttm"] = round(out["dividend"]["ttm_per_share"] / price * 100, 2)
            out["dividend_yield_pct_last_single"] = round(out["dividend"]["last_single_per_share"] / price * 100, 2)
    except Exception as e:
        out["missing"].append(f"分红: {type(e).__name__}")

    try:
        zy = retry(lambda: ak.stock_zyjs_ths(symbol=ticker))
        out["business"] = {k: str(zy[k].iloc[0]) for k in ("主营业务", "产品名称") if k in zy.columns}
    except Exception as e:
        out["missing"].append(f"主营: {type(e).__name__}")

    return out


def build_hk(ticker: str) -> dict:
    """港股：快照级（估值/分红）。5 年财报序列需另行取（aastocks / 披露易年报路径），见 README 的港股缺口说明。"""
    import akshare as ak
    sym = ticker.zfill(5)
    out = {"ticker": sym, "market": "HK", "sources": SOURCES, "missing": [], "verification": []}
    snap = retry(lambda: ak.stock_hk_financial_indicator_em(symbol=sym))
    s = snap.iloc[0]
    pick = {"price_unit": "HKD", "market_cap": _num(s.get("总市值(港元)")), "eps": _num(s.get("基本每股收益(元)")),
            "bvps": _num(s.get("每股净资产(元)")), "shares": _num(s.get("已发行股本(股)")),
            "pe": _num(s.get("市盈率")), "pb": _num(s.get("市净率")), "roe_pct": _num(s.get("股东权益回报率(%)")),
            "net_margin_pct": _num(s.get("销售净利率(%)")), "revenue": _num(s.get("营业总收入")),
            "np": _num(s.get("净利润")), "div_yield_pct": _num(s.get("股息率TTM(%)")),
            "dps_ttm": _num(s.get("每股股息TTM(港元)"))}
    out["snapshot"] = pick
    # ---- 价格（新浪）----
    try:
        import pandas as pd
        h = retry(lambda: ak.stock_hk_daily(symbol=sym, adjust="qfq"))
        h["date"] = pd.to_datetime(h["date"])
        h = h.dropna(subset=["close"]).sort_values("date")
        price = _num(h["close"].iloc[-1])
        last = h["date"].iloc[-1]
        y5 = h[h["date"] >= last - pd.Timedelta(days=365 * 5)]
        y1 = h[h["date"] >= last - pd.Timedelta(days=365)]
        out["sources"]["price"] = "sina 新浪 stock_hk_daily(qfq)"
        out["snapshot"].update({"price": price, "price_date": str(last.date()), "price_adj": "qfq"})
        out["price_stats"] = {
            "ret_1y_pct": round((price / _num(y1["close"].iloc[0]) - 1) * 100, 1) if len(y1) else None,
            "ret_5y_pct": round((price / _num(y5["close"].iloc[0]) - 1) * 100, 1) if len(y5) else None,
            "high_5y": _num(y5["high"].max()), "low_5y": _num(y5["low"].min()),
            "pct_below_5y_high": round((1 - price / _num(y5["high"].max())) * 100, 1),
        }
        if pick["market_cap"] and pick["shares"]:
            cap = price * pick["shares"]
            err = abs(cap - pick["market_cap"]) / pick["market_cap"] * 100
            out["verification"].append({"check": "市值两源互验（新浪价×股本 vs 快照总市值）",
                                        "sina_cap_yi": round(cap / 1e8, 2), "snapshot_cap_yi": round(pick["market_cap"] / 1e8, 2),
                                        "diff_pct": round(err, 2),
                                        "verdict": "一致" if err <= 1 else ("存在差异" if err <= 5 else "重大差异，须查原始财报")})
    except Exception as e:
        out["missing"].append(f"价格: {type(e).__name__}")
    if pick["market_cap"] and pick["shares"] and not out["snapshot"].get("price"):
        out["verification"].append({"check": "市值/股本", "note": f"价格未取到，隐含价 ≈ {pick['market_cap']/pick['shares']:.2f} HKD，需人工核对"})
    try:
        df = retry(lambda: ak.stock_hk_valuation_baidu(symbol=sym, indicator="市盈率(TTM)", period="近十年"))
        v = df["value"].astype(float); cur = _num(v.iloc[-1])
        out["valuation"] = {"pe_ttm": {"current": cur, "pct_10y": round((v <= cur).mean() * 100, 1),
                                       "min_10y": _num(v.min()), "max_10y": _num(v.max()), "median_10y": _num(v.median())}}
    except Exception as e:
        out["missing"].append(f"PE分位: {type(e).__name__}")
    try:
        dv = retry(lambda: ak.stock_hk_dividend_payout_em(symbol=sym))
        out["dividends"] = [{"fiscal_year": str(r["财政年度"]), "plan": str(r["分红方案"]), "ex_date": str(r["除净日"])}
                            for _, r in dv.head(6).iterrows()]
    except Exception as e:
        out["missing"].append(f"分红: {type(e).__name__}")
    out["missing"].append("5年财报序列（aastocks + 披露易年报路径，本脚本不取）")
    return out


SEC_UA = (os.environ.get("VALUEINVEST_SEC_UA")
          or "ValueInvest-Assistant (set VALUEINVEST_SEC_UA='Your Name your@email.com')")
# SEC 要求 User-Agent 形如 <应用名> <邮箱>，否则 403；未设置时会在美股取数前给出提示。


def _sec_get(url: str, cache_dir: Path | None = None, timeout: int = 90):
    """SEC 取数（带 UA 头；companyfacts 可达 10MB，落缓存避免重复下载）。"""
    import requests
    key = None
    if cache_dir is not None:
        key = cache_dir / (re.sub(r"[^A-Za-z0-9]+", "_", url)[-80:] + ".json")
        if key.exists() and key.stat().st_size > 1000:
            return json.loads(key.read_text(encoding="utf-8"))
    r = retry(lambda: requests.get(url, headers={"User-Agent": SEC_UA, "Accept-Encoding": "gzip, deflate"},
                                  timeout=timeout))
    r.raise_for_status()
    data = r.json()
    if key is not None:
        key.parent.mkdir(parents=True, exist_ok=True)
        key.write_text(json.dumps(data), encoding="utf-8")
    return data


def _sec_get_text(url: str, cache_dir: Path | None = None, timeout: int = 180):
    import requests
    key = None
    if cache_dir is not None:
        key = cache_dir / (re.sub(r"[^A-Za-z0-9]+", "_", url)[-70:] + ".xml")
        if key.exists() and key.stat().st_size > 10000:
            return key.read_text(encoding="utf-8", errors="ignore")
    r = retry(lambda: requests.get(url, headers={"User-Agent": SEC_UA}, timeout=timeout))
    r.raise_for_status()
    txt = r.text
    if key is not None:
        key.parent.mkdir(parents=True, exist_ok=True)
        key.write_text(txt, encoding="utf-8")
    return txt


def _sec_quarters(cik: int, facts: dict, cache: Path, tags=("Revenues", "NetIncomeLoss",
                  "NetIncomeLossAvailableToCommonStockholdersBasic", "EarningsPerShareDiluted",
                  "InterestIncomeExpenseNet", "NoninterestIncome")) -> dict:
    """最新季报的季度口径（companyfacts 会滞后，本例止于 FY2025；10-Q 原文才有 1Q/2Q26）。

    走 submissions → 最新 10-Q → XBRL 实例（*_htm.xml）流式解析，只取关心的标签。
    """
    import xml.etree.ElementTree as ET
    subs = _sec_get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json", cache)
    rec = subs["filings"]["recent"]
    qs = [(a, d, doc) for f, a, d, doc in zip(rec["form"], rec["accessionNumber"], rec["filingDate"], rec["primaryDocument"]) if f == "10-Q"]
    if not qs:
        return {}
    accn, filed, _doc = sorted(qs, key=lambda x: x[1])[-1]
    base = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accn.replace('-', '')}"
    idx = _sec_get(f"{base}/index.json", cache, timeout=60)
    inst = next((n for n in (it["name"] for it in idx["directory"]["item"]) if n.endswith("_htm.xml")), None)
    if not inst:
        return {}
    url = f"{base}/{inst}"
    txt = _sec_get_text(url, cache)          # 首次下载可达 ~18MB，之后走缓存
    tmp = cache / (re.sub(r"[^A-Za-z0-9]+", "_", url)[-70:] + ".tmp")
    tmp.write_text(txt, encoding="utf-8")
    ctx, facts_q = {}, {}
    from datetime import date as _dt
    for _ev, el in ET.iterparse(tmp, events=("end",)):
        t = el.tag.split("}")[-1]
        if t == "context":
            cid, st, en = el.get("id"), None, None
            for ch in el.iter():
                ct = ch.tag.split("}")[-1]
                if ct == "startDate":
                    st = ch.text
                if ct == "endDate":
                    en = ch.text
            if st or en:
                ctx[cid] = (st, en)
            el.clear()
        elif t in tags and el.get("contextRef") and el.text:
            st, en = ctx.get(el.get("contextRef"), (None, None))
            if en:
                facts_q[(t, en, (_dt.fromisoformat(en) - _dt.fromisoformat(st)).days if st else None)] = float(el.text)
            el.clear()
    out = {"latest_10q": {"accession": accn, "filed": filed, "instance": url},
           "facts": {f"{t}|{e}|{d}": v for (t, e, d), v in sorted(facts_q.items())}}
    eps = {k: v for k, v in facts_q.items() if k[0] == "EarningsPerShareDiluted"}
    q_ends = sorted({k[1] for k in eps})
    if len(q_ends) >= 2:
        cur, prev = q_ends[-1], q_ends[-2]
        q3 = eps.get(("EarningsPerShareDiluted", cur, 90))
        h1 = eps.get(("EarningsPerShareDiluted", cur, 180))
        h1_prev = eps.get(("EarningsPerShareDiluted", prev, 180))
        fy = (facts.get("us-gaap", {}).get("EarningsPerShareDiluted", {}).get("units", {}).get("USD/shares", []))
        out["eps_latest_quarter"] = q3
        out["eps_current_h1"] = h1
        out["eps_prior_h1"] = h1_prev
        if h1 and h1_prev:
            out["eps_h1_yoy_pct"] = round((h1 / h1_prev - 1) * 100, 1)
    return out


def _xbrl_series(facts: dict, tag: str, unit: str = "USD", form: str = "10-K") -> dict:
    """按财年取年度值：流量项=约一年区间（300~400 天），存量项=期末瞬时值；同财年多份申报取最新 filed。

    坑（实测踩过的）：
    不要用 frame.startswith('CY')——会命中季度帧；这里一律按区间长度 + 10-K 过滤。
    """
    from datetime import date as _d
    src = facts.get("us-gaap", {}).get(tag) or facts.get("dei", {}).get(tag)
    if not src:
        return {}
    out = {}
    for it in src.get("units", {}).get(unit, []):
        if it.get("form") != form or it.get("val") is None or not it.get("end"):
            continue
        en = it["end"]
        if it.get("start"):
            days = (_d.fromisoformat(en) - _d.fromisoformat(it["start"])).days
            if not 300 <= days <= 400:
                continue
            yr = int(en[:4]) if en[5:7] >= "06" else int(en[:4]) - 1
        else:
            yr = int(en[:4]) if en[5:7] >= "06" else int(en[:4]) - 1
        prev = out.get(yr)
        if prev is None or (it.get("filed") or "") >= prev[1]:
            out[yr] = (it["val"], it.get("filed") or "")
    return {k: v[0] for k, v in out.items()}


US_TAGS = [
    ("revenue_net", "USD", ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
                            "InterestIncomeExpenseNet", "InterestAndDividendIncomeOperating"]),
    ("np", "USD", ["NetIncomeLoss"]),
    ("np_common", "USD", ["NetIncomeLossAvailableToCommonStockholdersBasic"]),
    ("ocf", "USD", ["NetCashProvidedByUsedInOperatingActivities"]),
    ("equity", "USD", ["StockholdersEquity"]),
    ("assets", "USD", ["Assets"]),
    ("goodwill", "USD", ["Goodwill"]),
    ("eps_diluted", "USD/shares", ["EarningsPerShareDiluted"]),
    ("dividends_per_share", "USD/shares", ["CommonStockDividendsPerShareDeclared"]),
    ("shares_out", "shares", ["EntityCommonStockSharesOutstanding", "CommonStockSharesOutstanding",
                              "CommonStockSharesIssued", "WeightedAverageNumberOfDilutedSharesOutstanding"]),
]


def build_us(ticker: str, cross_check: dict | None = None) -> dict:
    """美股：一手数据来自 SEC EDGAR XBRL（10-K），行情来自 Nasdaq API。

    银行等特殊业态：毛利率/净利率不适用，脚本会写进 gaps；OCF 对银行无意义（含贷款投放），
    按事实披露、不做解读。第二独立来源（yfinance/macrotrends/stockanalysis 常被 429/403/CF 挡）
    通过 --cross-check 注入；拿不到就明确报缺口，不假装有两源。
    """
    sym = ticker.strip().upper()
    if "VALUEINVEST_SEC_UA" not in os.environ:
        print("⚠️ 未设置 VALUEINVEST_SEC_UA —— SEC 要求 User-Agent 为 '<应用名> <邮箱>'，"
              "否则可能返回 403。建议：export VALUEINVEST_SEC_UA='Your Name your@email.com'",
              file=sys.stderr)
    out = {"ticker": sym, "market": "US", "sources": {
        "financials": f"SEC EDGAR XBRL companyfacts（10-K 年度）",
        "price": "Nasdaq API api.nasdaq.com/api/quote/<sym>/historical",
    }, "missing": [], "verification": []}
    cache = Path("~/.cache/valueinvest").expanduser()

    # ---- CIK ----
    tickers = _sec_get("https://www.sec.gov/files/company_tickers.json", cache)
    cik = None
    for v in tickers.values():
        if v["ticker"].upper() == sym:
            cik = int(v["cik_str"])
            break
    if cik is None:
        sys.exit(f"SEC 未找到 {sym} 的 CIK")
    out["cik"] = cik
    resp = _sec_get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json", cache)
    out["entity_name"] = resp.get("entityName")
    facts = resp.get("facts", resp)   # XBRL 实体在 resp['facts'] 下（us-gaap / dei）

    # ---- 年度财报（按标签优先级取；记录实际使用的标签，便于复核）----
    used, series = {}, {}
    for key, unit, cands in US_TAGS:
        for tag in cands:
            s = _xbrl_series(facts, tag, unit)
            if len(s) >= 3:
                series[key] = s
                used[key] = tag
                break
    out["xbrl_tags_used"] = used
    # 每股分红：XBRL 常按季度申报（无年度条目），先按 (start,end) 去重（同一季度会在多份申报里重复出现），再按财年加总
    from datetime import date as _dt
    seen_dps, dps_q, dps_n = {}, {}, {}
    for it in facts.get("us-gaap", {}).get("CommonStockDividendsPerShareDeclared", {}).get("units", {}).get("USD/shares", []):
        if it.get("val") is None or not it.get("end") or not it.get("start"):
            continue
        if (_dt.fromisoformat(it["end"]) - _dt.fromisoformat(it["start"])).days > 130:
            continue
        k = (it["start"], it["end"])
        if k not in seen_dps or (it.get("filed") or "") >= seen_dps[k][1]:
            seen_dps[k] = (it["val"], it.get("filed") or "")
    for (st, en), (val, _f) in seen_dps.items():
        yr = int(en[:4]) if en[5:7] >= "06" else int(en[:4]) - 1
        dps_q[yr] = dps_q.get(yr, 0.0) + val
        dps_n[yr] = dps_n.get(yr, 0) + 1
    if dps_q:
        series["dividends_per_share"] = {k: round(v, 2) for k, v in dps_q.items() if v > 0}
        used["dividends_per_share"] = "CommonStockDividendsPerShareDeclared（季度去重后按财年加总）"
        latest_dps_yr = max(dps_q)
        if dps_n.get(latest_dps_yr, 0) < 4:
            out["missing"].append(f"每股分红 {latest_dps_yr} 仅含 {dps_n[latest_dps_yr]} 个季度（XBRL 未逐季申报全部季度）"
                                  f"⇒ 该年 DPS 与据此算出的股息率被**低估**，勿直接当年度分红额使用")
    years = sorted(series.get("np", series.get("revenue_net", {})), reverse=True)[:6]
    if not years:
        sys.exit("XBRL 未取到年度数据")
    out["financials_annual"] = {}
    for y in years:
        row = {k: series[k].get(y) for k in series}
        # 银行无毛利率；只在营收与营业成本都能取到时才算（本脚本不取成本，故一致为 None）
        row["_note"] = "美股银行/金融：无毛利率、净利率口径，OCF 含贷款投放不具可比性"
        out["financials_annual"][str(y)] = row

    # ---- 行情（Nasdaq）----
    import requests, pandas as pd
    end = datetime.now().strftime("%Y-%m-%d")
    h = retry(lambda: requests.get(
        f"https://api.nasdaq.com/api/quote/{sym}/historical?assetclass=stocks&fromdate=2015-01-01&todate={end}&limit=9999",
        headers={"User-Agent": "Mozilla/5.0"}, timeout=60)).json()
    rows = ((h or {}).get("data") or {}).get("tradesTable", {}).get("rows", [])
    if not rows:
        sys.exit("Nasdaq 未返回行情")
    px = pd.DataFrame([{"date": pd.to_datetime(r["date"]), "close": float(r["close"].replace("$", "").replace(",", "")),
                        "high": float(r["high"].replace("$", "").replace(",", "")),
                        "low": float(r["low"].replace("$", "").replace(",", ""))} for r in rows]).sort_values("date")
    price = float(px["close"].iloc[-1])
    last = px["date"].iloc[-1]
    out["snapshot"] = {"price": price, "price_date": str(last.date()), "price_adj": "unadjusted(实际成交价)",
                       "currency": "USD", "shares_out_sec": series.get("shares_out", {}).get(max(series.get("shares_out", {0})) or 0)}
    y1, y5 = px[px["date"] >= last - pd.Timedelta(days=365)], px[px["date"] >= last - pd.Timedelta(days=365 * 5)]
    out["price_stats"] = {
        "ret_1y_pct": round((price / float(y1["close"].iloc[0]) - 1) * 100, 1) if len(y1) else None,
        "ret_5y_pct": round((price / float(y5["close"].iloc[0]) - 1) * 100, 1) if len(y5) else None,
        "high_5y": float(y5["high"].max()), "low_5y": float(y5["low"].min()),
        "pct_below_5y_high": round((1 - price / float(y5["high"].max())) * 100, 1),
    }

    # ---- 估值：用「财年末收盘价 / 该财年 EPS」自建 PE 序列（来源可回溯：SEC EPS × Nasdaq 价）----
    eps, dps = series.get("eps_diluted", {}), series.get("dividends_per_share", {})
    pe_hist, year_end_px = {}, {}
    for yr in sorted(eps):
        seg = px[(px["date"] >= f"{yr}-12-01") & (px["date"] <= f"{yr+1}-01-31")]
        if len(seg) and eps[yr] and eps[yr] > 0:
            year_end_px[yr] = float(seg["close"].iloc[-1])
            pe_hist[yr] = round(year_end_px[yr] / eps[yr], 2)
    cur_pe = round(price / eps[max(eps)], 1) if eps and eps[max(eps)] > 0 else None
    val = {}
    if pe_hist:
        pv = sorted(pe_hist.values())
        val["pe_fy_end"] = {"current_on_latest_fy_eps": cur_pe, "pct_in_available_years": round(
            sum(1 for v in pv if v <= (cur_pe or 0)) / len(pv) * 100, 1),
            "min": min(pv), "max": max(pv), "median": round(sorted(pv)[len(pv) // 2], 2),
            "years_covered": [min(pe_hist), max(pe_hist)]}
    sh = out["snapshot"]["shares_out_sec"]
    if sh and series.get("equity"):
        bvps = max(series["equity"].values()) / sh
        val["pb_on_latest_equity"] = {"price": price, "bvps": round(bvps, 2), "pb": round(price / bvps, 2),
                                      "note": "eq 含优先股，银行 PB 略被低估"}
    if dps:
        # 取最近**有 ≥3 季度**的财年（VZ 每年 XBRL 只报 3 季，Q4 在 10-K 里还没入 companyfacts）。
        # 只有 ≥4 季的年份才标"完整"，3 季标"低估"缺口；1-2 季视为当年首笔，跳过。
        # T 教训：不能取 max(years)（命中单季 0.28 当全年）。VZ 教训：不能只取 ≥4 季（回退到 2016）。
        full_years = [y for y in dps if dps_n.get(y, 0) >= 4]
        recent_3q = [y for y in dps if dps_n.get(y, 0) >= 3]
        latest_annual_fy = max(series.get("np", series.get("revenue_net", {})))  # 最新年度财报年
        # 优先取"近期已知真值"（≥4 季且离最新财年 ≤1 年）：C 的 2025 缺 1 季是 10-K 滞后，2024 是真值。
        # 若近期没有完整年（VZ：2017 起每年只报 3 季，最近完整年是 2016），
        # 回退到最近的 ≥3 季年份并标低估——不能回退到远古完整年。
        recent_full = [y for y in full_years if y >= latest_annual_fy - 1]
        if recent_full:
            latest_dps_yr = max(recent_full)
            complete = True
        elif recent_3q:
            latest_dps_yr = max(recent_3q)
            complete = False
        else:
            latest_dps_yr = max(dps)
            complete = False
        latest_dps = dps[latest_dps_yr]
        val["dividend_yield_pct"] = round(latest_dps / price * 100, 2)
        val["dps_latest_fy"] = latest_dps
        val["dps_fy"] = latest_dps_yr
        val["dps_quarters_reported"] = dps_n.get(latest_dps_yr, 0)
        if not complete:
            n = dps_n.get(latest_dps_yr, 0)
            out["missing"].append(f"每股分红 {latest_dps_yr} 仅含 {n} 个季度（XBRL 未逐季申报全部季度）"
                                  f"⇒ 该年 DPS ${latest_dps} 与据此算出的股息率 {val['dividend_yield_pct']}% 被**低估**，"
                                  f"实际全年 DPS 更高，勿直接当年度分红额使用")
    # ---- 季度口径：companyfacts 会滞后（本例止于 FY2025/2026-02-20），最新季报走 10-Q 原文 ----
    try:
        q = _sec_quarters(cik, facts, cache)
    except Exception as e:  # noqa: BLE001
        q = {}
        out["missing"].append(f"最新季报(10-Q)季度口径取数失败: {type(e).__name__}")
    if q:
        out["quarters"] = q
        fy_eps = eps.get(max(eps)) if eps else None
        eps_q, h1c, h1p = q.get("eps_latest_quarter"), q.get("eps_current_h1"), q.get("eps_prior_h1")
        if eps_q:
            val["pe_on_latest_quarter_annualized"] = {"quarter_eps": eps_q, "annualized_eps": round(eps_q * 4, 2),
                                                      "pe": round(price / (eps_q * 4), 2),
                                                      "note": "单季年化，波动的 Markets 业务会被放大，仅作边界参考"}
        if fy_eps and h1c and h1p:
            ttm_eps = fy_eps - h1p + h1c
            val["pe_on_ttm_eps"] = {"ttm_eps": round(ttm_eps, 2), "pe": round(price / ttm_eps, 2),
                                    "formula": f"上一财年 EPS {fy_eps} − 上年同期半年 {h1p} + 本期半年 {h1c}（全部来自 SEC 10-K/10-Q）"}
        out["valuation"] = val
        out["verification"].append({"check": "季度口径来源", "note": f"SEC companyfacts 滞后于最新申报；"
                                    f"季度/TTM 数据取自 {q['latest_10q']['filed']} 申报的 10-Q 原文（{q['latest_10q']['accession']}）"})
    out["valuation"] = val

    # ---- 市值 + 两路股本互验 ----
    if sh:
        out["snapshot"]["market_cap"] = price * sh
        out["snapshot"]["market_cap_unit"] = "USD"
    nps = series.get("np_common", {}).get(max(series.get("np_common", {0})) or 0)
    shares_eps = round(nps / eps[max(eps)], 0) if (nps and eps and eps[max(eps)]) else None
    out["shares"] = {"sec_shares_outstanding": sh, "from_np_common_over_eps": shares_eps}
    if sh and shares_eps:
        err = abs(sh - shares_eps) / sh * 100
        out["verification"].append({"check": "股本两路互验（SEC outstanding vs 普通股净利/EPS）",
                                    "a": sh, "b": shares_eps, "diff_pct": round(err, 2),
                                    "verdict": "一致" if err <= 3 else ("存在差异（摊薄/时点差异可能）" if err <= 10 else "重大差异，须查原始财报")})
    if out["snapshot"].get("market_cap"):
        out["verification"].append({"check": "市值自算", "note": f"price × SEC 股本 = {out['snapshot']['market_cap']/1e9:.2f}B USD；第二独立市值来源不可得时不得声称已双源验证"})

    # ---- 第二来源注入（可选）----
    if cross_check:
        out["cross_check"] = {"sources": cross_check.get("sources", []), "values": cross_check.get("values", {})}
        for field, vals in (cross_check.get("compare") or {}).items():
            a, b = vals.get("a"), vals.get("b")
            if a and b:
                err = abs(a - b) / abs(a) * 100
                out["verification"].append({"check": f"跨源互验 {field}（{vals.get('la')} vs {vals.get('lb')}）",
                                            "a": a, "b": b, "diff_pct": round(err, 2),
                                            "verdict": "一致" if err <= 1 else ("存在差异" if err <= 5 else "重大差异，须查原始财报")})
    else:
        out["missing"].append("第二独立来源（跨源互验）：yfinance 429 / macrotrends 403 / stockanalysis Cloudflare —— 需在报告中标注为单源")

    # ---- 业态说明（通用；行业专属指标脚本不取，报告须自行联网核）----
    out["business_note"] = ("美股通用：行业专属指标（银行的 CET1/效率比率/净息差、电信的折旧摊销/资本开支强度、"
                            "工业的自由现金流口径等）在 10-K 正文而非 XBRL，本脚本不取；OCF 须结合业态解读"
                            "（银行含贷款投放、电信受大额 capex 支配），不与工商企业简单比较。")
    if not series.get("equity"):
        out["missing"].append("股东权益（StockholdersEquity）未从 XBRL 取到（公司可能用其他标签）⇒ 本包不算 PB，估值须另取账面")
    out["sources"]["second_source"] = "见 cross_check（若缺则本包为单源：SEC 一手 + Nasdaq 行情）"
    return out


def render_md(fp: dict) -> str:
    L = [f"# 事实包 {fp['ticker']}（{fp['market']}）", "",
         f"- 生成时间：{fp['generated_at']}", f"- 数据来源：见文末 sources；**本文件所有数字由脚本取数，禁止 LLM 改写**", ""]
    L += ["## 行情与估值快照", "", "| 项 | 值 |", "|---|---|"]
    for k, v in fp.get("snapshot", {}).items():
        L.append(f"| {k} | {v} |")
    for k, v in (fp.get("price_stats") or {}).items():
        L.append(f"| {k} | {v} |")
    if fp.get("valuation") and fp["market"] != "US":
        L += ["", "## 历史估值分位（越低越便宜；分位=当前值在窗口内低于它的比例）", "",
              "| 指标 | 当前 | 10年分位% | 10年中位 | 10年区间 |", "|---|---|---|---|---|"]
        for k, v in fp["valuation"].items():
            if "pct_10y" in v:
                L.append(f"| {k} | {v['current']} | {v['pct_10y']} | {v['median_10y']} | {v['min_10y']}~{v['max_10y']} |")
    if fp["market"] == "US":
        L += ["", "## 估值（自建：SEC EPS × Nasdaq 财年末收盘价；来源可回溯）", "",
              "| 指标 | 值 |", "|---|---|"]
        for k, v in (fp.get("valuation") or {}).items():
            L.append(f"| {k} | {json.dumps(v, ensure_ascii=False)} |")
        if fp.get("business_note"):
            L += ["", f"> ⚠️ 业态说明：{fp['business_note']}"]
        if fp.get("entity_name"):
            L.insert(2, f"- 标的：**{fp['entity_name']}**（CIK {fp.get('cik')}）")
    def _yi(x):
        return f"{x/1e8:,.2f}" if isinstance(x, (int, float)) else x

    if fp.get("financials_annual") and fp["market"] == "US":
        L += ["", "## 年度财报（近 6 期，来自 SEC 10-K；金额单位＝**百万美元**）", "",
              "| 财年 | 营收净额 | 净利(含少数股东) | 普通股净利 | 摊薄EPS | 股东权益 | 总资产 | 经营现金流 | 每股分红 | 股本 |", "|---|---|---|---|---|---|---|---|---|---|"]
        def _m(x):
            return f"{x/1e6:,.0f}" if isinstance(x, (int, float)) else x
        for y, r in sorted(fp["financials_annual"].items(), reverse=True):
            L.append("| {y} | {a} | {b} | {c} | {d} | {e} | {f} | {g} | {h} | {i} |".format(
                y=y, a=_m(r.get("revenue_net")), b=_m(r.get("np")), c=_m(r.get("np_common")), d=r.get("eps_diluted"),
                e=_m(r.get("equity")), f=_m(r.get("assets")), g=_m(r.get("ocf")),
                h=r.get("dividends_per_share"), i=_m(r.get("shares_out"))))
        L += ["", f"- XBRL 标签（实际使用，便于复核）：`{json.dumps(fp.get('xbrl_tags_used', {}), ensure_ascii=False)}`"]
    elif fp.get("financials_annual"):
        L += ["", "## 年度财报（近 6 期；金额单位＝**亿元**，比率单位＝% 或倍数见字段名）", "",
              "| 期 | 营收(亿) | 归母净利(亿) | 扣非净利(亿) | ROE | 毛利率% | 净利率% | 资产负债率% | 经营现金流(亿) | 自由现金流/股(元) |", "|---|---|---|---|---|---|---|---|---|---|"]
        for p, r in sorted(fp["financials_annual"].items(), reverse=True):
            L.append("| {p} | {a} | {b} | {c} | {roe} | {gross_margin} | {net_margin} | {debt_ratio} | {d} | {fcf_ps} |".format(
                p=p, a=_yi(r.get("revenue")), b=_yi(r.get("np_parent")), c=_yi(r.get("np_deducted")),
                d=_yi(r.get("ocf")), **{k: r.get(k) for k in ("roe", "gross_margin", "net_margin", "debt_ratio", "fcf_ps")}))
    if fp.get("financials_latest_interim") and fp["market"] != "US":
        it = fp["financials_latest_interim"]
        L += ["", f"## 最新一期 {it.get('period')}（年报未出时以中期为准；金额单位＝**亿元**）", "",
              "| 指标 | 值 | 指标 | 值 |", "|---|---|---|---|",
              f"| 营收(亿) | {_yi(it.get('revenue'))} | 归母净利(亿) | {_yi(it.get('np_parent'))} |",
              f"| 扣非净利(亿) | {_yi(it.get('np_deducted'))} | 经营现金流(亿) | {_yi(it.get('ocf'))} |",
              f"| 净资产(亿) | {_yi(it.get('equity'))} | 商誉(亿) | {_yi(it.get('goodwill'))} |",
              f"| 基本EPS(元) | {it.get('eps')} | 每股净资产(元) | {round(it['bvps'],2) if it.get('bvps') else None} |",
              f"| ROE% | {it.get('roe')} | 毛利率% | {it.get('gross_margin')} |",
              f"| 净利率% | {it.get('net_margin')} | 资产负债率% | {it.get('debt_ratio')} |",
              f"| 自由现金流/股(元) | {it.get('fcf_ps')} | | |"]
    if fp.get("growth"):
        L += ["", "## 成长性", "", "```json", json.dumps(fp["growth"], ensure_ascii=False), "```"]
    if fp.get("shares"):
        L += ["", "## 股本（三路推导，供交叉验证）", "", "```json", json.dumps(fp["shares"], ensure_ascii=False), "```"]
    if fp.get("verification"):
        L += ["", "## 脚本级验算", ""]
        for v in fp["verification"]:
            L.append(f"- {v.get('check')}: {json.dumps({k: x for k, x in v.items() if k != 'check'}, ensure_ascii=False)}")
    if fp.get("dividends"):
        L += ["", "## 分红记录", "", "```json", json.dumps(fp["dividends"], ensure_ascii=False, indent=1), "```"]
        if fp.get("dividend_yield_pct_ttm") is not None:
            dv = fp.get("dividend", {})
            L.append(f"\n- **股息率（TTM 口径，近 12 个月实付合计）：{fp['dividend_yield_pct_ttm']}%** "
                     f"（{dv.get('ttm_n_payments')} 次派息，合计 {dv.get('ttm_per_share')} 元/股；按最新收盘价）")
            L.append(f"- 参考：最近单次派息 {dv.get('last_single_per_share')} 元/股（除权日 {dv.get('last_ex_date')}）"
                     f"→ 单次口径股息率 {fp.get('dividend_yield_pct_last_single')}%（**勿用单次口径替代 TTM**）")
    if fp.get("business"):
        L += ["", "## 主营业务", ""] + [f"- {k}: {v}" for k, v in fp["business"].items()]
    if fp.get("missing"):
        L += ["", "## ⚠️ 缺口（脚本明确报缺，禁止脑补）", ""] + [f"- {m}" for m in fp["missing"]]
    L += ["", "## sources", ""] + [f"- {k}: {v}" for k, v in fp["sources"].items()]
    return "\n".join(L) + "\n"


REQUIRED = ["ticker", "market", "generated_at", "snapshot", "sources"]

def verify(run_dir: str) -> int:
    """不联网的产出校验：facts.json 结构 + md 关键段落齐全。"""
    rd = Path(run_dir)
    js, md = rd / "facts.json", rd / "facts.md"
    errs = []
    if not js.exists() or not md.exists():
        print(f"❌ 缺文件: {js if not js.exists() else ''} {md if not md.exists() else ''}")
        return 1
    f = json.loads(js.read_text(encoding="utf-8"))
    for k in REQUIRED:
        if k not in f:
            errs.append(f"facts.json 缺字段 {k}")
    if not f.get("snapshot", {}).get("price"):
        errs.append("facts.json 无价格")
    txt = md.read_text(encoding="utf-8")
    for sec in ("## 行情与估值快照", "## sources"):
        if sec not in txt:
            errs.append(f"facts.md 缺段落 {sec}")
    if "行情与估值快照" in txt and "None" in txt.split("## 行情与估值快照")[1].split("##")[0]:
        errs.append("快照段出现 None，取数不完整")
    print("❌ " + "; ".join(errs) if errs else f"✅ facts 包通过结构校验（{f['market']} {f['ticker']}，缺口 {len(f.get('missing', []))} 项）")
    return 1 if errs else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ticker", nargs="?")
    ap.add_argument("run_dir", nargs="?")
    ap.add_argument("--verify", metavar="RUN_DIR")
    ap.add_argument("--cross-check", metavar="JSON", help="注入第二独立来源（美股用）：{\"sources\":[...],\"values\":{...},\"compare\":{\"revenue\":{\"a\":..,\"b\":..,\"la\":..,\"lb\":..}}}")
    a = ap.parse_args()
    if a.verify:
        sys.exit(verify(a.verify))
    if not a.ticker or not a.run_dir:
        ap.error("需要 ticker 和 run_dir（或 --verify RUN_DIR）")
    m = classify(a.ticker)
    cc = json.loads(Path(a.cross_check).expanduser().read_text(encoding="utf-8")) if a.cross_check else None
    if m == "A":
        fp = build_a(a.ticker)
    elif m == "HK":
        fp = build_hk(a.ticker)
    elif m == "US":
        fp = build_us(a.ticker, cc)
    else:
        sys.exit(f"不支持的代码 {a.ticker}")
    fp["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rd = Path(a.run_dir).expanduser()
    rd.mkdir(parents=True, exist_ok=True)
    (rd / "facts.json").write_text(json.dumps(fp, ensure_ascii=False, indent=1), encoding="utf-8")
    (rd / "facts.md").write_text(render_md(fp), encoding="utf-8")
    # meta.json：数据截止日 + 阶段状态（verify_run.py 的判据之一）
    mp = rd / "meta.json"
    meta = json.loads(mp.read_text(encoding="utf-8")) if mp.exists() else {}
    meta.update({"ticker": fp["ticker"], "market": fp["market"], "date": datetime.now().strftime("%Y-%m-%d"),
                 "data_cutoff": str(fp.get("snapshot", {}).get("price_date") or fp["generated_at"][:10]),
                 "gaps": fp.get("missing", [])})
    meta.setdefault("stages", {})["facts"] = {"status": "done", "at": fp["generated_at"], "sources": fp["sources"]}
    mp.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"✅ 事实包写入 {rd}/facts.json + facts.md")
    if fp["missing"]:
        print("⚠️ 缺口: " + "; ".join(fp["missing"]))
    sys.exit(verify(str(rd)))


if __name__ == "__main__":
    main()

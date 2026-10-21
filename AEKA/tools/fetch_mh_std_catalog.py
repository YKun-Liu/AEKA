# -*- coding: utf-8 -*-
"""
fetch_mh_std_catalog.py —— 从全国标准信息公共服务平台（std.samr.gov.cn）
拉取 MH（民用航空）行业标准备案全量目录，落盘 JSON 原始数据并生成 Markdown 清单。

数据源：https://std.samr.gov.cn/hb/hbQuery（行业标准目录查询）
接口：GET https://std.samr.gov.cn/hb/search/hbPage?searchText=&op=MH（民用航空）&ISSUE_DATE=&pageNumber=N&pageSize=50
用途：官方权威题录（编号/名称/现行状态/日期/归口），仅题录不含全文。
用法：python fetch_mh_std_catalog.py
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date

BASE = "https://std.samr.gov.cn/hb/search/hbPage"
OP = "MH（民用航空）"
PAGE_SIZE = 50
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AEKA-catalog-fetch/0.1"}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, "data", "raw")
OUT_MD_DIR = os.path.join(ROOT, "knowledge", "00_题录库", "MH目录")


def fetch_page(page: int, retries: int = 4) -> dict:
    params = {
        "searchText": "",
        "op": OP,
        "ISSUE_DATE": "",
        "pageNumber": page,
        "pageSize": PAGE_SIZE,
    }
    url = BASE + "?" + urllib.parse.urlencode(params)
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            print(f"page {page} attempt {attempt + 1} failed: {exc}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    return {"total": 0, "rows": []}


def clean_code(code: str) -> str:
    """标准号清洗：'MH/T 7003—2017' 保留原样展示即可，仅规整空白。"""
    return re.sub(r"\s+", " ", (code or "")).strip()


def main() -> None:
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(OUT_MD_DIR, exist_ok=True)

    first = fetch_page(1)
    total = int(first.get("total", 0))
    print(f"total={total}")
    rows = list(first.get("rows", []))
    pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
    for p in range(2, pages + 1):
        data = fetch_page(p)
        rows.extend(data.get("rows", []))
        time.sleep(0.25)

    print(f"fetched rows={len(rows)}")
    today = date.today().isoformat()
    raw_path = os.path.join(RAW_DIR, f"mh_std_catalog_{today}.json")
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    print("raw ->", raw_path)

    # 统计
    def cnt(key, val):
        return sum(1 for r in rows if r.get(key) == val)

    n_cur = cnt("STATE", "现行")
    n_abs = cnt("STATE", "废止")
    n_other = total - n_cur - n_abs
    n_mand = sum(1 for r in rows if "强制" in (r.get("STD_NATURE") or ""))
    print(f"现行={n_cur} 废止={n_abs} 其他={n_other} 强制性={n_mand}")

    def sort_key(r):
        state = 0 if r.get("STATE") == "现行" else 1
        code = r.get("C_STD_CODE") or ""
        num = re.sub(r"\D", "", code)
        try:
            num = int(num) if num else 0
        except ValueError:
            num = 0
        return (state, num, code)

    rows_sorted = sorted(rows, key=sort_key)

    # 全量清单 md
    md = [
        f"# 民航行业标准（MH/T）官方备案目录（全量 {total} 条）",
        "",
        f"> 数据源：全国标准信息公共服务平台 行业标准目录查询（std.samr.gov.cn/hb/hbQuery，行业=MH 民用航空）",
        f"> 抓取日期：{today} ｜ 仅题录（不含全文）｜ 备案口径：现行 {n_cur} / 废止 {n_abs} / 其他 {n_other}，其中强制性 {n_mand} 条",
        "> 用途：版本台账核实底稿。引用任何标准前请以正式发布文本为准。",
        "",
        "| # | 标准号 | 名称 | 状态 | 性质 | 制修 | 发布日期 | 实施日期 | 归口/备案 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(rows_sorted, 1):
        issue = (r.get("ISSUE_DATE") or "").replace(" 00:00:00", "")
        act = (r.get("ACT_DATE") or "").replace(" 00:00:00", "")
        notice = r.get("NOTICE_NO") or ""
        md.append(
            f"| {i} | {clean_code(r.get('C_STD_CODE') or '')} | {(r.get('C_NAME') or '').strip()} "
            f"| {r.get('STATE') or ''} | {r.get('STD_NATURE') or ''} | {r.get('STD_ZXD') or ''} "
            f"| {issue} | {act} | {notice} |"
        )
    md_path = os.path.join(OUT_MD_DIR, f"民航行业标准MH_T_官方备案目录_全量{total}条_{today}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print("md   ->", md_path)

    # 弱电相关关键词初筛（候选，宽口径，宁滥勿缺，供人工确认）
    kws = [
        "监控", "安防", "摄像", "视频", "图像", "信息", "数据", "网络", "通信",
        "显示", "广播", "时钟", "集成", "弱电", "安检", "围界", "门禁", "报警",
        "机房", "离港", "航显", "存储", "布线", "大屏", "屏", "软件", "射频",
        "电磁", "防雷", "接地", "传感器", "探测", "终端", "服务器", "接口",
        "传输", "交换", "定位", "导航", "记录仪", "监视", "电子",
    ]
    hits = []
    for r in rows_sorted:
        text = (r.get("C_NAME") or "") + " " + (r.get("C_STD_CODE") or "") + " " + (r.get("CCS") or "")
        if any(k in text for k in kws):
            hits.append(r)
    print(f"弱电关键词初筛候选={len(hits)}")
    md2 = [
        f"# 民航行业标准（MH/T）弱电相关候选清单（关键词初筛 {len(hits)}/{total}）",
        "",
        "> ⚠️ 本表由名称关键词初筛生成，**仅供缩小范围**，每条均需人工核对与民航弱电工程的关联度后**才可**转入正式题录库。",
        f"> 数据源：全国标准信息公共服务平台（std.samr.gov.cn）MH 行业标准备案目录，抓取日期 {today}。",
        "",
        "| # | 标准号 | 名称 | 状态 | 性质 | 发布日期 | 实施日期 |",
        "|---|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(hits, 1):
        issue = (r.get("ISSUE_DATE") or "").replace(" 00:00:00", "")
        act = (r.get("ACT_DATE") or "").replace(" 00:00:00", "")
        md2.append(
            f"| {i} | {clean_code(r.get('C_STD_CODE') or '')} | {(r.get('C_NAME') or '').strip()} "
            f"| {r.get('STATE') or ''} | {r.get('STD_NATURE') or ''} | {issue} | {act} |"
        )
    md2_path = os.path.join(OUT_MD_DIR, f"民航行业标准_弱电相关候选初筛_{today}.md")
    with open(md2_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md2))
    print("md2  ->", md2_path)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
verify_std_mohurd.py —— 用住建部门户检索接口核实工程建设类国家标准题录。

数据源：www.mohurd.gov.cn 站内检索 API（jpaas-jsearch-web-server）
  interface/search/info_new?q=<关键词>&cateid=...&serviceId=...
用途：核实标准号/名称/发布实施日期/代替或废止关系（官方公告原文）。
输出：data/verify_report_mohurd.txt（供人工复核）+ 控制台摘要

用法：python tools/verify_std_mohurd.py [标准号 ...]
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

API = ("https://www.mohurd.gov.cn/api-gateway/jpaas-jsearch-web-server/interface/search/info_new"
       "?websiteid=&q={q}&pg=10&cateid=6ca0f12c0f0642ab8b1dc17028e12ea1"
       "&serviceId=e2f3058e2a3b4f8abc93eb76e739e3e7&p=1"
       "&pos=title,content,filenumber,documentNumber&sortType=2")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36"}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "verify_report_mohurd.txt")

TARGETS = sys.argv[1:] or [
    "GB 50198-2011", "GB 50394-2007", "GB 50396-2007",
    "GB 50311-2016", "GB/T 50312-2016", "GB 50314-2015", "GB 50339-2013",
]


def query(q):
    url = API.format(q=urllib.parse.quote(q))
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def extract(js, std_no):
    """从检索结果中挑出与 std_no 相关的条目摘要"""
    out = []
    try:
        results = js["data"]["searchResult"]["result"]
    except Exception:
        return out
    key = std_no.replace(" ", "").replace("/", "").replace(".", "")
    for item in results:
        d = item.get("data", {})
        title = (d.get("title") or "").strip()
        filenumber = (d.get("filenumber") or "").strip()
        content = d.get("content") or ""
        createdate = d.get("createdate") or ""
        # 规范化后比对标准号
        norm_content = content.replace(" ", "")
        if key and (key in norm_content or key in title.replace(" ", "")):
            # 抽取含“编号为/自…起实施/废止”的关键句
            sents = []
            for pat in (r"[^。；]*编号[^。；]*", r"[^。；]*自\s*20\d\d\s*年[^。；]*实施[^。；]*",
                        r"[^。；]*同时废止[^。；]*", r"[^。；]*原[^。；]*废止[^。；]*"):
                for m in re.finditer(pat, content):
                    s = re.sub(r"\s+", "", m.group(0))
                    if s and s not in sents:
                        sents.append(s)
            out.append({
                "title": title, "filenumber": filenumber, "createdate": createdate,
                "sents": sents[:6],
            })
    return out


def main():
    buf = []
    for std in TARGETS:
        try:
            js = query(std)
        except Exception as e:  # noqa
            buf.append(f"### {std}\n  [查询失败] {e}\n")
            print(f"### {std} -> ERROR {e}")
            continue
        hits = extract(js, std)
        if not hits:
            buf.append(f"### {std}\n  未在该渠道检索到相关公告（可能非工程建设类，或需换关键词）\n")
            print(f"### {std} -> 无相关公告")
        else:
            buf.append(f"### {std}")
            for h in hits[:3]:
                buf.append(f"  标题: {h['title']}")
                buf.append(f"  文号: {h['filenumber']}  日期戳: {h['createdate']}")
                for s in h["sents"]:
                    buf.append(f"    · {s}")
            buf.append("")
            print(f"### {std} -> {len(hits)} 条相关；首条: {hits[0]['title'][:40]}")
        time.sleep(0.4)
    open(OUT, "w", encoding="utf-8").write("\n".join(buf))
    print("\n报告 ->", OUT)


if __name__ == "__main__":
    main()

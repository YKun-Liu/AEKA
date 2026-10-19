# -*- coding: utf-8 -*-
r"""extract_specs.py —— 从天府机场技术规范书提取结构化工程信息（纯本地、零 token）

输出（data/_survey/extracted/）：
  systems.json       每个系统的：名称/标段/字数/章节树/关键指标候选
  metrics.md         全项目关键技术指标汇总（存储天数、码率、可用性、带宽容灾等）
  interfaces.md      系统接口与边界线索（"接口""联动""接入""集成"上下文）
"""
import json
import re
import sys
from pathlib import Path

import docx

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = Path(r"E:\天府机场")
CONV = SRC / "_converted"
OUT = Path(r"E:\openclaw\workspace\AEKA\data\_survey\extracted")
OUT.mkdir(parents=True, exist_ok=True)

# 重要指标关键词（正则，捕获"关键词 + 数值 + 单位"）
METRIC_PATTERNS = [
    ("存储天数", r"(?:保存|存储|录像)[^。；\n]{0,30}?(\d{1,3})\s*(?:天|d)"),
    ("保存期限", r"(?:保存期限|留存)[^。；\n]{0,20}?(\d{1,3})\s*(?:天|d|个月|年)"),
    ("码率", r"(\d+(?:\.\d+)?)\s*(?:Mbps|Mb/s|kbps)", ),
    ("可用性", r"(\d{2,3}(?:\.\d+)?)\s*%\s*(?:的)?(?:可用性|系统可用|在线率)"),
    ("响应时间", r"(\d+(?:\.\d+)?)\s*(?:ms|毫秒|s|秒)\s*(?:内)?(?:响应|完成)"),
    ("带宽", r"(\d+(?:\.\d+)?)\s*(?:Gbps|Mbps|GE|10GE)", ),
    ("并发", r"(\d+)\s*(?:路|个)?\s*(?:并发|同时)", ),
    ("分辨率", r"(1080[pi]|4K|3840\s*[×x]\s*2160|2560\s*[×x]\s*1440|1920\s*[×x]\s*1080)"),
    ("帧率", r"(\d{1,2})\s*(?:fps|帧/秒)"),
    ("无故障时间MTBF", r"MTBF[^0-9]{0,10}(\d+(?:,\d{3})*)\s*(?:小时|h)"),
    ("存储容量", r"(\d+(?:\.\d+)?)\s*(?:TB|PB)"),
]

IFACE_KEYS = ("接口", "联动", "接入", "集成", "对接", "互通", "数据交换", "协议")

FILES = sorted(SRC.glob("*.docx")) + sorted(CONV.glob("*.docx"))


def chapter_tree(doc):
    """按 Heading 层级还原章节树（只到 3 级）"""
    tree, stack = [], {}
    for p in doc.paragraphs:
        if not (p.style and p.style.name.startswith("Heading") and p.text.strip()):
            continue
        m = re.search(r"(\d)", p.style.name)
        lvl = int(m.group(1)) if m else 1
        if lvl > 3:
            continue
        t = p.text.strip()[:60]
        if lvl == 1:
            tree.append({"h": t, "sub": []})
            stack[1] = tree[-1]
        elif lvl == 2 and tree:
            tree[-1]["sub"].append({"h": t, "sub": []})
            stack[2] = tree[-1]["sub"][-1]
        elif lvl == 3 and stack.get(2):
            stack[2]["sub"].append({"h": t})
    return tree


systems, metrics_rows, iface_rows = [], [], []

for i, p in enumerate(FILES, 1):
    try:
        doc = docx.Document(str(p))
    except Exception:
        continue
    text = "\n".join(x.text for x in doc.paragraphs)
    # 表格文本也纳入（指标常在表格）
    for tb in doc.tables:
        for row in tb.rows:
            text += "\n" + " | ".join(c.text.strip() for c in row.cells)

    name = p.stem
    seg = "二标段" if "二标段" in name else ("三标段" if "三标段" in name or "三标" in name
                                          else ("四标段" if "四标段" in name else
                                                ("一标段" if "一标段" in name else "V5.9系列")))

    sysinfo = {
        "文件": name, "标段": seg, "字符数": len(text),
        "表格数": len(doc.tables),
        "章节": chapter_tree(doc)[:8],
        "指标命中": {},
        "接口提及": 0,
    }

    for label, pat in METRIC_PATTERNS:
        hits = re.findall(pat, text)
        if hits:
            sysinfo["指标命中"][label] = list(dict.fromkeys(hits))[:5]

    # 接口：抽取含关键词的句子（去重、限长）
    sents = re.split(r"[。；\n]", text)
    picked = []
    for s in sents:
        s = s.strip()
        if 8 < len(s) < 120 and any(k in s for k in IFACE_KEYS):
            picked.append(s)
    uniq = list(dict.fromkeys(picked))[:12]
    sysinfo["接口提及"] = len(picked)
    for s in uniq:
        iface_rows.append(f"| {name[:28]} | {s[:100]} |")

    if sysinfo["指标命中"]:
        for label, vals in sysinfo["指标命中"].items():
            metrics_rows.append(f"| {name[:30]} | {label} | {', '.join(map(str, vals))} |")

    systems.append(sysinfo)
    print(f"[{i}/{len(FILES)}] {len(text):>7d} {name[:44]}")

(OUT / "systems.json").write_text(
    json.dumps(systems, ensure_ascii=False, indent=1), encoding="utf-8")

md = ["# 天府机场技术规范书 —— 关键指标提取", "",
      "> 纯本地规则抽取，未经模型加工。数值仅供认知参考，**引用须回查原文**。", "",
      "| 文件 | 指标类型 | 抽取值 |", "|---|---|---|"]
md += metrics_rows
(OUT / "metrics.md").write_text("\n".join(md), encoding="utf-8")

mi = ["# 系统接口与边界线索（原文摘句）", "",
      "| 文件 | 原句 |", "|---|---|"]
mi += iface_rows
(OUT / "interfaces.md").write_text("\n".join(mi), encoding="utf-8")

print(f"\n完成 {len(systems)} 个系统；指标 {len(metrics_rows)} 行；接口 {len(iface_rows)} 行")

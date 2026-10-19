# -*- coding: utf-8 -*-
r"""extract_general.py —— 从 4 份总则提取"认知型"内容（术语/系统/机制/组织）

只抽取高信息密度片段，供模型提炼（避免整本入上下文）：
  - 术语定义行（含"是指"、"："、缩略语）
  - 系统清单/系统构成
  - 接口与集成机制（IDD、集成测试、总协调人）
  - 组织与运行架构（AOCC、指挥中心等）
输出：data/_survey/general/术语与机制_YYYY.md（按文件分节）
"""
import re
import sys
from pathlib import Path

import docx

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = Path(r"E:\天府机场")
CONV = SRC / "_converted"
OUT = Path(r"E:\openclaw\workspace\AEKA\data\_survey\general")
OUT.mkdir(parents=True, exist_ok=True)

# 总则文件（含"总则"或"技术文件PART1"）
cands = [p for p in list(SRC.glob("*.docx")) + list(CONV.glob("*.docx"))
         if "总则" in p.name or "PART1" in p.name]

KEY = ("是指", "定义为", "指的是", "缩略语", "IDD", "接口", "集成",
       "总协调人", "AOCC", "指挥", "管理架构", "系统构成", "由以下",
       "包括但不限于", "术语")


def extract(p):
    d = docx.Document(str(p))
    lines = []
    for x in d.paragraphs:
        t = x.text.strip()
        if 6 < len(t) < 260 and any(k in t for k in KEY):
            lines.append(t)
    # 表格（缩略语表/系统表常在表格）
    for tb in d.tables:
        for r in tb.rows:
            cells = [c.text.strip() for c in r.cells]
            if len(cells) >= 2 and all(cells) and len(" ".join(cells)) < 200:
                lines.append(" | ".join(dict.fromkeys(cells)))
    # 去重保序
    return list(dict.fromkeys(lines))


all_out = []
for p in sorted(cands):
    try:
        lines = extract(p)
    except Exception as e:
        print("FAIL", p.name[:40], e)
        continue
    tag = "四标段" if "四标段" in p.name else ("三标段" if "三标" in p.name
                                           else ("二标段" if "二标段" in p.name else "一标段"))
    all_out.append(f"\n## 【{tag}】{p.name}\n")
    all_out.extend(lines)
    print(f"{tag:6s} {len(lines):4d} 片段 | {p.name[:44]}")

text = "# 天府机场总则 —— 术语/机制/架构抽取\n" + "\n".join(all_out)
out = OUT / "术语与机制.md"
out.write_text(text, encoding="utf-8")
print(f"\n总字符 {len(text):,} -> {out}")

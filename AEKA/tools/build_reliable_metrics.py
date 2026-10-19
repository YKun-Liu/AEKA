# -*- coding: utf-8 -*-
r"""build_reliable_metrics.py —— 生成"高可靠性指标对照表"（含语义过滤）

过滤规则：
  1) 无效值：空、'0'、'1'（截断）
  2) 存储天数合理区间：5~365
  3) 语义过滤：非录像类系统（UPS/配电/桥架/机房环境/综合管路等）的"存储天数"剔除
     —— 实测 UPS 文档中的"28天"指蓄电池容量保存率测试周期，与录像无关
  4) MTBF 量级过滤：< 10000 小时的视为误抓（工程设备 MTBF 通常数万小时）
输出：data/_survey/可靠指标对照表.md
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"E:\openclaw\workspace\AEKA")
SRC = ROOT / "data/_survey/extracted/systems.json"
OUT = ROOT / "data/_survey/可靠指标对照表.md"

RELI = ("存储天数", "保存期限", "分辨率", "无故障时间MTBF", "帧率")

# 非录像类系统关键词（其"存储天数"无意义）
NON_VIDEO = ("UPS", "配电", "桥架", "综合管路", "机房", "空调", "防雷", "接地",
             "布线", "机柜", "控制台", "施工", "项目管理")


def is_video_system(name):
    return not any(k in name for k in NON_VIDEO)


systems = json.load(open(SRC, encoding="utf-8"))
rows = []

for s in systems:
    name = s["文件"]
    hit = s.get("指标命中", {})
    for k in RELI:
        if k not in hit:
            continue
        vals = [str(v).strip() for v in hit[k]]
        vals = [v for v in vals if v and v not in ("0", "1")]

        if k in ("存储天数", "保存期限"):
            if not is_video_system(name):
                continue                       # 规则 3
            vals = [v for v in vals if v.isdigit() and 5 <= int(v) <= 365]

        if k == "无故障时间MTBF":
            clean = []
            for v in vals:
                n = int(v.replace(",", ""))
                if n >= 10000:                 # 规则 4
                    clean.append(f"{n:,}")
            vals = clean

        if not vals:
            continue
        rows.append((s["标段"], name[:44], k, "、".join(vals[:4])))

md = [
    "# 天府机场 —— 高可靠性指标对照表（语义过滤后）", "",
    "> 来源：`E:\\天府机场` 技术规范书，纯本地规则抽取 + 语义过滤。",
    "> **可信度 C 级（项目资料）**：反映该项目口径，不是规范要求，也不是行业通则。",
    "> 引用前须回原文核对。", "",
    "## 过滤说明", "",
    "剔除的内容及原因：",
    "- 存储天数：非录像类系统（UPS/配电/桥架/机房/布线等）——实测 UPS 文档中的 28 天",
    "  指蓄电池容量保存率测试周期，与录像存储无关",
    "- 无效值：空值、`0`、`1`（文本截断）",
    "- MTBF：小于 10,000 小时视为误抓",
    "- 未收录项：带宽、存储容量（数值与单位组合稀疏，误抓率高，须人工核对）", "",
    "## 存储期限（按系统）", "",
    "| 标段 | 系统 | 指标 | 取值（天） |", "|---|---|---|---|",
]
md += [f"| {a} | {b} | {c} | {d} |" for a, b, c, d in rows if c in ("存储天数", "保存期限")]

md += ["", "## 分辨率 / 帧率", "",
       "| 标段 | 系统 | 指标 | 取值 |", "|---|---|---|---|"]
md += [f"| {a} | {b} | {c} | {d} |" for a, b, c, d in rows
       if c in ("分辨率", "帧率")]

md += ["", "## 设备可靠性（MTBF）", "",
       "| 标段 | 系统 | MTBF（小时） |", "|---|---|---|"]
md += [f"| {a} | {b} | {d} |" for a, b, c, d in rows if c == "无故障时间MTBF"]

OUT.write_text("\n".join(md), encoding="utf-8")

n_store = sum(1 for r in rows if r[2] in ("存储天数", "保存期限"))
print(f"对照表已生成：{len(rows)} 行（存储期限 {n_store} 条）")
print("输出：", OUT)

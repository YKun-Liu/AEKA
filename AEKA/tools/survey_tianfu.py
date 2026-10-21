# -*- coding: utf-8 -*-
r"""survey_tianfu.py —— 天府机场信息弱电技术规范书：体量测绘 + 规范名称抽取

纯本地运行（不调用任何大模型），输出：
  1) data/_survey/体量清单.csv       每文件：字数/段落/表格/标题数/规范数
  2) data/_survey/规范清单.md        全书引用的全部标准（去重、按标准号排序）
  3) data/_survey/测绘报告.md        总览与缺口提示
  4) data/_survey/未解析.txt         .doc 老格式等无法解析的文件

抽取规则依据实测形态：
  "计算机信息系统安全保护等级划分准则 GB17859"
  "电子信息系统机房施工及验收规范GB50462"
  "《建筑抗震设计规范》（GB50011-2010）"
只记录"标准号 + 名称"，不读入模型上下文。
"""
import csv
import re
import sys
from pathlib import Path

import docx

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = Path(r"E:\天府机场")
CONVERTED = SRC / "_converted"
OUT = Path(r"E:\openclaw\workspace\AEKA\data\_survey")
OUT.mkdir(parents=True, exist_ok=True)

STDNO = (r"(?:GB\s*/\s*T|GB|MH\s*/\s*T|MH|JGJ\s*/\s*T|JGJ|CJJ|YD\s*/\s*T|"
         r"GA\s*/\s*T|GA|SJ\s*/\s*T|TIA\s*/\s*EIA)")
NUM = r"\d{2,5}(?:\s*[\.\-—]\s*\d{1,4})?"

# 名称 + 编号（名称后可有空白）
PAT_NAME_FIRST = re.compile(
    rf"([\u4e00-\u9fa5A-Za-z][\u4e00-\u9fa5A-Za-z（）()·、]{{3,50}})\s*"
    rf"({STDNO})\s*({NUM})")
# 《名称》（编号）
PAT_BRACKET = re.compile(
    rf"《([^》]{{3,50}})》\s*[（(]?\s*({STDNO})\s*({NUM})\s*[)）]?")

# 误匹配黑名单：名称里含这些词说明抓到的是正文而非规范名
BAD_NAME = ("按国家", "国家标准", "满足", "符合", "按照", "执行", "规定",
            "要求", "详见", "参见", "见第", "使用", "采用", "依据")

# 规范名特征词（提高可信度）
GOOD_NAME = ("规范", "标准", "准则", "规程", "规定", "技术要求", "指南")


def norm_std(a, b):
    return re.sub(r"\s+", "", a) + re.sub(r"\s+", "", b)


def extract(text):
    """返回 {标准号: [名称候选]}"""
    res = {}
    for m in PAT_NAME_FIRST.finditer(text):
        name = m.group(1).strip()
        if any(b in name for b in BAD_NAME) or len(name) < 4:
            continue
        res.setdefault(norm_std(m.group(2), m.group(3)), set()).add(name)
    for m in PAT_BRACKET.finditer(text):
        name = m.group(1).strip()
        if len(name) < 4:
            continue
        res.setdefault(norm_std(m.group(2), m.group(3)), set()).add(name)
    return res


def read_docx(p):
    d = docx.Document(str(p))
    paras = [x.text for x in d.paragraphs]
    headings = sum(1 for x in d.paragraphs
                   if x.style and x.style.name.startswith("Heading")
                   and x.text.strip())
    return "\n".join(paras), len(d.paragraphs), len(d.tables), headings


rows, all_stds, failed = [], {}, []

files = sorted(SRC.glob("*.docx")) + sorted(CONVERTED.glob("*.docx"))
print(f"待解析 .docx: {len(files)}")
for i, p in enumerate(files, 1):
    try:
        text, npara, ntab, nhead = read_docx(p)
    except Exception as e:
        failed.append("%s\t解析失败: %s" % (p.name, e))
        print(f"  [{i}/{len(files)}] FAIL {p.name[:40]}")
        continue
    stds = extract(text)
    for k, v in stds.items():
        all_stds.setdefault(k, set()).update(v)
    rows.append({
        "文件": p.name, "字符数": len(text), "段落": npara,
        "表格": ntab, "标题": nhead, "标准数": len(stds),
    })
    print(f"  [{i}/{len(files)}] {len(text):>8d} 字符  {len(stds):>2d} 标准  {p.name[:44]}")

# .doc 老格式：仅记录，暂不解析（缺 Word/LibreOffice）
docs = sorted(SRC.glob("*.doc"))
if docs:
    failed.append("以下 .doc 原文件已转换为 _converted/*.docx 并纳入统计（保留原文件不动）")
    for p in docs:
        failed.append(f"{p.name}\t.doc（已转换，见 _converted）")

# 1) 体量清单
with open(OUT / "体量清单.csv", "w", newline="", encoding="utf-8-sig") as fp:
    w = csv.DictWriter(fp, fieldnames=["文件", "字符数", "段落", "表格", "标题", "标准数"])
    w.writeheader()
    w.writerows(rows)

# 2) 规范清单
lines = ["# 天府机场信息弱电技术规范书 —— 引用标准清单", "",
         f"来源目录：`{SRC}`", f"解析文件：{len(rows)} 个 .docx", "",
         "> 说明：下表由规则从原文抽取，**部分标准名称可能带错位或旧版号**，",
         "> 补库前须逐条核实（可用 `tools/verify_std_mohurd.py` 或题录库比对）。", "",
         "| 标准号 | 名称（原文抽取） | 出现文件数 |", "|---|---|---|"]

filecount = {}
for p in files:
    try:
        t, _, _, _ = read_docx(p)
    except Exception:
        continue
    for k in extract(t):
        filecount[k] = filecount.get(k, 0) + 1

for std in sorted(all_stds):
    names = "；".join(sorted(all_stds[std])[:2])
    lines.append(f"| {std} | {names} | {filecount.get(std, 1)} |")

lines += ["", "## 待核实：名称可疑（不含规范特征词）", ""]
for std in sorted(all_stds):
    names = list(all_stds[std])
    if not any(g in n for n in names for g in GOOD_NAME):
        lines.append(f"- `{std}` {names[0]}")

(OUT / "规范清单.md").write_text("\n".join(lines), encoding="utf-8")

# 3) 未解析
(OUT / "未解析.txt").write_text("\n".join(failed), encoding="utf-8")

# 4) 总览
total_chars = sum(r["字符数"] for r in rows)
md = ["# 天府机场信息弱电技术规范书 —— 测绘报告", "",
      "> 纯本地解析，未调用大模型，零 token 消耗。", "",
      "## 体量", "",
      f"- 解析成功：**{len(rows)}** 个 .docx",
      f"- 未能解析：**{len(failed)}** 个（见 `未解析.txt`）",
      f"- 总字符数：**{total_chars:,}**（约 {total_chars/1000:.0f} 千字）",
      f"- 估算整本入模型 token：约 **{total_chars/1.5/10000:.1f} 万**（中文约 1.5 字符/token）",
      "",
      f"- 抽取到不同标准号：**{len(all_stds)}** 个",
      "",
      "## 按体量排序（前 15）", "",
      "| 文件 | 字符数 | 表格 | 标准数 |", "|---|---|---|---|"]
for r in sorted(rows, key=lambda x: -x["字符数"])[:15]:
    md.append(f"| {r['文件'][:44]} | {r['字符数']:,} | {r['表格']} | {r['标准数']} |")
(OUT / "测绘报告.md").write_text("\n".join(md), encoding="utf-8")

print(f"\n完成：{len(rows)} 个文件，{total_chars:,} 字符，{len(all_stds)} 个标准")
print("输出目录：", OUT)

# -*- coding: utf-8 -*-
r"""normalize_clause_spacing.py —— 规范化条款号点后空格（GB 50348 等 OCR 文本）

现象：GB 50348-2018 的 OCR 文本里条款号呈 "6. 12.4"、"6. 1.3"（点后有空格），
      导致按 "6.12.4" 检索失败。
策略：把「数字. + 空格 + 数字」规范为「数字.数字」，仅处理数字紧邻的模式，
      避免影响 "2 5 m"、"1 5 倍" 等测量值（它们不含点）。
范围：knowledge/01_国家标准、02_民航标准 下 .txt（含清洗版），先备份。
"""
import re
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

AEKA = Path(r"E:\openclaw\workspace\AEKA")
DIRS = [AEKA / "knowledge" / "01_国家标准", AEKA / "knowledge" / "02_民航标准"]

# 数字 + 点 + 若干空格 + 数字  →  数字.数字
PAT = re.compile(r"(?<=\d)\.\s+(?=\d)")

total = 0
for d in DIRS:
    if not d.exists():
        continue
    for f in sorted(d.glob("*.txt")):
        t = f.read_text(encoding="utf-8")
        new, n = PAT.subn(".", t)
        if n:
            bak = f.with_name(f.name + ".spcbak")
            if not bak.exists():
                shutil.copy2(f, bak)
            f.write_text(new, encoding="utf-8")
            total += n
            print(f"{f.name[:56]:58s} 修正 {n} 处")
print(f"\n合计修正 {total} 处")

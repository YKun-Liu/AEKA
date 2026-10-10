# -*- coding: utf-8 -*-
r"""restore_clause_dots v3 —— 用 chr() 构造码点，避开 \U 转义位数陷阱。

确证：MH/T 5017-2017 条款号「.」被 PyMuPDF 提取为 U+1001B0（364 处夹在数字间）。
本脚本将其在「数字之间」还原为英文句点，其余位置还原为全角点。
只替换该单一码点，不动其它任何字符；先备份。
"""
import re
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PUA = chr(0x1001B0)          # 唯一实际出现的 PUA 字符
AEKA = Path(r"E:\openclaw\workspace\AEKA")

GLOB_DIRS = [AEKA / "knowledge" / "02_民航标准", AEKA / "data" / "processed"]
NUM_DOT = re.compile("(?<=\\d)" + re.escape(PUA) + "(?=\\d)")

targets = []
for d in GLOB_DIRS:
    if d.exists():
        targets += sorted(d.glob("MH_T 5017-2017*.txt"))

grand = 0
for f in targets:
    t = f.read_text(encoding="utf-8")
    n = t.count(PUA)
    if n == 0:
        print(f"{f.name[:48]:50s} 无 PUA，跳过")
        continue
    new, n_clause = NUM_DOT.subn(".", t)
    n_other = new.count(PUA)
    new = new.replace(PUA, "．")
    bak = f.with_name(f.name + ".v3bak")
    if not bak.exists():
        shutil.copy2(f, bak)
    f.write_text(new, encoding="utf-8")
    grand += n_clause
    print(f"{f.name[:48]:50s} PUA={n:4d}  →条款点={n_clause:3d}  其它={n_other}")

print(f"\n合计还原条款号点：{grand}")

c = AEKA / "knowledge/02_民航标准/MH_T 5017-2017_民用运输机场航站楼安防监控系统工程设计规范_清洗版.txt"
if c.exists():
    print("\n样例：")
    for line in c.read_text(encoding="utf-8").splitlines():
        if ("拾音装置" in line or "安检通道" in line or "最低照度" in line) and line[:1].isdigit():
            print("  ", line[:66])

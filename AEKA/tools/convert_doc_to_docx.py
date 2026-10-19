# -*- coding: utf-8 -*-
r"""convert_doc_to_docx.py —— 用 WPS COM 把 .doc 批量转为 .docx

输入：E:\天府机场\*.doc
输出：E:\天府机场\_converted\*.docx（不覆盖原文件）
"""
import sys
from pathlib import Path

import win32com.client as win32

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = Path(r"E:\天府机场")
DST = SRC / "_converted"
DST.mkdir(exist_ok=True)

WPS = r"E:\Program Files\WPS Office\12.1.0.29161\office6\wps.exe"

docs = sorted(SRC.glob("*.doc"))
print(f"待转换 {len(docs)} 个 .doc")

app = None
ok = fail = 0
try:
    app = win32.Dispatch("KWps.Application")
    app.Visible = False
    app.DisplayAlerts = 0
    print("WPS COM 已连接")
except Exception as e:
    print("WPS COM 连接失败:", e)
    sys.exit(1)

for i, p in enumerate(docs, 1):
    out = DST / (p.stem + ".docx")
    if out.exists():
        print(f"  [{i}/{len(docs)}] 跳过(已存在) {p.name[:40]}")
        ok += 1
        continue
    try:
        doc = app.Documents.Open(str(p), ReadOnly=True)
        # 16 = wdFormatDocumentDefault (.docx)
        doc.SaveAs2(str(out), FileFormat=16)
        doc.Close(False)
        ok += 1
        print(f"  [{i}/{len(docs)}] OK  {p.name[:44]}")
    except Exception as e:
        fail += 1
        print(f"  [{i}/{len(docs)}] FAIL {p.name[:40]} -> {type(e).__name__}")

try:
    app.Quit()
except Exception:
    pass

print(f"\n完成：成功 {ok}，失败 {fail}\n输出：{DST}")

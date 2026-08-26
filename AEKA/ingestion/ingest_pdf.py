# -*- coding: utf-8 -*-
"""ingestion/ingest_pdf.py — 标准 PDF 入库管线（第一阶段：复制原始 + 提取文本 + 生成 metadata）
只读原则：不修改原始 PDF，输出到 data/processed 与 knowledge 目录。
"""
import json
import shutil
import sys
from pathlib import Path

import pymupdf  # PyMuPDF

AEKA = Path(r"E:\openclaw\workspace\AEKA")
RAW = AEKA / "data" / "raw"
PROC = AEKA / "data" / "processed"
KB = AEKA / "knowledge" / "02_民航标准"

SRC = Path(
    r"C:/Users/Administrator/.openclaw/media/inbound/"
    "4._民用运输机场安全保卫设施_MHT_7003-2017_正式发布版---dea9ab63-5d36-48a6-9636-1e5d0500bb0b.pdf"
)

STD_NO = "MH/T 7003-2017"
STD_NAME = "民用运输机场安全保卫设施"
# 文件名中不能含路径分隔符
FILE_BASE = f"{STD_NO.replace('/', '_')}_{STD_NAME}"


def main() -> int:
    if not SRC.exists():
        print(f"[FAIL] 源文件不存在: {SRC}")
        return 1

    # 1) 原始 PDF -> data/raw（保留原始资料）
    RAW.mkdir(parents=True, exist_ok=True)
    raw_pdf = RAW / SRC.name
    shutil.copy2(SRC, raw_pdf)
    print(f"[OK] 原始 PDF -> {raw_pdf} ({raw_pdf.stat().st_size} B)")

    # 2) 提取文本
    doc = pymupdf.open(raw_pdf)
    pages = []
    for i, page in enumerate(doc, 1):
        txt = page.get_text("text")
        pages.append(f"===== 第 {i} 页 / 共 {len(doc)} 页 =====\n{txt}")
    doc.close()

    full_text = "\n".join(pages)
    PROC.mkdir(parents=True, exist_ok=True)
    txt_out = PROC / f"{FILE_BASE}.txt"
    txt_out.write_text(full_text, encoding="utf-8")
    print(f"[OK] 文本提取 -> {txt_out} ({txt_out.stat().st_size} B, {len(pages)} 页)")

    # 3) metadata
    meta = {
        "std_no": STD_NO,
        "std_name": STD_NAME,
        "std_name_en": "Security facilities of civil transportation airport",
        "standard_type": "民航行业标准",
        "ics": "13.310",
        "ccs": "A 91",
        "publisher": "中国民用航空局",
        "issue_date": "2017-07-06",
        "implement_date": "2017-10-01",
        "replaces": "MH/T 7003-2008",
        "supersedes_history": ["MH 7003-95", "MH/T 7003-2008"],
        "proposer": "中国民用航空局公安局",
        "admin_dept": "中国民航科学技术研究院",
        "drafting_unit": "中国民航科学技术研究院",
        "status": "现行有效（正式发布版）",
        "kb_category": "02_民航标准",
        "source": "用户 Liu 提供（人工确认入库）",
        "ingest_date": "2026-08-26",
        "raw_file": str(raw_pdf.relative_to(AEKA)),
        "processed_file": str(txt_out.relative_to(AEKA)),
    }
    # 页数单独补
    meta["pages"] = len(pages)

    KB.mkdir(parents=True, exist_ok=True)
    kb_txt = KB / f"{FILE_BASE}.txt"
    shutil.copy2(txt_out, kb_txt)
    meta_out = KB / f"{FILE_BASE}_metadata.json"
    meta_out.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] 知识库文本 -> {kb_txt}")
    print(f"[OK] metadata -> {meta_out}")
    print("[DONE] 入库完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())

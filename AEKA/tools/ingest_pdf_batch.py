# -*- coding: utf-8 -*-
"""
ingest_pdf_batch.py —— 批量 PDF 规范入库（用户提供版，2026-09-17）

流程（对齐既有 MH/T 7003 入库规范）：
  1) 原始 PDF -> data/raw/（只读复制，不修改源文件）
  2) PyMuPDF 提取文本（分页标记 ===== 第 N 页 / 共 M 页 =====）-> data/processed/
  3) 入库文本 -> knowledge/<分类>/
  4) 清洗版（全角转半角 + 去 CJK 字间空格）-> knowledge/<分类>/..._清洗版.txt
  5) metadata.json（字段对齐既有条目；日期等来自 PDF 原文，缺则留空并注明）

用法: python tools/ingest_pdf_batch.py [std_no ...]   # 省略则全部
"""
import json
import os
import re
import shutil
import sys
from datetime import date
from pathlib import Path

import pymupdf

AEKA = Path(r"E:\openclaw\workspace\AEKA")
SRC_DIR = Path(r"E:\规范")
RAW = AEKA / "data" / "raw"
PROC = AEKA / "data" / "processed"
KB_ROOT = AEKA / "knowledge"

# 源文件 -> 标准信息（日期/代替关系均来自 PDF 封面/公告页原文）
TARGETS = [
    {
        "src": "GB 55029-2022《安全防范工程通用规范》.pdf",
        "std_no": "GB 55029-2022", "std_name": "安全防范工程通用规范",
        "std_name_en": "General code of security engineering",
        "standard_type": "国家标准（强制性工程建设规范）", "kb_category": "01_国家标准",
        "phase": "通用规范",
        "publisher": "中华人民共和国住房和城乡建设部、国家市场监督管理总局",
        "admin_dept": "中华人民共和国公安部（主编部门）",
        "issue_date": "2022-03-10", "implement_date": "2022-10-01",
        "status": "现行",
        "date_source": "PDF 封面（2022-03-10 发布 / 2022-10-01 实施）",
    },
    {
        "src": "GB503482018安全防范工程技术标准.pdf",
        "std_no": "GB 50348-2018", "std_name": "安全防范工程技术标准",
        "std_name_en": "Technical standard for security engineering",
        "standard_type": "国家标准（工程建设类）", "kb_category": "01_国家标准",
        "phase": "技术标准（设计/施工/验收）",
        "publisher": "中华人民共和国住房和城乡建设部、国家市场监督管理总局",
        "admin_dept": "中华人民共和国公安部（主编部门）",
        "issue_date": "2018-05-14", "implement_date": "2018-12-01",
        "status": "现行",
        "date_source": "PDF 封面（2018-05-14 发布 / 2018-12-01 实施）",
    },
    {
        "src": "GB50395-2007视频安防监控系统设计规范.pdf",
        "std_no": "GB 50395-2007", "std_name": "视频安防监控系统工程设计规范",
        "std_name_en": "Code of design for video monitoring system",
        "standard_type": "国家标准（工程建设类）", "kb_category": "01_国家标准",
        "phase": "设计规范",
        "publisher": "中华人民共和国建设部",
        "admin_dept": "中华人民共和国公安部（主编部门）",
        "issue_date": "2007-03-21", "implement_date": "2007-08-01",
        "status": "现行",
        "date_source": "PDF 公告第587号（2007-03-21 批准 / 2007-08-01 实施）",
        "mandatory_clauses": "3.0.3、5.0.4(3)、5.0.5、5.0.7(3)",
    },
    {
        "src": "GBT 28181-2016 公共安全视频监控联网系统信息传输、交换、控制技术要求.pdf",
        "std_no": "GB/T 28181-2016", "std_name": "公共安全视频监控联网系统信息传输、交换、控制技术要求",
        "std_name_en": ("Technical requirements for information transport, switch and control "
                        "in video surveillance network system for public security"),
        "standard_type": "国家标准（推荐性）", "kb_category": "01_国家标准",
        "phase": "技术要求",
        "publisher": "中华人民共和国国家质量监督检验检疫总局、中国国家标准化管理委员会",
        "admin_dept": "公安部",
        "issue_date": "2016-07-12", "implement_date": "2016-08-01",
        "replaces": "GB/T 28181-2011",
        "status": "已被 GB/T 28181-2022 代替（历史版本，仅供版本对比）",
        "date_source": "PDF 封面（2016-07-12 发布 / 2016-08-01 实施；代替 GB/T 28181-2011）",
    },
    {
        "src": "GBT-50326-2017-建设工程项目管理规.pdf",
        "std_no": "GB/T 50326-2017", "std_name": "建设工程项目管理规范",
        "std_name_en": "Code for construction project management",
        "standard_type": "国家标准（工程建设类）", "kb_category": "01_国家标准",
        "phase": "管理规范",
        "publisher": "",
        "admin_dept": "中华人民共和国住房和城乡建设部（管理）；中国建筑业协会（主编单位）",
        "issue_date": "", "implement_date": "",
        "status": "现行（原文缺封面/公告页，发布与实施日期未提取）",
        "date_source": "原始 PDF 无封面与公告页（首 3 页为前言/编制信息），日期字段留空，引用前须核对官方公告",
    },
    {
        "src": "MHT5017-2017 民用运输机场航站楼安防监控系统工程设计规范.pdf",
        "std_no": "MH/T 5017-2017",
        "std_name": "民用运输机场航站楼安防监控系统工程设计规范",
        "std_name_en": ("Design code for security and protection system engineering of "
                        "civil transport airport terminal building"),
        "standard_type": "民航行业标准", "kb_category": "02_民航标准",
        "phase": "设计规范",
        "publisher": "中国民用航空局",
        "admin_dept": "中国民用航空局（批准部门）；北京中航弱电系统工程有限公司（主编单位）",
        "issue_date": "2017-11-28", "implement_date": "2018-01-01",
        "replaces": "MH/T 5017-2004",
        "status": "现行",
        "date_source": "PDF 封面（2017-11-28 发布 / 2018-01-01 施行；代替 MH/T 5017-2004）",
    },
]

FW_MAP = {chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}  # ！..～ -> !..~


def sanitize(name: str) -> str:
    """仅用于中文名称部分：去空格与标点"""
    name = re.sub(r"[\\:*?\"<>|《》]", "", name)
    name = re.sub(r"[、，,\s]+", "", name)
    return name


def file_base(std_no: str, std_name: str) -> str:
    """文件基名：标准号仅把 / 换为 _（保留空格，如 'GB 50348-2018'、'GB_T 28181-2016'）
    + 中文名去空格标点。对齐既有条目命名。"""
    no = std_no.replace("/", "_")
    return f"{no}_{sanitize(std_name)}"


def clean_text(text: str) -> str:
    out = []
    for ln in text.split("\n"):
        if ln.startswith("====="):
            out.append(ln)
            continue
        ln = "".join(FW_MAP.get(ch, ch) for ch in ln)
        CJK = r"\u4e00-\u9fff"
        ln = re.sub(r"(?<=[%s])\s+(?=[%s])" % (CJK, CJK), "", ln)
        out.append(ln)
    return "\n".join(out)


def process(t):
    src = SRC_DIR / t["src"]
    if not src.exists():
        print(f"[FAIL] 源文件不存在: {src}")
        return False
    base = file_base(t["std_no"], t["std_name"])
    cat_dir = KB_ROOT / t["kb_category"]
    cat_dir.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    PROC.mkdir(parents=True, exist_ok=True)

    # 1) 原始 PDF 复制
    raw_pdf = RAW / src.name
    if not raw_pdf.exists() or raw_pdf.stat().st_size != src.stat().st_size:
        shutil.copy2(src, raw_pdf)

    # 2) 提取文本
    doc = pymupdf.open(src)
    pages = []
    for i, page in enumerate(doc, 1):
        pages.append(f"===== 第 {i} 页 / 共 {len(doc)} 页 =====\n{page.get_text('text')}")
    n = len(pages)
    doc.close()
    full = "\n".join(pages)
    proc_txt = PROC / f"{base}.txt"
    proc_txt.write_text(full, encoding="utf-8")

    # 3) 入库文本
    kb_txt = cat_dir / f"{base}.txt"
    kb_txt.write_text(full, encoding="utf-8")

    # 4) 清洗版
    clean_txt = cat_dir / f"{base}_清洗版.txt"
    clean_txt.write_text(clean_text(full), encoding="utf-8")

    # 5) metadata
    meta = {
        "std_no": t["std_no"], "std_name": t["std_name"], "std_name_en": t.get("std_name_en", ""),
        "standard_type": t["standard_type"], "phase": t["phase"],
        "publisher": t.get("publisher", ""), "admin_dept": t.get("admin_dept", ""),
        "issue_date": t.get("issue_date", ""), "implement_date": t.get("implement_date", ""),
        "replaces": t.get("replaces", ""),
        "status": t["status"], "kb_category": t["kb_category"],
        "source": "用户 Liu 提供（人工确认入库）",
        "quality_note": "文本由 PyMuPDF 从用户提供的 PDF 直接提取（非 OCR）；已生成去字间空格/全角转半角的清洗版供检索",
        "date_source": t.get("date_source", ""),
        "kb_category_note": "分类沿用既有实践：按标准来源（国标/民航）；阶段属性见 phase 字段",
        "ingest_date": date.today().isoformat(),
        "raw_file": f"data\\raw\\{src.name}",
        "processed_file": f"data\\processed\\{base}.txt",
        "pages": n,
    }
    if t.get("mandatory_clauses"):
        meta["mandatory_clauses"] = t["mandatory_clauses"]
    (cat_dir / f"{base}_metadata.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] {t['std_no']:18s} {n:3d}页 -> {t['kb_category']}\\{base}.txt")
    return True


def main():
    want = sys.argv[1:]
    ok = 0
    for t in TARGETS:
        if want and t["std_no"] not in want:
            continue
        if process(t):
            ok += 1
    print(f"\nDONE {ok}/{len(want) if want else len(TARGETS)}")


if __name__ == "__main__":
    main()

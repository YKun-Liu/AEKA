# -*- coding: utf-8 -*-
"""
build_knowledge_index.py —— 扫描 knowledge/ 下已入库规范，按页切块生成检索索引。

输入：knowledge/01_国家标准/*.txt（raw）、*_清洗版.txt、*_metadata.json
      knowledge/02_民航标准/ 同结构
输出：data/index/knowledge_index.json
  [ {std_no, std_name, category, std_type, admin_dept, issue_date,
     implement_date, status, source(quality note), page(1-based), text} ... ]

切块策略：按页（===== 第 N 页 / 共 M 页 ===== 标记）。
正文优先用 _清洗版.txt（已去 OCR 字间空格，检索/阅读更干净）；
raw .txt 作为对照保留在 chunk 外（引用核对用，此处不进索引以省空间）。
"""
import json
import os
import re
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB_DIRS = ["01_国家标准", "02_民航标准"]
OUT = os.path.join(ROOT, "data", "index", "knowledge_index.json")

PAGE_RE = re.compile(r"^===== 第 (\d+) 页 / 共 (\d+) 页 =====$")


def load_meta(meta_path):
    try:
        m = json.load(open(meta_path, encoding="utf-8-sig"))
        return m
    except Exception:
        return {}


def split_pages(text):
    """按分页标记切成 [(page_no, content)]"""
    pages = []
    cur_page, cur_buf = None, []
    for line in text.splitlines():
        mt = PAGE_RE.match(line.strip())
        if mt:
            if cur_page is not None:
                pages.append((cur_page, "\n".join(cur_buf).strip()))
            cur_page = int(mt.group(1))
            cur_buf = []
        else:
            if cur_page is not None:
                cur_buf.append(line)
    if cur_page is not None:
        pages.append((cur_page, "\n".join(cur_buf).strip()))
    return pages


def main():
    chunks = []
    for kb in KB_DIRS:
        d = os.path.join(ROOT, "knowledge", kb)
        if not os.path.isdir(d):
            continue
        metas = {}
        for mf in glob.glob(os.path.join(d, "*_metadata.json")):
            base = mf[: -len("_metadata.json")]
            metas[base] = load_meta(mf)
        # 找清洗版（优先）或 raw txt
        txt_candidates = {}
        for tf in glob.glob(os.path.join(d, "*.txt")):
            base = tf[: -len(".txt")]
            txt_candidates.setdefault(base, tf)
        for base, meta in metas.items():
            # base 形如 'GB_T 28181-2022_公共安全...'
            # 清洗版文件名 = base + '_清洗版.txt'
            clean = base + "_清洗版.txt"
            if os.path.exists(clean):
                tf = clean
            elif base + ".txt" in txt_candidates or os.path.exists(base + ".txt"):
                tf = base + ".txt"
            else:
                print("skip no txt:", base)
                continue
            text = open(tf, encoding="utf-8").read()
            pages = split_pages(text)
            std_no = meta.get("std_no") or os.path.basename(base).split("_")[0]
            std_name = meta.get("std_name", "")
            for pno, content in pages:
                if not content.strip():
                    continue  # 空白页不入索引
                chunks.append({
                    "std_no": std_no,
                    "std_name": std_name,
                    "category": kb,
                    "std_type": meta.get("standard_type", ""),
                    "admin_dept": meta.get("admin_dept", ""),
                    "issue_date": meta.get("issue_date", ""),
                    "implement_date": meta.get("implement_date", ""),
                    "status": meta.get("status", ""),
                    "quality": meta.get("quality_note", ""),
                    "page": pno,
                    "text": content,
                })
            print(f"{kb}: {std_no} -> {len(pages)} 页")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(chunks, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"\nTOTAL chunks: {len(chunks)} -> {OUT}")
    # 统计
    by_std = {}
    for c in chunks:
        by_std.setdefault(c["std_no"], 0)
        by_std[c["std_no"]] += 1
    print("per std:", by_std)


if __name__ == "__main__":
    main()

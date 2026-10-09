# -*- coding: utf-8 -*-
"""
search_standard.py —— 民航弱电规范检索工具（V1，轻量关键词检索）

用法（命令行）:
  python search_standard.py "视频监控"                      # 全库关键词检索
  python search_standard.py "存储 天数" --std "MH/T 7003"   # 指定标准
  python search_standard.py "网络安全等级保护" --cat "01"    # 指定分类
  python search_standard.py --list                           # 列出库内标准
  python search_standard.py --info "GB/T 28181-2022"        # 标准元数据

特性:
  - 匹配已做 OCR 容错：忽略汉字/字母数字之间的空白差异（如 "28181 一 2022" 可命中 "28181-2022" 需另处理连字符，此处主要处理空格）
  - 支持多关键词 AND 逻辑（空格分隔）
  - 输出：标准号 | 页 | 片段（含高亮行上下文）

输出 JSON 模式（供 Agent 调用）:
  python search_standard.py "录像 保存" --json --top 5
"""
import argparse
import json
import os
import re
import sys

# Windows 控制台 GBK 无法输出特殊字符（如 ²/上标），强制 UTF-8
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

INDEX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "data", "index", "knowledge_index.json")


def load_index():
    if not os.path.exists(INDEX):
        sys.exit(f"索引不存在: {INDEX}，请先运行 tools/build_knowledge_index.py")
    return json.load(open(INDEX, encoding="utf-8"))


def norm(s):
    """OCR 容错：删除汉字与拉丁/数字之间、汉字之间的空格；小写化"""
    if not s:
        return ""
    s = re.sub(r"\s+", "", s)
    return s.lower()


def highlight(text, terms):
    """把命中的关键词（原文形态）加 [[]] 标记。terms 为原始词列表。"""
    out = text
    for t in terms:
        if not t:
            continue
        # 尝试原文与去空格两种
        for form in (t, norm(t)):
            if not form:
                continue
            # 原文直接高亮
            out = out.replace(form, f"[[{form}]]")
            break
    return out


def search(chunks, query_terms, std_filter=None, cat_filter=None, top=10):
    """返回 list[chunk] 每项带命中行。AND 语义（全部词都需在 chunk 文本去空格后出现）。"""
    qn = [norm(t) for t in query_terms if t]
    results = []
    for c in chunks:
        if std_filter and std_filter.lower() not in c["std_no"].lower():
            continue
        if cat_filter and cat_filter not in c["category"]:
            continue
        tn = norm(c["text"])
        if all(q in tn for q in qn):
            results.append(c)
    # 排序：命中词在文本中出现的总次数（粗略相关度）
    def score(c):
        tn = norm(c["text"])
        return sum(tn.count(q) for q in qn)
    results.sort(key=score, reverse=True)
    return results[:top]


def status_flag(c):
    """版本状态警示：已废止/被代替/历史版本的标准在结果中明确标出，防止误用旧版。"""
    s = (c.get("status") or "")
    if not s:
        return ""
    if ("已被" in s) or ("代替（历史" in s) or ("历史版本" in s) or ("废止" in s):
        return f"  ⚠ 注意：{s}"
    return ""


def format_result(c, terms, show_text=True):
    lines = [f"[{c['std_no']}] 第{c['page']}页 | {c['std_name']} | {c['category']}{status_flag(c)}"]
    if show_text and c["text"]:
        # 展示命中行及前后一行
        raw_lines = c["text"].splitlines()
        hit_lines = [i for i, l in enumerate(raw_lines)
                     if any(t in norm(l) for t in map(norm, terms) if t)]
        if hit_lines:
            lo = max(0, min(hit_lines) - 1)
            hi = min(len(raw_lines), max(hit_lines) + 2)
            body = "\n".join(raw_lines[lo:hi])
        else:
            body = c["text"][:200]
        lines.append(body[:400])
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="AEKA 规范检索")
    ap.add_argument("query", nargs="*", help="检索关键词（空格分隔 = AND）")
    ap.add_argument("--std", help="限定标准号子串，如 MH/T 7003")
    ap.add_argument("--cat", help="限定分类：01_国家标准 / 02_民航标准（可写 01/02）")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--list", action="store_true", help="列出库内标准")
    ap.add_argument("--info", metavar="STD", help="查看某标准 metadata 摘要")
    args = ap.parse_args()

    chunks = load_index()

    if args.list:
        seen = {}
        for c in chunks:
            seen.setdefault(c["std_no"], c)
        for std in sorted(seen):
            m = seen[std]
            print(f"{std:20s} {m['std_name'][:40]:42s} {m['category']} ({len([x for x in chunks if x['std_no']==std])}页)")
        return

    if args.info:
        hits = [c for c in chunks if c["std_no"].lower() == args.info.lower() or
                args.info.lower() in c["std_no"].lower()]
        if not hits:
            print("未找到:", args.info)
            return
        c = hits[0]
        print(f"标准号: {c['std_no']}")
        print(f"名称: {c['std_name']}")
        for k in ("std_type", "admin_dept", "issue_date", "implement_date", "status", "category"):
            if c.get(k):
                print(f"{k}: {c[k]}")
        if c.get("quality"):
            print(f"质量注记: {c['quality'][:120]}")
        return

    if not args.query:
        ap.print_help()
        return

    cat = args.cat
    if cat and not cat.startswith("0"):
        cat = {"01": "01_国家标准", "02": "02_民航标准"}.get(cat, cat)

    res = search(chunks, args.query, args.std, cat, args.top)
    if args.json:
        out = []
        for c in res:
            out.append({
                "std_no": c["std_no"], "std_name": c["std_name"],
                "category": c["category"], "page": c["page"],
                "snippet": format_result(c, args.query, show_text=True),
                "text": c["text"][:800],
            })
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return

    if not res:
        print("无匹配。尝试换关键词，或先 --list 查看库内标准。")
        return
    print(f"命中 {len(res)} 条：\n")
    # 顶部汇总本条结果涉及的标准版本状态（防误用旧版）
    warns = {c["std_no"]: status_flag(c) for c in res if status_flag(c)}
    for std, w in warns.items():
        print(f"⚠ {std}{w.strip()}")
    if warns:
        print()
    for c in res:
        print(format_result(c, args.query))
        print("-" * 60)


if __name__ == "__main__":
    main()

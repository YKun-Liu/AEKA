# -*- coding: utf-8 -*-
r"""prep_github.py —— GitHub 公开前核查（只读，不改任何文件）

核查项：
  1) 已跟踪文件里出现「机场/城市/人名」的文件清单与次数（不打印正文）
  2) 敏感关键词（key/secret/token/password）出现的文件与行号（只打印少量上下文）
  3) 大小异常文件（可能误入的大二进制）
输出：data/_github_check.md
"""
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"E:\openclaw\workspace")
OUT = Path(r"E:\openclaw\workspace\AEKA\data\_github_check.md")

# 只检查 AEKA 本仓库要保留的范围（排除规范正文大文件）
EXCLUDE = [
    ":!AEKA/knowledge/01_国家标准",
    ":!AEKA/knowledge/02_民航标准",
    ":!AEKA/data/index",
    ":!AEKA/data/processed",
    ":!AEKA/memory/dreaming",
    ":!AEKA/memory/*",
    ":!AEKA/data/raw",
    ":!*/dreaming/*",
]

TERMS = ["天府", "成都", "简阳", "赖改", "建设指挥部"]


def git(*args):
    r = subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True)
    return r.stdout.decode("utf-8", errors="replace")


lines = ["# GitHub 公开前核查", ""]

# 1) 机场/地名
lines.append("## 一、敏感地名/人名 命中的文件（不含规范正文与记忆）")
lines.append("")
lines.append("| 文件 | 天府 | 成都 | 简阳 | 赖改 | 指挥部 |")
lines.append("|---|---|---|---|---|---|")
files = [f for f in git("ls-files").splitlines() if f]
for f in files:
    if f.startswith(("AEKA/knowledge/01_", "AEKA/knowledge/02_",
                     "AEKA/data/index", "AEKA/data/processed",
                     "AEKA/data/raw", "memory/", "AEKA/memory/")):
        continue
    try:
        path = ROOT / f
        if not path.is_file() or path.stat().st_size > 2_000_000:
            continue
        t = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    cnt = [t.count(x) for x in TERMS]
    if any(cnt):
        lines.append(f"| {f} | " + " | ".join(str(c) if c else "-" for c in cnt) + " |")

# 2) 敏感关键词
lines += ["", "## 二、敏感关键词命中（排除标准正文）", ""]
pat = re.compile(r"(api[_-]?key|apikey|secret[_-]?key|access[_-]?token|"
                 r"password|passwd|sk-[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})",
                 re.I)
hits = 0
for f in files:
    if f.startswith(("AEKA/knowledge/01_", "AEKA/knowledge/02_",
                     "AEKA/data/index", "AEKA/data/processed", "AEKA/data/raw")):
        continue
    try:
        path = ROOT / f
        if not path.is_file() or path.stat().st_size > 2_000_000:
            continue
        for i, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if pat.search(line):
                hits += 1
                snippet = line.strip()[:90]
                lines.append(f"- `{f}:{i}` {snippet}")
                if hits > 60:
                    lines.append("- ...（超过 60 条，截断）")
                    break
    except Exception:
        continue
    if hits > 60:
        break
if hits == 0:
    lines.append("（无命中）")

# 3) 大文件
lines += ["", "## 三、已跟踪的较大文件（> 500KB）", "", "| 文件 | 大小 |", "|---|---|"]
for f in files:
    try:
        p = ROOT / f
        if p.is_file() and p.stat().st_size > 500_000:
            lines.append(f"| {f} | {p.stat().st_size/1024/1024:.2f} MB |")
    except Exception:
        continue

OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"核查完成 -> {OUT}  命中关键词 {hits} 条")

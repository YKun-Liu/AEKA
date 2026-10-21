# -*- coding: utf-8 -*-
"""
run_acceptance.py —— AEKA 验收测试自动化（可机器校验部分）

覆盖：
  A) 计算题 C01~C08 —— 断言数值与工具输出一致
  B) 检索命中 V/R —— 断言标准+关键词是否命中
  C) 版本感知 V01 —— 断言检索输出带 ⚠ 版本警示

人工抽检项（引用准确度）另见报告。
"""
import json
import os
import re
import subprocess
import sys

# 控制台统一 UTF-8（避免 GBK 编码错误）
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# 脚本在 tests/retrieval/ 下，向上两级到 AEKA 根
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PY = sys.executable
CALC = os.path.join(ROOT, "tools", "engineering_calculator.py")
SEARCH = os.path.join(ROOT, "tools", "search_standard.py")
REP_DIR = os.path.join(ROOT, "tests", "retrieval")

results = []


def run(script, args):
    out = subprocess.run([PY, script] + list(args), capture_output=True, text=True,
                         encoding="utf-8", errors="replace", cwd=ROOT)
    if out.returncode != 0:
        return (out.stdout or "") + "\n[STDERR]\n" + (out.stderr or "")
    return out.stdout


def calc(args):
    return run(CALC, args)


def search(*args):
    return run(SEARCH, list(args))


def check(cid, desc, passed, evidence=""):
    results.append((cid, desc, passed, evidence))
    print(f"[{'PASS' if passed else 'FAIL'}] {cid} {desc}")
    if not passed:
        print(f"       {evidence[:200]}")


# ---------- A) 计算题 ----------
print("=" * 60, "\nA) 计算题\n" + "=" * 60)
o = calc(["storage", "--bitrate", "4", "--channels", "200", "--days", "90"])
check("C01", "200路×4Mbps×90天 = 777,600 GB",
      "777,600 GB" in o and "43.20 GB" in o, o)
o = calc(["storage", "--bitrate", "4", "--channels", "200", "--days", "90",
          "--disk-tb", "16", "--raid", "5"])
check("C02", "16TB盘/RAID5 估算 49 块",
      "49 块" in o and "RAID5" in o, o)

o = calc(["bandwidth", "--channels", "200", "--bitrate", "4", "--peak", "1.3"])
check("C03", "200×4×1.3 = 1040 Mbps",
      "1,040 Mbps" in o or "1040" in o.replace(",", ""), o)
o = calc(["bandwidth", "--channels", "200", "--bitrate", "4", "--peak", "1.3",
          "--headroom", "0.2"])
check("C04", "加 20% 余量 → 1.25 Gbps", "1.25 Gbps" in o, o)
o = calc(["fiber", "--ptx", "0", "--prx", "-24", "--km", "10",
          "--connectors", "2", "--splices", "4"])
check("C05", "光纤余量 16.1 dB 判定满足",
      "16.10 dB" in o and "满足" in o, o)
o = calc(["ups", "--load-w", "5000", "--pf", "0.9", "--minutes", "60",
          "--battery-v", "192"])
check("C06", "UPS ≥6.94 kVA；电池 ≈34 Ah",
      "6.94 kVA" in o and "34.0" in o, o)
o = calc(["rack", "--devices", "摄像机:8x15", "交换机:2x150", "服务器:3x450"])
check("C07", "机柜 1770 W / 8.05 A / 6039 BTU/h",
      "1,770 W" in o and "8.05" in o and "6,039" in o, o)
o = calc(["ups", "--load-w", "5000", "--pf", "0.9", "--minutes", "120",
          "--battery-v", "192"])
check("C08", "2h 备电 → 电池 68 Ah（60min 的两倍）", "68" in o, o)

# ---------- B) 检索命中 ----------
print("\n" + "=" * 60, "\nB) 检索命中\n" + "=" * 60)
CASES = [
    ("R-S01", "90天保存(安检)", ["保存", "--std", "MH/T 5017"], ["4.1.7"]),
    ("R-S02", "安检部位摄像机", ["安检", "--std", "MH/T 5017"], ["4.3.1"]),
    ("R-S03", "拾音装置", ["拾音", "--std", "MH/T 5017"], ["4.3.5"]),
    ("R-S04", "UPS 1.5倍", ["UPS", "--std", "MH/T 5017"], ["1.5"]),
    ("R-S05", "备份电源2h", ["8.2.4", "--std", "MH/T 5017"], ["2h"]),
    ("R-S06", "监控中心UPS 2h", ["UPS", "--std", "MH/T 7003"], ["2 h"]),
    ("R-S07", "无人值守生物识别", ["生物特征", "--std", "MH/T 7003"], ["14.3.7"]),
    ("R-S08", "围界5m警戒", ["围界", "--std", "MH/T 7003"], ["5 m"]),
    ("R-S09", "闭锁断电状态", ["闭锁", "--std", "MH/T 5017"], ["5.3.4"]),
    ("R-S10", "备用电源GB50348", ["备用电源", "--std", "GB 50348"], ["6.12.4"]),
]
for cid, desc, sargs, expects in CASES:
    o = search(*sargs, "--top", "5")
    ok = all(e in o for e in expects)
    check(cid, desc + f"（期望 {expects}）", ok, o[:400])

# ---------- C) 版本感知 ----------
print("\n" + "=" * 60, "\nC) 版本感知\n" + "=" * 60)
o = search("统一编码规则", "--top", "5")
check("V01", "28181-2016 检索结果带版本警示",
      "已被" in o and "代替" in o, o[:400])

# ---------- 汇总 ----------
print("\n" + "=" * 60)
total = len(results)
passed = sum(1 for _, _, p, _ in results if p)
print(f"机器可校验项：{passed}/{total} 通过")
fails = [(c, d, e) for c, d, p, e in results if not p]
if fails:
    print("\n未通过：")
    for c, d, e in fails:
        print(f"  {c} {d}")

rep = os.path.join(REP_DIR, "验收结果_机器校验_2026-10-10.md")
lines = ["# AEKA 验收测试结果（机器可校验部分）2026-10-10", "",
         f"通过 {passed}/{total}", "", "| 编号 | 项目 | 结果 |", "|---|---|---|"]
for c, d, p, _ in results:
    lines.append(f"| {c} | {d} | {'✅' if p else '❌'} |")
open(rep, "w", encoding="utf-8").write("\n".join(lines))
print("\n报告 ->", rep)

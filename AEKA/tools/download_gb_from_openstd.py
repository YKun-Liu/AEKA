# -*- coding: utf-8 -*-
"""
download_gb_from_openstd.py —— 从国家标准全文公开系统（openstd.samr.gov.cn）下载
免费公开国标 PDF 到本地库，并生成 JSON 索引（本地数据库）。

机制（2026-09-06 实测）：
  - 检索列表：GET /bzgk/std/std_list?page=1&pageSize=10&p.p1=0&p.p90=circulation_date&p.p91=desc&p.p2=<关键字>（匿名可用）
  - 详情/下载入口：showInfo(hcno) → newGbInfo?hcno=... ；下载中转页 showGb?type=download&hcno=... 需登录
  - 真实文件：viewGb?hcno=... （需登录会话，匿名返回空流）
用法：
  1) python download_gb_from_openstd.py resolve          # 解析 8 本 A 档标准的 hcno（匿名）
  2) python download_gb_from_openstd.py download <cookie> # cookie 为 openstd 登录后的 Cookie 头
输出：
  - data/raw/gb_openstd_pdf/<标准号>_<名称>.pdf
  - data/index/gb_openstd_index.json
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date

BASE = "https://openstd.samr.gov.cn/bzgk"
UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Referer": BASE + "/std/",
}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_DIR = os.path.join(ROOT, "data", "raw", "gb_openstd_pdf")
IDX_DIR = os.path.join(ROOT, "data", "index")
IDX_PATH = os.path.join(IDX_DIR, "gb_openstd_index.json")

# A 档：openstd 免费池内的民航弱电相关国标（非工程建设、非采标）
TARGETS = [
    {"code": "GB 35114-2017", "name_hint": "公共安全视频监控联网信息安全技术要求"},
    {"code": "GB/T 28181-2022", "name_hint": "公共安全视频监控联网系统信息传输、交换、控制技术要求"},
    {"code": "GB/T 25724-2017", "name_hint": "安全防范视频监控数字音视频编解码"},
    {"code": "GB 20815-2006", "name_hint": "视频安防监控数字录像设备"},
    {"code": "GB/T 22239-2019", "name_hint": "网络安全等级保护基本要求"},
    {"code": "GB/T 25070-2019", "name_hint": "网络安全等级保护安全设计技术要求"},
    {"code": "GB/T 28448-2019", "name_hint": "网络安全等级保护测评要求"},
    {"code": "GB/T 21671-2018", "name_hint": "基于以太网技术的局域网系统验收测评规范"},
]


def http_get(url: str, cookie: str = "", timeout: int = 60) -> bytes:
    headers = dict(UA)
    if cookie:
        headers["Cookie"] = cookie
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def list_url(keyword: str) -> str:
    q = urllib.parse.urlencode({
        "r": "0.1", "page": 1, "pageSize": 10,
        "p.p1": 0, "p.p90": "circulation_date", "p.p91": "desc", "p.p2": keyword,
    })
    return f"{BASE}/std/std_list?{q}"


def parse_rows(html: str):
    """解析列表页表格行。返回 [{hcno, code, name, en, kind, state, issue, act}]"""
    rows = []
    for tr in re.findall(r"<tr>.*?</tr>", html, re.S):
        hcnos = re.findall(r"showInfo\('([0-9A-Fa-f]+)'\)", tr)
        if not hcnos:
            continue
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        if len(tds) < 6:
            continue
        clean = lambda s: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()
        rows.append({
            "hcno": hcnos[0],
            "code": clean(tds[1]),
            "en": clean(tds[2]),
            "name": clean(tds[4]),
            "kind": clean(tds[5]),
            "state": clean(tds[6]) if len(tds) > 6 else "",
            "issue": clean(tds[7]) if len(tds) > 7 else "",
            "act": clean(tds[8]) if len(tds) > 8 else "",
        })
    return rows


def resolve() -> dict:
    result = {}
    os.makedirs(IDX_DIR, exist_ok=True)
    for t in TARGETS:
        key = t["code"].replace("/", "").replace(" ", "")  # 检索关键词去空格
        html = http_get(list_url(key)).decode("utf-8", "replace")
        rows = parse_rows(html)
        cand = []
        for r in rows:
            if r["code"].replace(" ", "") != t["code"].replace(" ", ""):
                continue
            if r["en"]:
                continue
            if r["kind"] not in ("推标", "强标"):
                continue
            if r["state"] != "现行":
                continue
            cand.append(r)
        cand.sort(key=lambda r: r.get("act") or r.get("issue") or "")
        pick = cand[-1] if cand else None
        if pick:
            pick["name"] = pick["name"] or t["name_hint"]
            result[t["code"]] = pick
            print(f"OK  {t['code']}  hcno={pick['hcno']}  {pick['name'][:40]}  act={pick['act']}")
        else:
            print(f"MISS {t['code']}  (候选 {[(r['code'], r['kind'], r['state'], r['hcno'][:8]) for r in rows[:6]]})")
        time.sleep(0.3)
    with open(os.path.join(IDX_DIR, "gb_openstd_resolve.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    return result


def download(cookie: str) -> None:
    os.makedirs(PDF_DIR, exist_ok=True)
    os.makedirs(IDX_DIR, exist_ok=True)
    resolve_path = os.path.join(IDX_DIR, "gb_openstd_resolve.json")
    if not os.path.exists(resolve_path):
        print("请先运行 resolve 生成 hcno 映射")
        return
    resolved = json.load(open(resolve_path, encoding="utf-8"))
    index = []
    today = date.today().isoformat()
    for code, info in resolved.items():
        hcno = info["hcno"]
        name = re.sub(r'[\\/:*?"<>|]', "_", info["name"])[:80]
        fname = f"{code.replace('/', '_')}_{name}.pdf"
        fpath = os.path.join(PDF_DIR, fname)
        url = f"{BASE}/std/viewGb?hcno={hcno}"
        ok = False
        for attempt in range(3):
            try:
                data = http_get(url, cookie=cookie, timeout=120)
                if len(data) > 100_000:
                    with open(fpath, "wb") as f:
                        f.write(data)
                    print(f"OK  {code}  {len(data):,} bytes -> {fname[:70]}")
                    ok = True
                    break
                print(f"small/empty {code}: {len(data)} bytes (attempt {attempt + 1}), retry...")
            except Exception as exc:  # noqa: BLE001
                print(f"error {code}: {exc} (attempt {attempt + 1})")
            time.sleep(2)
        head = ""
        if ok:
            with open(fpath, "rb") as f:
                head = f.read(8).hex().upper()
        index.append({
            "code": code,
            "name": info["name"],
            "hcno": hcno,
            "state": info.get("state", ""),
            "issue_date": info.get("issue", ""),
            "act_date": info.get("act", ""),
            "source": "openstd.samr.gov.cn",
            "download_date": today,
            "file": os.path.relpath(fpath, ROOT) if ok else "",
            "bytes": os.path.getsize(fpath) if ok else 0,
            "magic_hex": head,
            "status": "downloaded" if ok else "failed",
        })
        time.sleep(1.0)
    with open(IDX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=1)
    print(f"\nindex -> {IDX_PATH}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    mode = sys.argv[1]
    if mode == "resolve":
        resolve()
    elif mode == "download":
        if len(sys.argv) < 3:
            print("用法: python download_gb_from_openstd.py download '<Cookie头>'")
            sys.exit(1)
        download(sys.argv[2])
    else:
        print(__doc__)

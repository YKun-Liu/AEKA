# -*- coding: utf-8 -*-
"""
fetch_gb_online.py —— openstd.samr.gov.cn 国标全文批量抓取流水线 v2（2026-09-07 实测链路）

用法:
  python fetch_gb_online.py fetch <std_no>   # 抓 online.html + 下载全部墙图
  python fetch_gb_online.py rebuild <std_no> # 瓦片重组整页 PNG
  python fetch_gb_online.py ocr <std_no>     # OCR 每页 -> ocr/page_XXX.txt
  python fetch_gb_online.py ingest <std_no>  # 合并+清洗 -> knowledge/01_国家标准/ + metadata
  python fetch_gb_online.py all <std_no>     # 以上一步到位

流水线根目录: data/gb_fetch/<std_no>/
  - online.html / pages.json / walls/img_NN.webp / pages/page_XXX.png / ocr/page_XXX.txt
"""
import json, os, re, sys, time, glob, subprocess
from datetime import date

BASE = "https://openstd.samr.gov.cn/bzgk"
COOKIE = "JSESSIONID=F813FF9FE2FC1D2957D0E01207E84257"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "gb_fetch")
KB = os.path.join(ROOT, "knowledge", "01_国家标准")

HCNO = {
    "GB 35114-2017": "B7F5589329EF98B32F0EB8ACEC341C81",
    "GB/T 28181-2022": "8BBC2475624A6C31DC34A28052B3923D",
    "GB/T 25724-2017": "03AD844464D8FCB037A52561B8EE7F8F",
    "GB 20815-2006": "871D31F656CFB0D18060DB5374CF8E8E",
    "GB/T 22239-2019": "BAFB47E8874764186BDB7865E8344DAF",
    "GB/T 25070-2019": "9FB6EE8597B21436D0E99BF44FD42C4D",
    "GB/T 28448-2019": "7E736CDF4502B6FF1258DD250AA3EC8C",
    "GB/T 21671-2018": "FD5A2CF8369330FB689D80B8A7D3ECFC",
}
INFO = {
    "GB 35114-2017": {"zh": "公共安全视频监控联网信息安全技术要求", "kind": "强制性国标", "issue": "2017-11-01", "act": "2018-11-01", "dept": "公安部"},
    "GB/T 28181-2022": {"zh": "公共安全视频监控联网系统信息传输、交换、控制技术要求", "kind": "推荐性国标", "issue": "2022-12-30", "act": "2023-07-01", "dept": "公安部"},
    "GB/T 25724-2017": {"zh": "公共安全视频监控数字视音频编解码技术要求", "kind": "推荐性国标", "issue": "2017-04-01", "act": "2017-06-01", "dept": "公安部"},
    "GB 20815-2006": {"zh": "视频安防监控数字录像设备", "kind": "强制性国标", "issue": "2006-12-01", "act": "2008-01-01", "dept": "公安部"},
    "GB/T 22239-2019": {"zh": "信息安全技术 网络安全等级保护基本要求", "kind": "推荐性国标", "issue": "2019-05-10", "act": "2019-12-01", "dept": "公安部"},
    "GB/T 25070-2019": {"zh": "信息安全技术 网络安全等级保护安全设计技术要求", "kind": "推荐性国标", "issue": "2019-05-10", "act": "2019-12-01", "dept": "公安部"},
    "GB/T 28448-2019": {"zh": "信息安全技术 网络安全等级保护测评要求", "kind": "推荐性国标", "issue": "2019-05-10", "act": "2019-12-01", "dept": "公安部"},
    "GB/T 21671-2018": {"zh": "基于以太网技术的局域网系统验收测试方法", "kind": "推荐性国标", "issue": "2018-06-07", "act": "2019-01-01", "dept": "国家标准化管理委员会"},
}
TILE_W, TILE_H = 232, 328
PAGE_W, PAGE_H = 2320, 3280


def http_get(url, timeout=180):
    headers = {
        "User-Agent": UA,
        "Referer": f"{BASE}/std/newGbInfo?hcno={re.search(r'hcno=([0-9A-Fa-f]+)', url).group(1)}" if "hcno=" in url else BASE + "/std/",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cookie": COOKIE,
    }
    if "viewGbImg" in url:
        headers["Cache-Alive"] = "chunked"
        headers["Accept"] = "image/avif,image/webp,image/apng,image/*,*/*;q=0.8"
        headers["Referer"] = f"{BASE}/std/showGb?type=online&hcno={url.split('fileName=')[1][:32]}&request_locale=zh"
        headers["Sec-Fetch-Dest"] = "image"
        headers["Sec-Fetch-Mode"] = "no-cors"
    else:
        headers["Sec-Fetch-Dest"] = "document"
        headers["Sec-Fetch-Mode"] = "navigate"
    headers["Sec-Fetch-Site"] = "same-origin"
    import urllib.request
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def std_dir(std_no):
    return os.path.join(DATA, std_no.replace("/", "_").replace(" ", "_"))


def fetch(std_no):
    hcno = HCNO[std_no]
    d = std_dir(std_no)
    os.makedirs(os.path.join(d, "walls"), exist_ok=True)
    html_url = f"{BASE}/std/showGb?type=online&hcno={hcno}&request_locale=zh"
    html = http_get(html_url).decode("utf-8", "replace")
    open(os.path.join(d, "online.html"), "w", encoding="utf-8").write(html)
    pat = re.compile(r'<div id="(\d+)" class="page" bg="([^"]+)"[^>]*>(.*?)</div>', re.S)
    pages = []
    for m in pat.finditer(html):
        pid, bg, inner = m.groups()
        spans = re.findall(r'pdfImg-(\d+)-(\d+)" style="background-position: -(\d+)px -(\d+)px;"', inner)
        pages.append({"id": int(pid), "bg": bg,
                      "spans": [[int(a), int(b), int(c), int(d2)] for a, b, c, d2 in spans]})
    if not pages:
        print(f"!! {std_no}: 0 页，html={len(html)}B（无全文/需登录/采标）")
        return False
    uniq_bg, seen = [], set()
    for p in pages:
        if p["bg"] not in seen:
            seen.add(p["bg"])
            uniq_bg.append(p["bg"])
    json.dump({"pages": pages, "uniq_bg": uniq_bg},
              open(os.path.join(d, "pages.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print(f"{std_no}: {len(pages)} 页 / {len(uniq_bg)} 墙图")
    for i, bg in enumerate(uniq_bg):
        out = os.path.join(d, "walls", f"img_{i:02d}.webp")
        if os.path.exists(out) and os.path.getsize(out) > 50000:
            continue
        ok = False
        for attempt in range(4):
            try:
                data = http_get(f"{BASE}/std/viewGbImg?fileName={bg}")
                if len(data) > 50000:
                    open(out, "wb").write(data)
                    ok = True
                    break
            except Exception as exc:  # noqa
                print(f"  wall {i} try{attempt}: {exc}")
            time.sleep(1.5)
        if not ok:
            print(f"  FAIL wall {i} {bg[:40]}")
        time.sleep(0.25)
    return True


def rebuild(std_no):
    d = std_dir(std_no)
    meta = json.load(open(os.path.join(d, "pages.json"), encoding="utf-8"))
    pages, uniq_bg = meta["pages"], meta["uniq_bg"]
    outdir = os.path.join(d, "pages")
    os.makedirs(outdir, exist_ok=True)
    from PIL import Image
    bg2idx = {bg: i for i, bg in enumerate(uniq_bg)}
    cache = {}
    for p in pages:
        out = os.path.join(outdir, f"page_{p['id']:03d}.png")
        if os.path.exists(out) and os.path.getsize(out) > 10000:
            continue
        wi = bg2idx[p["bg"]]
        if wi not in cache:
            cache[wi] = Image.open(os.path.join(d, "walls", f"img_{wi:02d}.webp")).convert("RGB")
        wall = cache[wi]
        img = Image.new("RGB", (PAGE_W, PAGE_H), "white")
        for col, row, sx, sy in p["spans"]:
            tile = wall.crop((sx, sy, sx + TILE_W, sy + TILE_H))
            img.paste(tile, (col * TILE_W, row * TILE_H))
        img.save(out)
    print(f"{std_no}: rebuild done {len(pages)} pages")


PS_OCR = r'''
$ErrorActionPreference='Stop'
try {
  Add-Type -AssemblyName System.Runtime.WindowsRuntime
  $null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
  $null = [Windows.Storage.FileAccessMode, Windows.Storage, ContentType = WindowsRuntime]
  $null = [Windows.Storage.Streams.IRandomAccessStream, Windows.Foundation, ContentType = WindowsRuntime]
  $null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation, ContentType = WindowsRuntime]
  $null = [Windows.Graphics.Imaging.SoftwareBitmap, Windows.Foundation, ContentType = WindowsRuntime]
  $null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
  $null = [Windows.Globalization.Language, Windows.Foundation, ContentType = WindowsRuntime]
} catch { exit 1 }
$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($WinRtTask, $ResultType) {
  $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
  $netTask = $asTask.Invoke($null, @($WinRtTask))
  $netTask.Wait(-1) | Out-Null
  $netTask.Result
}
$path = $env:OCR_PATH
$file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($path)) ([Windows.Storage.StorageFile])
$stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
$decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
$bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
$engine = $null
try { $lang = New-Object Windows.Globalization.Language 'zh-Hans-CN'; $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($lang) } catch {}
if (-not $engine) { $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages() }
if (-not $engine) { exit 1 }
$result = Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
foreach ($line in $result.Lines) { Write-Output $line.Text }
'''


def ocr(std_no):
    d = std_dir(std_no)
    pdir, odir = os.path.join(d, "pages"), os.path.join(d, "ocr")
    os.makedirs(odir, exist_ok=True)
    from PIL import Image
    files = sorted(glob.glob(os.path.join(pdir, "page_*.png")),
                   key=lambda x: int(os.path.basename(x)[5:8]))
    ok = err = 0
    for f in files:
        pid = int(os.path.basename(f)[5:8])
        dst = os.path.join(odir, f"page_{pid:03d}.txt")
        if os.path.exists(dst) and os.path.getsize(dst) > 20:
            ok += 1
            continue
        im = Image.open(f)
        w = 1600
        tmp = os.path.join(odir, f"_t{pid}.png")
        im.resize((w, int(im.height * w / im.width)), Image.LANCZOS).save(tmp)
        env = dict(os.environ)
        env["OCR_PATH"] = tmp
        out = subprocess.run(["powershell", "-NoProfile", "-Command", PS_OCR],
                             capture_output=True, text=True, timeout=300, env=env)
        try:
            os.remove(tmp)
        except OSError:
            pass
        if out.returncode != 0:
            err += 1
            continue
        lines = [l for l in out.stdout.splitlines() if l.strip()]
        if lines:
            open(dst, "w", encoding="utf-8").write("\n".join(lines))
        else:
            # 空白页（纯白/纯黑）OCR 无输出：写入空文件保留页序
            open(dst, "w", encoding="utf-8").write("")
        ok += 1
        if (pid + 1) % 10 == 0:
            print(f"  ocr {pid+1}/{len(files)} ok={ok} err={err}", flush=True)
    print(f"{std_no}: OCR done ok={ok} err={err} / {len(files)}")


def ingest(std_no):
    d = std_dir(std_no)
    odir = os.path.join(d, "ocr")
    files = sorted(glob.glob(os.path.join(odir, "page_*.txt")),
                   key=lambda x: int(os.path.basename(x)[5:8]))
    if not files:
        print("no ocr files, run ocr first")
        return
    total = len(files)
    parts = []
    for f in files:
        txt = open(f, encoding="utf-8").read().strip()
        pid = int(os.path.basename(f)[5:8]) + 1
        parts.append(f"===== 第 {pid} 页 / 共 {total} 页 =====\n{txt}")
    full = "\n\n".join(parts)
    info = INFO[std_no]
    fn = f"{std_no.replace('/', '_')}_{info['zh'].replace(' ', '')}"
    # sanitize file name
    fn = re.sub(r'[\\/:*?"<>|]', "", fn)
    os.makedirs(KB, exist_ok=True)
    raw_path = os.path.join(KB, fn + ".txt")
    open(raw_path, "w", encoding="utf-8").write(full)
    # cleaned version
    CJK = r'\u4e00-\u9fff\u3000-\u303f\uff00-\uffef'
    cleaned = []
    for l in full.split("\n"):
        if l.startswith("====="):
            cleaned.append(l)
            continue
        l = re.sub(r'(?<=[%s]) +(?=[%s])' % (CJK, CJK), "", l)
        l = re.sub(r'(?<=[%s]) +(?=[，。；：、（）《》“”‘’．·—％])' % CJK, "", l)
        l = re.sub(r'(?<=[，。；：、（）《》“”‘’．·—％]) +(?=[%s])' % CJK, "", l)
        cleaned.append(l)
    clean_path = os.path.join(KB, fn + "_清洗版.txt")
    open(clean_path, "w", encoding="utf-8").write("\n".join(cleaned))
    meta = {
        "std_no": std_no,
        "std_name": info["zh"],
        "standard_type": info["kind"],
        "admin_dept": info["dept"],
        "issue_date": info["issue"],
        "implement_date": info["act"],
        "status": "现行（在线预览图源抓取，非官方 PDF 版）",
        "kb_category": "01_国家标准",
        "source": "国家标准全文公开系统 openstd.samr.gov.cn 在线预览自动抓取（非人工提供，未做人工全文校对）",
        "quality_note": "全文由官方在线预览页图片经瓦片重组+OCR 生成；文字可用于检索与交叉比对，正式引用条款前应核对官方文本/纸质出版物；OCR 对个别符号（如 I/l、全半角括号）可能存在误读",
        "ingest_date": date.today().isoformat(),
        "pages": total,
        "remark": f"抓取链路见 docs/openstd抓取链路实测_2026-09-07.md；hcno={HCNO[std_no]}",
    }
    meta_path = os.path.join(KB, fn + "_metadata.json")
    json.dump(meta, open(meta_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"{std_no}: ingested -> {fn}.txt + 清洗版 + metadata ({total}页)")
    print("  raw:", raw_path)


def all_steps(std_no):
    for step in (fetch, rebuild, ocr, ingest):
        print(f"== {std_no} [{step.__name__}] ==", flush=True)
        step(std_no)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    mode, std = sys.argv[1], sys.argv[2]
    if mode not in ("fetch", "rebuild", "ocr", "ingest", "all"):
        print(__doc__)
        sys.exit(1)
    {"fetch": fetch, "rebuild": rebuild, "ocr": ocr, "ingest": ingest, "all": all_steps}[mode](std)

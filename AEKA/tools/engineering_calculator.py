# -*- coding: utf-8 -*-
"""
engineering_calculator.py —— 民航弱电常用工程计算（蓝图 Sprint 6）

子命令：
  storage    视频监控存储容量（码率×路数×天数×冗余）
  bandwidth  传输带宽（并发×码率×峰值系数）
  fiber      光纤链路预算（发射-接收 ≥ 衰减）
  ups        UPS/电池容量（负载/功率因数×安全系数；备电时长→Ah）
  rack       机柜功率/电流/散热

设计原则：
  1) 先给计算逻辑（公式+代入），再给结论 —— 对齐用户偏好
  2) 每个结果附「规范依据提示」，提示关联的知识库条款（需 Agent 用 search_standard 核实引用）
  3) 支持 --json 供 Agent 调用

用法示例：
  python tools/engineering_calculator.py storage --bitrate 4 --channels 200 --days 90
  python tools/engineering_calculator.py storage --bitrate 4 --channels 200 --days 90 --json
  python tools/engineering_calculator.py bandwidth --channels 200 --bitrate 4 --peak 1.3
  python tools/engineering_calculator.py fiber --ptx 0 --prx -24 --km 10 --connectors 2 --splices 4
  python tools/engineering_calculator.py ups --load-w 5000 --pf 0.9 --minutes 60 --battery-v 192
  python tools/engineering_calculator.py rack --devices "摄像机:8x15" "交换机:2x150" "服务器:3x450"
"""
import argparse
import json
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SEC_PER_DAY = 86400
GB = 1e9          # 十进制 GB
GIB = 1024 ** 3   # 二进制 GiB


def _fmt_gb(v):
    """给定字节数，输出常见单位"""
    return {
        "GB(十进制)": round(v / GB, 2),
        "GiB(二进制)": round(v / GIB, 2),
        "TB(十进制)": round(v / GB / 1000, 3),
        "TiB(二进制)": round(v / GIB / 1024, 3),
    }


# ---------------- storage ----------------
def calc_storage(a):
    bitrate = a.bitrate            # Mbps / 路
    channels = a.channels          # 路
    days = a.days                  # 天
    overhead = a.overhead          # 封装/文件系统开销系数（1.0 = 不计）
    redundancy = a.redundancy      # 冗余系数（1.0 = 无冗余）

    bytes_per_day_1ch = bitrate * 1e6 * SEC_PER_DAY / 8
    total_bytes = bytes_per_day_1ch * channels * days * overhead * redundancy
    total_gb = total_bytes / GB

    steps = [
        f"① 单路日数据量 = 码率 × 86400 s ÷ 8 = {bitrate} Mbps × 86400 ÷ 8 = "
        f"{bytes_per_day_1ch/GB:.2f} GB/路·天",
        f"② 基础总量 = {bytes_per_day_1ch/GB:.2f} × {channels} 路 × {days} 天 = "
        f"{bytes_per_day_1ch*channels*days/GB:,.0f} GB",
        f"③ 计入开销系数 {overhead} × 冗余系数 {redundancy} → {total_gb:,.0f} GB",
    ]

    disks = []
    if a.disk_tb:
        usable = a.disk_tb * 1000  # TB→GB（十进制）
        cnt = total_gb / usable
        disks.append(f"按 {a.disk_tb} TB/盘（十进制）估算：需 {cnt:.1f} 块 → 取整 {int(cnt)+ (1 if cnt % 1 else 0)} 块")
        if a.raid:
            # RAID5/6 有效容量折算（n 盘组，损失 1~2 盘）
            n = int(cnt) + 1
            disks.append(f"RAID{a.raid} 下按 {n} 块组阵（有效容量损失 1~2 盘容量）")

    result = {
        "计算类型": "视频监控存储容量",
        "输入": {"码率Mbps": bitrate, "路数": channels, "天数": days,
                 "开销系数": overhead, "冗余系数": redundancy},
        "计算逻辑": steps,
        "结论": {
            "总容量": _fmt_gb(total_bytes),
            "单路日数据量GB": round(bytes_per_day_1ch / GB, 3),
            "通道日总量GB": round(bytes_per_day_1ch * channels / GB, 2),
        },
        "磁盘估算": disks,
        "规范依据提示": [
            "存储天数：机场安防系统音视频保存时限——MH/T 7003-2017 第15.4.1条（不少于 90 d，另见 9.3.2 h、13.1.7）",
            "码率/帧率/分辨率：GB/T 28181-2022 传输与交换要求（第5、6章）；GB 35114-2017 信息安全要求",
            "设备与记录：GB 20815-2006 视频安防监控数字录像设备（码率、记录间隔、存储空间）",
            "→ 引用前请用 tools/search_standard.py 核实条款号与现行版本",
        ],
    }
    return result


# ---------------- bandwidth ----------------
def calc_bandwidth(a):
    ch = a.channels
    br = a.bitrate
    peak = a.peak
    base = ch * br
    peak_mbps = base * peak
    steps = [
        f"① 并发基础带宽 = {ch} 路 × {br} Mbps = {base:,.0f} Mbps",
        f"② 计入峰值系数 {peak} → {peak_mbps:,.0f} Mbps = {peak_mbps/1000:.2f} Gbps",
    ]
    extra = []
    if a.headroom:
        need = peak_mbps * (1 + a.headroom)
        extra.append(f"③ 按 {a.headroom*100:.0f}% 链路余量 → 建议链路容量 ≥ {need:,.0f} Mbps "
                     f"（{need/1000:.2f} Gbps）")
    result = {
        "计算类型": "传输带宽",
        "输入": {"并发路数": ch, "单路码率Mbps": br, "峰值系数": peak,
                 "链路余量": a.headroom},
        "计算逻辑": steps + extra,
        "结论": {"峰值带宽Mbps": round(peak_mbps, 1),
                 "峰值带宽Gbps": round(peak_mbps / 1000, 3),
                 "建议链路": f"{(peak_mbps*(1+a.headroom))/1000:.2f} Gbps" if a.headroom else None},
        "规范依据提示": [
            "网络传输带宽/传输质量/延迟：GB/T 28181-2022 第5章（传输要求）",
            "联网规模与并发布数：MH/T 7003-2017 第15.3.6条（一类/二类机场不少于 30 路同时调用一路实时图像）",
            "→ 引用前请用 tools/search_standard.py 核实条款号与现行版本",
        ],
    }
    return result


# ---------------- fiber ----------------
def calc_fiber(a):
    budget = a.ptx - a.prx
    loss_conn = a.connectors * a.conn_loss
    loss_splice = a.splices * a.splice_loss
    loss_fiber = a.km * a.km_loss
    total_loss = loss_conn + loss_splice + loss_fiber + a.margin
    residual = budget - total_loss
    ok = residual >= 0
    steps = [
        f"① 链路功率预算 = 发射功率 − 接收灵敏度 = {a.ptx} − ({a.prx}) = {budget:.2f} dB",
        f"② 连接器 {a.connectors} 个 × {a.conn_loss} dB = {loss_conn:.2f} dB",
        f"③ 熔接点 {a.splices} 个 × {a.splice_loss} dB = {loss_splice:.2f} dB",
        f"④ 光纤 {a.km} km × {a.km_loss} dB/km（{a.wavelength}） = {loss_fiber:.2f} dB",
        f"⑤ 工程余量 = {a.margin:.2f} dB",
        f"⑥ 总衰减 = {total_loss:.2f} dB",
        f"⑦ 剩余余量 = 预算 − 总衰减 = {residual:.2f} dB → {'✅ 满足' if ok else '❌ 不满足'}",
    ]
    result = {
        "计算类型": "光纤链路预算",
        "输入": {"发射功率dBm": a.ptx, "接收灵敏度dBm": a.prx, "距离km": a.km,
                 "连接器": a.connectors, "熔接点": a.splices,
                 "每公里损耗dB": a.km_loss, "波长": a.wavelength, "工程余量dB": a.margin},
        "计算逻辑": steps,
        "结论": {"功率预算dB": round(budget, 2), "总衰减dB": round(total_loss, 2),
                 "剩余余量dB": round(residual, 2), "判定": "满足" if ok else "不满足"},
        "规范依据提示": [
            "综合布线与线缆选型：GB 50311-2016（设计）、GB/T 50312-2016（验收）",
            "视频监控传输方式与线缆：GB 50395-2007 第7章（传输方式、线缆选型与布线）；MH/T 5017-2017",
            "→ 引用前请用 tools/search_standard.py 核实条款号与现行版本",
        ],
    }
    return result


# ---------------- ups ----------------
def calc_ups(a):
    load_w = a.load_w
    pf = a.pf
    va = load_w / pf
    va_design = va * a.safety
    wh = load_w * (a.minutes / 60)
    battery_ah = wh / (a.battery_v * a.inv_eff * a.discharge)
    steps = [
        f"① 视在功率 = 有功功率 ÷ 功率因数 = {load_w} W ÷ {pf} = {va:,.0f} VA",
        f"② 计入安全系数 {a.safety} → 选型容量 ≥ {va_design:,.0f} VA ≈ {va_design/1000:.2f} kVA",
        f"③ 备电能量 = {load_w} W × {a.minutes} min ÷ 60 = {wh:,.0f} Wh",
        f"④ 电池容量 ≈ 能量 ÷ (电池组电压 × 逆变效率 {a.inv_eff} × 放电系数 {a.discharge})",
        f"   = {wh:,.0f} ÷ ({a.battery_v} × {a.inv_eff} × {a.discharge}) = {battery_ah:,.0f} Ah",
    ]
    result = {
        "计算类型": "UPS 容量与电池",
        "输入": {"负载W": load_w, "功率因数": pf, "安全系数": a.safety,
                 "备电时长min": a.minutes, "电池组电压V": a.battery_v,
                 "逆变效率": a.inv_eff, "放电系数": a.discharge},
        "计算逻辑": steps,
        "结论": {"视在功率VA": round(va, 1),
                 "建议选型kVA": round(va_design / 1000, 2),
                 "备电能量Wh": round(wh, 1),
                 "电池容量Ah": round(battery_ah, 1)},
        "规范依据提示": [
            "监控中心 UPS 供电时间：MH/T 7003-2017 第15.7.3条 e)（不间断运行所需 UPS，供电时间不少于 2 h）",
            "安防系统备用电源与供电保障：GB 50348-2018 第6.12.4条（备用电源形式/应急供电时间/负载分级）",
            "建筑物电子信息系统防雷与供电：GB 50343-2012、GB 51348-2019（电气设计）",
            "→ 引用前请用 tools/search_standard.py 核实条款号与现行版本",
        ],
    }
    return result


# ---------------- rack ----------------
def parse_devices(items):
    """'摄像机:8x15' -> (名称, 数量, 单台功率W)"""
    out = []
    for it in items:
        try:
            name, spec = it.split(":", 1)
            qty, watt = spec.lower().split("x")
            out.append((name.strip(), int(qty), float(watt)))
        except Exception:
            raise SystemExit(f"设备格式应为 名称:数量x功率W，例如 摄像机:8x15  —— 收到: {it}")
    return out


def calc_rack(a):
    devices = parse_devices(a.devices)
    total_w = sum(q * w for _, q, w in devices)
    current = total_w / a.voltage
    heat_btu = total_w * 3.412
    design_w = total_w * a.safety
    steps = [f"① 设备合计功率 = " + " + ".join(f"{n} {q}×{w}W" for n, q, w in devices)
             + f" = {total_w:,.0f} W",
             f"② 电流 = {total_w:,.0f} W ÷ {a.voltage} V = {current:,.1f} A",
             f"③ 散热 ≈ {total_w:,.0f} W × 3.412 = {heat_btu:,.0f} BTU/h（≈ {total_w/1000:.2f} kW）",
             f"④ 计入配电安全系数 {a.safety} → 配电容量 ≥ {design_w:,.0f} W（{design_w/a.voltage:,.1f} A）"]
    result = {
        "计算类型": "机柜功率/电流/散热",
        "输入": {"设备": [f"{n}:{q}x{w}" for n, q, w in devices],
                 "电压V": a.voltage, "安全系数": a.safety},
        "计算逻辑": steps,
        "结论": {"设备总功率W": round(total_w, 1), "工作电流A": round(current, 2),
                 "散热BTU/h": round(heat_btu), "建议配电W": round(design_w, 1)},
        "规范依据提示": [
            "机房/数据中心：GB 50174-2017 数据中心设计规范",
            "民用建筑电气设计：GB 51348-2019",
            "→ 引用前请用 tools/search_standard.py 核实条款号与现行版本",
        ],
    }
    return result


# ---------------- main ----------------
def main():
    ap = argparse.ArgumentParser(description="民航弱电工程计算器")
    sub = ap.add_subparsers(dest="cmd", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true",
                        help="输出 JSON（Agent 调用）")

    s = sub.add_parser("storage", parents=[common], help="视频监控存储容量")
    s.add_argument("--bitrate", type=float, required=True, help="单路码率 Mbps")
    s.add_argument("--channels", type=int, required=True)
    s.add_argument("--days", type=float, required=True)
    s.add_argument("--overhead", type=float, default=1.0, help="封装/文件系统开销系数")
    s.add_argument("--redundancy", type=float, default=1.0, help="冗余系数")
    s.add_argument("--disk-tb", type=float, default=0, help="单盘容量 TB（可选）")
    s.add_argument("--raid", type=int, default=0, help="RAID 级别（5/6，可选）")
    s.set_defaults(func=calc_storage)

    b = sub.add_parser("bandwidth", parents=[common], help="传输带宽")
    b.add_argument("--channels", type=int, required=True, help="并发路数")
    b.add_argument("--bitrate", type=float, required=True, help="单路码率 Mbps")
    b.add_argument("--peak", type=float, default=1.0, help="峰值系数")
    b.add_argument("--headroom", type=float, default=0.0, help="链路余量系数（0.2 表示 20%%）")
    b.set_defaults(func=calc_bandwidth)

    f = sub.add_parser("fiber", parents=[common], help="光纤链路预算")
    f.add_argument("--ptx", type=float, required=True, help="发射功率 dBm")
    f.add_argument("--prx", type=float, required=True, help="接收灵敏度 dBm")
    f.add_argument("--km", type=float, required=True, help="链路长度 km")
    f.add_argument("--connectors", type=int, default=2)
    f.add_argument("--conn-loss", type=float, default=0.5, help="单连接器损耗 dB")
    f.add_argument("--splices", type=int, default=0)
    f.add_argument("--splice-loss", type=float, default=0.1, help="单熔接点损耗 dB")
    f.add_argument("--km-loss", type=float, default=0.35, help="每公里损耗 dB（1310nm≈0.35）")
    f.add_argument("--wavelength", default="1310nm")
    f.add_argument("--margin", type=float, default=3.0, help="工程余量 dB")
    f.set_defaults(func=calc_fiber)

    u = sub.add_parser("ups", parents=[common], help="UPS 容量与电池")
    u.add_argument("--load-w", type=float, required=True, help="负载有功功率 W")
    u.add_argument("--pf", type=float, default=0.9, help="功率因数")
    u.add_argument("--safety", type=float, default=1.25, help="安全系数")
    u.add_argument("--minutes", type=float, required=True, help="备电时长 min")
    u.add_argument("--battery-v", type=float, default=192, help="电池组标称电压 V")
    u.add_argument("--inv-eff", type=float, default=0.85)
    u.add_argument("--discharge", type=float, default=0.9)
    u.set_defaults(func=calc_ups)

    r = sub.add_parser("rack", parents=[common], help="机柜功率/电流/散热")
    r.add_argument("--devices", nargs="+", required=True, help="如 摄像机:8x15")
    r.add_argument("--voltage", type=float, default=220)
    r.add_argument("--safety", type=float, default=1.25)
    r.set_defaults(func=calc_rack)

    args = ap.parse_args()
    res = args.func(args)

    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return
    print(f"\n【{res['计算类型']}】")
    print("— 计算逻辑 —")
    for st in res["计算逻辑"]:
        print("  " + st)
    print("— 结论 —")
    for k, v in res["结论"].items():
        if v is None:
            continue
        if isinstance(v, dict):
            print(f"  {k}:")
            for kk, vv in v.items():
                print(f"    - {kk}: {vv:,}")
        else:
            print(f"  {k}: {v}")
    if res.get("磁盘估算"):
        print("— 磁盘估算 —")
        for d in res["磁盘估算"]:
            print("  " + d)
    print("— 规范依据提示（需按现行版本核实） —")
    for c in res["规范依据提示"]:
        print("  · " + c)


if __name__ == "__main__":
    main()

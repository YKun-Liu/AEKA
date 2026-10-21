# 工程工具与扩展方向（V1）

## Tool 列表（蓝图第 10 节）与实现状态

| Tool | 说明 | 状态 |
|---|---|---|
| `search_standard` | 规范检索（关键词/标准号/分类过滤，返回页级片段+metadata） | ✅ `tools/search_standard.py` + `data/index/knowledge_index.json` |
| `engineering_calculator` | 工程计算：存储容量/带宽/光纤链路预算/UPS容量/机柜功率 | ✅ `tools/engineering_calculator.py`（2026-09-17） |
| `search_knowledge` | 工程资料检索（PDF/Word/Excel） | ⬜ 待建（知识库以规范为主，资料类偏少） |
| `read_document` | 读取 PDF/Word/Excel | ⬜ 待建（当前用 PyMuPDF 直接读） |
| `generate_engineering_report` | 输出 Markdown/Word/PDF 报告 | ⬜ 待建 |

## 工程计算器用法（tools/engineering_calculator.py）

```bash
# 视频监控存储容量（码率×路数×天数×冗余）
python tools/engineering_calculator.py storage --bitrate 4 --channels 200 --days 90 \
       --overhead 1.05 --disk-tb 16

# 传输带宽（并发×码率×峰值系数，可加链路余量）
python tools/engineering_calculator.py bandwidth --channels 200 --bitrate 4 --peak 1.3 --headroom 0.2

# 光纤链路预算（发射功率−接收灵敏度 ≥ 衰减）
python tools/engineering_calculator.py fiber --ptx 0 --prx -24 --km 10 --connectors 2 --splices 4

# UPS 容量与电池
python tools/engineering_calculator.py ups --load-w 5000 --pf 0.9 --minutes 60 --battery-v 192

# 机柜功率/电流/散热
python tools/engineering_calculator.py rack --devices "摄像机:8x15" "交换机:2x150" "服务器:3x450"

# 加 --json 输出结构化结果（Agent 调用）
```

设计要点：
1. 输出**先计算逻辑（公式+代入）再结论**——对齐用户"涉及数值先讲逻辑"的偏好。
2. 每条结果附**规范依据提示**（条款号取自知识库，如 MH/T 7003-2017 §15.4.1 存储 90 d、§15.7.3 e) UPS ≥2 h）；
   提示仅为线索，正式引用前须用 `search_standard` 核实条款与现行版本。
3. 默认参数为工程常见值（1310nm 0.35 dB/km、连接器 0.5 dB、熔接 0.1 dB、功率因数 0.9、安全系数 1.25），
   可按项目实际覆盖。

## 常用工程计算（公式备查）

- 视频监控存储：`码率(Mbps) × 86400 ÷ 8 = GB/路·天`；总量 = ×路数 ×天数 ×开销 ×冗余
- 传输带宽：`并发路数 × 单路码率 × 峰值系数`；建议链路再加余量（工程常取 20%）
- 光纤链路预算：`发射功率 − 接收灵敏度 ≥ 连接器 + 熔接 + 距离×每公里损耗 + 余量`
- UPS 容量：`视在功率 = 负载功率 ÷ 功率因数 × 安全系数`；电池 `Ah ≈ Wh ÷ (电池电压 × 逆变效率 × 放电系数)`
- 机柜：`电流 = 功率 ÷ 电压`；`散热 BTU/h ≈ 功率 × 3.412`

## 知识库目录规划（蓝图第 6 节）

```text
knowledge/
├── 01_国家标准/
├── 02_民航标准/
├── 03_设计规范/
├── 04_施工规范/
├── 05_验收规范/
├── 06_设备资料/
├── 07_项目资料/
└── 08_个人经验/
```

> 现行分类实践：按**标准来源**归档（01 国标 / 02 民航），阶段属性记在 metadata 的 `phase` 字段。

## 知识 Metadata 规范

```json
{
  "title": "规范名称",
  "category": "民航标准",
  "system": "视频监控",
  "version": "版本",
  "chapter": "5.3",
  "page": 36,
  "source": "xxx.pdf",
  "authority": "发布机构",
  "effective_date": "2025-01-01"
}
```

# 工程工具与扩展方向（V1 规划）

## Tool 列表（蓝图第 10 节）

- `search_knowledge`：搜索民航弱电工程知识库（query/system/category/version/top_k）
- `search_standard`：规范查询（名称/专业系统/关键词/版本/有效期）
- `read_document`：读取 PDF/Word/Excel
- `engineering_calculator`：带宽、存储容量、光纤链路预算、UPS 容量、机柜功率
- `generate_engineering_report`：输出 Markdown / Word / PDF

## 常用工程计算（V1 逐步实现）

- 视频监控存储容量：码率 × 路数 × 天数 × 冗余
- 网络带宽：并发会话 × 平均码率 × 峰值系数
- 光纤链路预算：发射功率 − 接收灵敏度 ≥ 衰减（连接器 + 熔接 + 距离 × 每公里损耗 + 余量）
- UPS 容量：负载功率 / 功率因数 × 安全系数

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

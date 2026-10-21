# 民航弱电工程知识 Agent V1.0 开发蓝图

> 项目代号：AEKA（Airport Engineering Knowledge Agent）
> 核心平台：OpenClaw
> 目标：构建一个面向民航弱电工程管理的专业知识 Agent，支持云端与本地大模型，并逐步扩展到方案审查、工程计算、项目管理和自动办公。

---

## 1. 项目定位

### 1.1 项目目标

不是开发一个普通的聊天机器人，而是构建：

> **基于 OpenClaw 的民航弱电工程数字专家。**

第一阶段重点解决：

- 民航弱电规范查询
- 工程技术资料检索
- 工程问题问答
- 规范依据引用
- 文档分析
- 工程知识总结

最终形成：

```text
用户
 ↓
OpenClaw
 ↓
民航弱电工程 Agent
 ↓
知识检索 / 工具调用 / 记忆
 ↓
民航工程知识库
 ↓
规范、设计文件、施工方案、验收资料、设备资料、项目经验
```

### 1.2 用户背景与路线

项目开发者具备：

- 民航弱电工程管理经验
- C/C++ 软件开发经验
- Codex 辅助开发经验
- OpenClaw 使用基础

因此本项目不以“从零学习 Python/AI”为目标，而以：

> **Agent 架构 + OpenClaw 实践 + 民航专业知识数字化**

为核心。

---

## 2. V1.0 总体架构

```text
 用户
 │
 ▼
 ┌──────────────┐
 │ OpenClaw     │
 │ Gateway      │
 └──────┬───────┘
        │
        ▼
 ┌─────────────────────┐
 │ 民航弱电工程 Agent   │
 └──────────┬──────────┘
            │
   ┌────────┼────────┐
   │        │        │
   ▼        ▼        ▼
 Skills   Tools    Memory
   │        │        │
   ▼        ▼        ▼
 专业知识技能  工程工具   项目上下文
 规范查询技能  文档工具   用户偏好
 报告生成技能  检索工具   历史问题
   │
   ▼
 ┌─────────────┐
 │  RAG知识库  │
 └──────┬──────┘
        │
  ┌─────┼─────┐
  ▼     ▼     ▼
 PDF   Word  Excel
   │
   ▼
 民航工程资料
```

---

## 3. 核心设计原则

### 3.1 OpenClaw负责Agent编排

V1不从零开发Agent Loop、Planner、Tool Dispatcher、Memory Manager。

由 OpenClaw 负责：

- Agent运行
- 模型调用
- Tool调用
- Skills
- Memory
- Session
- 权限控制
- 模型切换

开发重点放在专业知识和工程工具。

### 3.2 专业知识是核心资产

真正的长期价值来自：

```text
民航规范
+
工程资料
+
项目经验
+
工程判断规则
```

### 3.3 模型与业务解耦

架构不绑定单一模型：

```text
 OpenClaw
 │
 ┌────────┴────────┐
 │                 │
 云端              本地
 │                 │
 GPT/Claude等     Qwen/DeepSeek等
```

复杂推理优先使用云端模型；文档摘要、分类、批处理等任务可以使用本地模型。

### 3.4 知识库与Agent分离

不要把所有PDF直接塞进Prompt：

```text
原始资料
 ↓
解析
 ↓
清洗
 ↓
切分
 ↓
Metadata
 ↓
Embedding
 ↓
索引
 ↓
检索
 ↓
Agent
```

---

## 4. V1.0 功能范围

### 4.1 必须实现

#### A. 民航弱电知识问答

示例：

> 机场航站楼视频监控系统验收时重点检查哪些内容？

回答必须包括：

- 结论
- 规范依据
- 资料来源
- 章节/条款
- 页码（能够获取时）
- 工程说明
- 不确定性说明

#### B. 规范检索

支持：

- 按关键词检索
- 按专业系统检索
- 按规范名称检索
- 按版本/有效期检索
- 返回原始资料依据

#### C. 工程资料检索

支持：

- PDF
- Word
- Excel

#### D. 文档分析

能够对上传的工程资料进行：

- 摘要
- 问题提取
- 风险识别
- 条款匹配

#### E. 工程报告生成

第一版支持：

- Markdown
- Word
- PDF（后续）

---

## 5. V1.0 暂不实现

以下功能放到V2以后：

- 多Agent复杂协作
- 自动修改原始工程文件
- 自动发送邮件
- 自动修改项目数据库
- 自动执行高风险系统命令
- 自动做最终工程决策
- 完全本地化运行
- 大规模企业级多租户部署

原则：

> **V1先做到"准确、可追溯、可解释"，再追求"自动化"。**

---

## 6. 知识库设计

### 6.1 建议目录

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

### 6.2 专业分类

```text
民航弱电
├── 综合布线
├── 网络
├── 视频监控
├── 门禁
├── 安防
├── 广播
├── 时钟
├── 航显
├── 信息集成
├── 楼宇自控
├── 机房
├── UPS
└── 综合弱电
```

### 6.3 知识Metadata

每个知识片段建议包含：

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

Metadata是后续实现"只检索现行规范""只搜索视频监控规范"等能力的基础。

---

## 7. RAG方案

### 7.1 V1推荐路线

第一版不要急于引入复杂向量数据库。

优先验证：

- OpenClaw Memory
- Embedding
- 轻量检索
- 自定义 `search_knowledge` Tool

如果知识量达到几十万甚至更多知识片段，再评估：

- Qdrant
- Milvus
- 其他专业向量数据库

### 7.2 文档处理流程

```text
PDF / Word / Excel
 ↓
文档解析
 ↓
文本清洗
 ↓
结构识别
 ↓
Chunk切分
 ↓
Metadata
 ↓
Embedding
 ↓
索引
 ↓
检索
 ↓
重排序
 ↓
LLM
 ↓
带依据的答案
```

### 7.3 PDF解析

初期：

- PyMuPDF

后期视实际文档情况增加：

- OCR
- 表格识别
- 扫描PDF处理

---

## 8. OpenClaw Agent设计

### 8.1 V1只设计一个主Agent

Agent名称：

```text
Civil Aviation Engineering Agent
```

不要一开始设计大量多Agent。

通过Skills扩展专业能力：

```text
 Agent
 │
 ┌───────────┼───────────┐
 ▼           ▼           ▼
 规范查询    工程知识    报告生成
 Skill       Skill       Skill
```

### 8.2 主Agent职责

主Agent负责：

1. 理解用户问题
2. 判断问题类型
3. 决定是否需要检索
4. 调用相应Skill/Tool
5. 汇总资料
6. 形成回答
7. 给出依据
8. 说明不确定性

---

## 9. Skills设计

### 9.1 civil-aviation-engineering

职责：

- 建立民航弱电工程专业角色
- 约束回答风格
- 区分规范要求和工程经验
- 禁止无依据编造规范

核心规则：

```text
你是一名民航弱电工程技术专家。

回答问题时：

1. 优先使用知识库资料。
2. 优先使用具有明确来源的规范。
3. 区分规范要求与工程经验。
4. 无法确认时明确说明。
5. 不得编造规范条款。
6. 尽可能给出资料名称。
7. 尽可能给出章节、条款、页码。
```

### 9.2 standard-search

职责：

- 识别规范类问题
- 检索相关规范
- 根据专业、系统、版本过滤
- 返回可靠的原文上下文
- 为回答提供引用依据

### 9.3 engineering-review

职责：

- 分析设计方案
- 检查施工方案
- 对照规范
- 识别潜在风险

### 9.4 report-generation

职责：

- 工程总结
- 技术说明
- 风险清单
- 周报
- 检查报告

---

## 10. Tool设计

V1建议首先开发5个Tool。

### 10.1 search_knowledge

用途：

```text
搜索民航弱电工程知识库
```

输入：

- query
- system
- category
- version
- top_k

输出：

- 文档名称
- 内容片段
- 章节
- 页码
- Metadata
- 相关度

### 10.2 search_standard

专门用于规范查询。

支持：

- 规范名称
- 专业系统
- 关键词
- 版本
- 有效期

### 10.3 read_document

用途：

读取指定PDF/Word/Excel。

### 10.4 engineering_calculator

V1可以逐步增加：

```text
带宽计算
存储容量计算
光纤链路预算
UPS容量
机柜功率
```

### 10.5 generate_engineering_report

输出：

- Markdown
- Word
- PDF

---

## 11. 核心RAG工作流

```text
用户：
某机场视频监控系统应该保存多少天？

 ↓

 OpenClaw Agent

 ↓

 判断为规范问题

 ↓

 search_standard()

 ↓

 检索相关规范

 ↓

 找到候选资料

 ↓

 读取相关上下文

 ↓

 LLM分析

 ↓

 判断是否存在可靠依据

 ↓

 输出答案
```

如果没有可靠依据：

```text
没有检索到足够可靠的规范依据。

以下内容仅作为工程经验参考：
……
```

严禁为了回答问题而编造条款。

---

## 12. 标准回答模板

建议统一输出：

```text
## 结论

……

## 依据

1. 《XXX》
  第X章第X条
  第X页

2. 《XXX》
  第X章第X条

## 工程说明

……

## 注意事项

……

## 可信度

A / B / C / D
```

---

## 13. 可信度体系

建议引入四级可信度：

| 等级 | 含义 |
|---|---|
| A | 有明确规范条款直接支持 |
| B | 多份可靠资料相互印证 |
| C | 主要来自工程经验 |
| D | 模型推测，缺乏可靠依据 |

例如：

```text
结论可信度：A

依据：
《XXXX规范》第5.3.2条
```

没有明确规范时：

```text
结论可信度：C

说明：
当前结论主要依据工程经验，
未检索到明确规范条款。
```

---

## 14. 云端与本地模型策略

### 14.1 云端模型

主要负责：

- 复杂技术分析
- 多文档综合
- 规范解释
- 方案审查
- 复杂Agent任务

### 14.2 本地模型

主要负责：

- 文档摘要
- 文档分类
- Metadata提取
- 批量预处理
- 普通问答

推荐探索：

```text
Ollama
 ↓
Qwen / DeepSeek 等本地模型
```

本地模型不承担重要工程决策的最终判断。

### 14.3 模型抽象

```text
 OpenClaw
 │
 ┌─────────┴─────────┐
 │                   │
 云端模型            本地模型
 │                   │
 复杂推理            文档处理
 规范分析            分类摘要
 方案审查            批量任务
```

---

## 15. 开发环境

建议：

```text
Windows
 +
WSL2 Ubuntu
 +
VS Code
 +
Python
 +
Git
 +
Docker（后续）
 +
OpenClaw
```

本地模型：

```text
Ollama
```

开发辅助：

```text
Codex
```

Codex负责：

- 编写Python工具
- 重构代码
- 编写测试
- 处理文档解析
- 调试工具

开发者负责：

- 架构
- 专业规则
- 数据设计
- 验收标准

---

## 16. 项目目录

建议：

```text
AEKA/
│
├── README.md
│
├── docs/
│   ├── architecture.md
│   ├── requirements.md
│   ├── knowledge-model.md
│   └── evaluation.md
│
├── knowledge/
│   ├── 01_国家标准/
│   ├── 02_民航标准/
│   ├── 03_设计规范/
│   ├── 04_施工规范/
│   ├── 05_验收规范/
│   ├── 06_设备资料/
│   ├── 07_项目资料/
│   └── 08_个人经验/
│
├── ingestion/
│   ├── pdf_parser.py
│   ├── word_parser.py
│   ├── excel_parser.py
│   └── metadata.py
│
├── tools/
│   ├── search_knowledge.py
│   ├── search_standard.py
│   ├── read_document.py
│   ├── calculate_storage.py
│   ├── calculate_bandwidth.py
│   └── generate_report.py
│
├── skills/
│   ├── civil_aviation/
│   │   └── SKILL.md
│   ├── standard_search/
│   │   └── SKILL.md
│   ├── engineering_review/
│   │   └── SKILL.md
│   └── report_generation/
│       └── SKILL.md
│
├── tests/
│   ├── knowledge/
│   ├── retrieval/
│   └── agent/
│
└── data/
    ├── raw/
    ├── processed/
    └── index/
```

---

## 17. OpenClaw配置策略

OpenClaw配置应优先使用当前版本提供的：

```text
openclaw onboard
openclaw configure
```

配置文件通常位于：

```text
~/.openclaw/openclaw.json
```

Agent工作空间单独管理。

第一阶段重点确认：

```text
Agent
├── primary model
├── fallback model
├── workspace
├── tools
└── skills
```

不要直接复制不确定版本的旧配置。

在真正实施时，应先确认本机OpenClaw版本，再按照该版本的官方配置结构写入。

---

## 18. 安全设计

### 18.1 V1采用只读原则

允许：

```text
读取文件
搜索知识
分析文档
生成报告
```

暂时禁止：

```text
删除文件
修改原始规范
修改项目原始资料
执行高风险命令
自动发送邮件
自动修改数据库
```

### 18.2 原始知识库保护

资料进入知识库前：

```text
原始资料
 ↓
人工确认
 ↓
解析
 ↓
进入知识库
```

禁止Agent自动修改原始知识。

---

## 19. 12周实施计划

### Sprint 1：OpenClaw环境

目标：

- OpenClaw版本确认
- Gateway正常运行
- 云端模型接入
- 本地模型条件确认
- Agent工作空间建立

验收：

```text
可以正常与民航工程Agent对话。
```

### Sprint 2：知识资料

目标：

- 建立知识目录
- 准备20~50份真实资料
- 建立Metadata规范
- PDF/Word/Excel解析

验收：

```text
可以从资料中提取干净文本和基本Metadata。
```

### Sprint 3：知识检索

目标：

- Embedding
- 索引
- search_knowledge
- 基础RAG

验收：

```text
输入工程问题，可以找到相关资料。
```

### Sprint 4：规范Skill

目标：

- standard-search Skill
- 规范检索
- 来源引用
- 章节/页码

验收：

```text
回答规范问题时可以提供可靠依据。
```

### Sprint 5：专业Agent

目标：

- civil-aviation-engineering Skill
- 工程回答模板
- 可信度体系
- 不确定性控制

验收：

```text
形成稳定的民航弱电专业回答风格。
```

### Sprint 6：工程工具

目标：

- 存储计算
- 网络带宽计算
- 工程报告生成

验收：

```text
Agent可以正确调用工程计算Tool。
```

### Sprint 7~8：方案分析

目标：

- 上传设计方案
- 对照规范
- 自动识别问题
- 输出问题清单

### Sprint 9~10：测试

建立：

```text
20个规范问题
20个设计问题
20个施工问题
20个验收问题
20个工程经验问题
```

共100个测试问题。

### Sprint 11：可靠性优化

重点：

- 检索准确率
- 引用准确率
- 幻觉
- 错误拒答
- 版本冲突

### Sprint 12：V1.0

形成：

```text
民航弱电工程知识 Agent V1.0
```

---

## 20. 测试与验收标准

建议：

| 指标 | V1目标 |
|---|---:|
| 正确找到相关资料 | ≥90% |
| 引用正确 | ≥90% |
| 明确说明不确定性 | ≥95% |
| 明显幻觉 | ≤5% |
| 普通问题回答成功率 | ≥90% |

重点不是让模型"什么都回答"。

而是：

> **不知道的时候敢于说不知道。**

---

## 21. V1.0最终产品形态

```text
 我的民航工程AI
 │
 ┌─────┴─────┐
 │ OpenClaw  │
 └─────┬─────┘
       │
  ┌────┼────┐
  │    │    │
 工程知识 规范检索 工程工具
  │    │    │
  ▼    ▼    ▼
 RAG知识库 标准库 计算工具
  │
  ▼
 民航弱电专业能力
```

V1完成后再逐步增加：

```text
方案审查
施工方案审查
招标文件分析
项目进度分析
会议纪要分析
工程日报
工程周报
风险预警
自动办公
```

---

## 22. V2发展方向

### V2：工程审查Agent

```text
设计文件
 ↓
规范检索
 ↓
逐项检查
 ↓
问题清单
 ↓
整改建议
```

### V3：项目管理Agent

```text
施工日志
会议纪要
监理通知
问题单
 ↓
项目Agent
 ↓
进度
风险
质量
成本
 ↓
管理报告
```

### V4：个人AI工程工作平台

```text
 OpenClaw
 │
 ┌───────────┼───────────┐
 │           │           │
 知识Agent   项目Agent   办公Agent
 │           │           │
 ▼           ▼           ▼
 规范/资料   项目管理    Word/Excel/邮件
```

---

## 23. 第一阶段实际开工顺序

不要一次实现整个系统。

严格按照：

```text
Step 1  确认Windows/WSL2环境
Step 2  确认OpenClaw版本
Step 3  确认OpenClaw当前配置
Step 4  接入一个云端模型
Step 5  建立Civil Aviation Engineering Agent
Step 6  准备20~50份工程资料
Step 7  建立知识库
Step 8  实现search_knowledge
Step 9  实现standard-search Skill
Step 10 实现引用与可信度
Step 11 建立100题测试集
Step 12 V1.0验收
```

---

## 24. 项目成功标准

这个项目最终成功的标志不是：

> "我学会了OpenClaw。"

而是：

> **当你遇到一个真实民航弱电工程问题时，可以把问题交给Agent，它能够检索你的专业资料，找到可靠依据，进行分析，并生成可以用于工程管理工作的结果。**

这才是本项目真正的目标。

---

## 25. 下一步

建议不要继续停留在架构设计阶段。

下一步直接进入：

**V0.1环境实施。**

实施顺序：

```text
Windows
 ↓
WSL2
 ↓
OpenClaw
 ↓
云端模型
 ↓
本地模型
 ↓
Agent
 ↓
第一个民航工程Skill
```

等V0.1跑通以后，再开始RAG知识库。

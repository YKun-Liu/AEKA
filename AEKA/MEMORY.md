# MEMORY.md - AEKA 长期记忆（重要决策/知识要点沉淀）

> 维护约定：日常细节记 `memory/YYYY-MM-DD.md`；跨会话重要决策/状态沉淀到本文件。只追加、不篡改历史。

## 身份与配置（2026-08-26）
- AEKA = 民航弱电工程知识 Agent，独立于 main 会话；workspace=`E:\openclaw\workspace\AEKA`，agentDir=`~\.openclaw\agents\aeka\agent`。
- 模型策略：复杂推理/规范分析用云端 DeepSeek（默认 deepseek/deepseek-v4-flash）；批量摘要/分类可切本地 `ollama/deepseek-r1:8b`。本地模型不做最终工程判断。
- 角色规则：`skills/civil-aviation-engineering/SKILL.md`（回答模板、四级可信度 A/B/C/D、反编造红线）。

## 红线（强制，源自 AGENTS.md）
- 只读：不删除文件、不修改原始规范/项目原始资料；知识入库前需用户人工确认。
- 不编造规范条款；工程结论必须有依据（规范条款 or 明确标注工程经验）；不做最终工程决策。

## 知识库进度
- ✅ 已入库：MH/T 7003-2017《民用运输机场安全保卫设施》（用户提供正式 PDF；代替 MH/T 7003-2008；2017-10-01 实施）。
  - raw PDF：`data/raw/`；提取文本：`data/processed/`；入库文本+metadata：`knowledge/02_民航标准/`；管线：`ingestion/ingest_pdf.py`。
- ✅ 已入库（2026-09-17，用户提供 PDF 共 6 本，PyMuPDF 提取非 OCR）——管线 `tools/ingest_pdf_batch.py`：
  - GB 55029-2022《安全防范工程通用规范》、GB 50348-2018《安全防范工程技术标准》、GB 50395-2007《视频安防监控系统工程设计规范》、GB/T 50326-2017《建设工程项目管理规范》、MH/T 5017-2017《民用运输机场航站楼安防监控系统工程设计规范》→ 均已入 `knowledge/01_国家标准`、`02_民航标准`（txt+清洗版+metadata）。
  - GB/T 28181-2016（用户 PDF）入库为**历史版本**，已被 2022 版代替，仅供版本对比；检索工具已加版本状态警示（`⚠ 已被代替`）。
  - ⚠ GB/T 50326-2017 原始 PDF 缺封面/公告页，发布与实施日期未提取（metadata 留空并标注），引用前需核对官方公告。
- ✅ 已入库：GB/T 28181-2022（2026-09-07 自动抓取 OCR；**非人工确认版**，正式引用需核对官方文本）。
- ✅ 已入库（2026-09-07 批量，openstd 链路 8 本）：GB 35114-2017、GB/T 25724-2017、GB 20815-2006、GB/T 22239-2019、GB/T 25070-2019、GB/T 28448-2019、GB/T 21671-2018、GB/T 28181-2022。
- 📊 当前合计：**15 部规范 / 1791 页**（01_国家标准 13 部 + 02_民航标准 2 部）；索引 `data/index/knowledge_index.json` 1781 片段。
- ✅ 题录骨架：`knowledge/00_题录库/规范题录库_民航弱电核心规范_v0.1.md`（已核实/已入库/候选三态；渠道标注）。
- ⚠️ 题录未核实的号/版本一律不得当事实引用。

## 渠道实测结论（补充 2026-09-07）
- **openstd.samr.gov.cn 无直接 PDF**：download 验证码为死代码（JS isValid 硬编码 true）；真实全文在 showGb?type=online 预览页 → 瓦片乱序图（232×328/块）→ viewGbImg?fileName= 取图（需会话 + `Cache-Alive: chunked` 头）→ 按 HTML span 坐标重组还原 → OCR。完整链路见 `docs/openstd抓取链路实测_2026-09-07.md`。
- 9/6 工具 `tools/download_gb_from_openstd.py` 的 download 模式假设失效，已由 `tools/fetch_gb_online.py` 取代。

## 渠道实测结论（补充 2026-09-17）
- **工程建设类国标（GB 50xxx/GB/T 50xxx）题录核实渠道打通**：住建部门户站内检索 API（jpaas-jsearch-web-server/interface/search/info_new），可查号/名称/发布实施日期/代替与废止关系（公告原文）。工具：`tools/verify_std_mohurd.py`。
- 住建部官网“标准公告”栏目（gongkai/fdzdgknr/bzgg）为公告权威源；**部分公告带附件 PDF**（如 GB 55029-2022 公告附件即全文），是全文获取的可利用渠道之一。
- **强制性规范体系变动警示**：GB 55xxx 系列通用规范（2022 起实施）陆续废止旧标准强条——如 GB 55029-2022 废止 GB 50348/50394/50395/50396 部分强条；GB 55024-2022、GB 55037-2022 等同理。引用旧标准强条前必须核对对应通用规范。
- 题录更正：GB 50526-2010 已被 **GB/T 50526-2021《公共广播系统工程技术标准》** 代替（2021-10-01 实施）。
- 行业标准（GA/T、SJ/T、YD/T 等）题录渠道：hbba.sacinfo.org.cn（行业标准信息服务平台，可达，待实测检索接口）。

## 方向决策（2026-09-03）
- 用户否掉"视频监控存储容量计算工具"方向（太普通）。
- 新方向：**规范检索下载 + 入库（多源知识底座）**，后续演示"国标 vs 民航标准多源交叉"。

## 渠道实测结论（2026-09-03）
- 国家标准全文公开系统 std.samr.gov.cn：✅ 通用国标（非采标 31,144 项）可下载；❌ 明确排除工程建设类 GB 50xxx。
- MH/T 官方无免费全文（靠用户提供 PDF）。
- 住建部 ccsn.gov.cn / openstd.mohurd.gov.cn 失效；mohurd 主页 JS 渲染，现行入口待定位。
- web_search：duckduckgo / perplexity 不可达；api.moonshot.ai(200)、api.minimax.io 可达 → **待用户提供 Kimi/MiniMax key 或跑 `openclaw configure --section web`**。配置备份 openclaw.json.bak-20260903。

## 进行中（2026-09-07）
- 目标站点全文抓取：需用户从浏览器详情页（Network → newGbInfo 请求）复制 Cookie 提供会话凭证；Cookie 会随登录失效，失效需重新复制。

## S3 检索层落地（2026-09-07 下午）
- 索引：`tools/build_knowledge_index.py` → `data/index/knowledge_index.json`（9 部规范 1087 页级片段，按页切块挂 metadata）。
- 检索：`tools/search_standard.py`（关键词 AND/限定 --std/--cat、--json 输出、OCR 容错去空格匹配、UTF-8 修复）。
- Skill：civil-aviation-engineering SKILL.md 新增「规范检索工作流」——问答先检索再答，引用格式《标准号》第X章第X条（第X页）。
- 演示验证：MH/T 7003 视频监控保存时限 90d（13/18/21 页多条）可命中；GB 20815 记录/存储条款可命中。
- 注意：PowerShell 管道重定向 UTF-8 会乱码（工具直接输出正常）；OCR 文本连字符/全角符号（如 `GB 20815 ． 2`）会影响精确检索，待后续优化。

## S6 工程计算工具（2026-09-17）
- `tools/engineering_calculator.py`：storage（存储容量）/ bandwidth（带宽）/ fiber（光纤链路预算）/ ups（UPS+电池）/ rack（机柜功率电流散热），支持 `--json`。
- 输出顺序：计算逻辑（公式+代入）→ 结论 → 规范依据提示（需 search_standard 核实）→ 参数假设说明。
- 规范依据已挂接知识库条款：MH/T 7003-2017 §15.4.1（存储 ≥90d）、§15.7.3 e)（UPS ≥2h）、§15.3.6（并发路数）；GB 50348-2018 §6.12.4（备用电源）；GB/T 28181-2022 第5章（传输）；GB 20815-2006（录像设备）。
- 技能已同步：`skills/civil-aviation-engineering/SKILL.md` 新增“工程计算工作流”；`references/engineering-tools.md` 更新工具清单与公式备查。
- 待建：search_knowledge、read_document、generate_engineering_report（报告生成）。

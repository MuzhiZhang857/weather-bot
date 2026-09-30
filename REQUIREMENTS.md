# REQUIREMENTS — 需求清单（ADP-1.0 §7）

> 职责：回答"项目到底要解决什么问题"。本文是 GATE 1（有无 accepted requirement）的唯一依据。
> 状态取值：**ACCEPTED**（已确认）/ **PROPOSED**（已提议待批准）/ **UNKNOWN**（无法确定，写明所需证据）/ **CONFLICT**（与代码现状冲突，已记录）。
> AI 不得自行新增 MUST 需求或升级任何状态；新需求走 PROPOSED → 用户确认 → ACCEPTED（AGENTS.md §5、ADP-1.0 §7）。

## 迁移判定规则（TASK-000，2026-09-30）

1. 有历史 PRD（`.trae/specs/weather-alert-system/spec.md`）条目且已实现并提交 → **ACCEPTED（Historical）**；
2. 无 PRD 条目、但已提交入库且被仓库内部署配置（railway.json / render.yaml）引用 → **ACCEPTED（Historical）**，标注证据；
3. **存在于未提交工作区的功能（无论是否已运行）→ PROPOSED**。存在代码 ≠ 存在需求；
4. 仓库证据无法判断意图的 → UNKNOWN，写明裁决所需证据。

> **例外记录（2026-09-30，TASK-003 任务书）**：REQ-011..014 由用户**显式批准**从 PROPOSED 升级为 ACCEPTED——这是规则 3 的唯一例外，升级依据是用户决策本身（ADR-015），不是代码存在性。

## 需求清单

### REQ-001 天气数据服务
- Priority: MUST · Status: **ACCEPTED（Historical）**
- 系统 SHALL 通过和风天气 API 获取实况、7 天预报、24h 逐时预报与生活指数，返回结构化数据。
- Evidence: .trae spec FR-1/AC-1；`services/weather_service.py`；docs/ARCHITECTURE.md §6。

### REQ-002 语义规则引擎
- Priority: MUST · Status: **ACCEPTED（Historical）**
- 系统 SHALL 基于可配置规则（代码内置 + JSON 叠加）把天气数据解析为语义标签集合。
- Evidence: .trae spec FR-2/AC-2；`services/semantic_engine.py`；ADR-006。

### REQ-003 LLM 文案生成与降级
- Priority: MUST · Status: **ACCEPTED（Historical）**
- 系统 SHALL 调用 OpenAI 兼容 LLM 按 Prompt 模板生成中文提醒；LLM 任何失败 SHALL 降级到固定模板保证推送不中断。
- Evidence: .trae spec FR-3/AC-3；`services/llm_service.py`；ADR-004/005。

### REQ-004 企业微信推送
- Priority: MUST · Status: **ACCEPTED（Historical）**
- 系统 SHALL 通过企业微信机器人 WebSocket 将 markdown 提醒送达配置的会话。
- Evidence: .trae spec FR-4/AC-4；`services/push_service.py`；ADR-009。

### REQ-005 定时完整工作流
- Priority: MUST · Status: **ACCEPTED（Historical）**
- 系统 SHALL 按 `SCHEDULE_TIME`（Asia/Shanghai）每日执行"取数 → 规则 → LLM → 推送"完整工作流。
- Evidence: .trae spec FR-5/FR-6/AC-5；`services/scheduler.py`；ADR-002/003。

### REQ-006 配置无硬编码
- Priority: MUST · Status: **CONFLICT**
- 所有配置 SHALL 来自 `.env`/环境变量，代码不得硬编码密钥。
- **冲突内容**：`qywx_websocket.py`（os.getenv 硬编码默认值）、`wechat_weather.py`（全文硬编码）、README.md"示例值"含疑似真实凭证（STATE.md §6-1）。
- 处置：活跃路径（services/*）已合规；legacy 按 ADR-012 保留，凭证处置属用户决策（STATE.md §6-1），任何人不得为"合规"擅自改 legacy。

### REQ-007 结构化日志
- Priority: SHOULD · Status: **ACCEPTED（Historical）**
- 系统 SHALL 输出东八区时间戳的结构化日志；watchdog 场景日志 SHALL 不污染 stdout。
- Evidence: .trae spec NFR-4；`main.py setup_logging`；`weather_monitor.py`（文件日志 + stdout 契约联动 REQ-013）。

### REQ-008 模块化低耦合
- Priority: SHOULD · Status: **ACCEPTED（Historical）**
- 系统 SHALL 保持 Service 层模块化架构。
- Evidence: .trae spec NFR-1；`services/` 分层；ARCHITECTURE.md §4。

### REQ-009 产品边界（Non-Goals）
- Priority: WON'T · Status: **ACCEPTED（Historical）**
- 明确不做：前端/UI 页面、完整聊天机器人、LangChain 封装、多 Agent 系统、Django 迁移（当前阶段）。
- Evidence: .trae spec Non-Goals。注意：README"预留 Django/Agent 扩展能力"仅为愿景表述，代码不存在（ARCHITECTURE.md §2）。

### REQ-010 @ 消息监听与回复（listen/both 模式）
- Priority: SHOULD · Status: **ACCEPTED（Historical）**
- 系统 SHALL 监听群内 @ 消息并经 `response_url` 回复天气提醒；`--mode both` SHALL 同时运行监听与定时推送。
- Evidence: git `2fe4ec2`、`34d4d71`、`d323f82`；`railway.json` startCommand `python main.py --mode both`。PRD 无对应条目，按迁移判定规则第 2 条认定。

### REQ-011 多城市监控
- Priority: SHOULD · Status: **ACCEPTED**（2026-09-30，TASK-003 任务书批准；ADR-015）
- 系统 SHALL 支持经由 `CITY_SLUGS`（及可选 `CITY_NAMES`）配置的城市列表，对每个城市独立执行"取数 → 规则判定 → 告警产出"；未配置 `CITY_SLUGS` 时 SHALL 回退到单城市 `CITY_ID`；城市清单为空时 SHALL 以非零退出码终止。
- 不变量：单城市取数失败 SHALL 只跳过该城市，不影响其他城市，且**不改变**该城市的既有告警状态。
- 详细设计：docs/DESIGN-watchdog.md §5.1/§5.4；AC-1/AC-4；测试：test_watchdog.py（ConfigResolutionTests / MonitorFlowTests）。

### REQ-012 告警去重与状态记忆
- Priority: SHOULD · Status: **ACCEPTED**（2026-09-30，TASK-003 任务书批准；ADR-015）
- 系统 SHALL 以"规则标签"为指纹、按城市×标签维护持久化活动态：同一标签在活动态期间的后续命中 SHALL 静默去重；一次未命中 SHALL 解除活动态（此后再命中按新告警处理）；城市取数失败 SHALL 冻结该城市状态（不误解除）；状态 SHALL 原子落盘并在重启后保持去重语义。
- **已批准的双通道决定**：定时日报（REQ-005）不接入 WeatherState 去重——日报与事件告警是两个独立语义通道（ADR-015）。
- 详细设计：docs/DESIGN-watchdog.md §5.2（状态机）；已知风险 D3（并发）/D4（抖动）按 TASK-003 决定记录接受；AC-2/AC-3；测试：test_watchdog.py（WeatherStateTests / MonitorFlowTests）。

### REQ-013 watchdog stdout 消息契约
- Priority: SHOULD · Status: **ACCEPTED**（2026-09-30，TASK-003 任务书批准；ADR-015）
- watchdog SHALL 仅在存在**新**告警事件时向 stdout 输出文案（多城市以空行分隔），无新事件时 stdout SHALL 为零字节；诊断日志 SHALL 只写文件不进 stdout；watchdog 自身 SHALL 不负责真实外部消息投递（stdout 即外部投递边界）。
- **UNKNOWN 成分（M2 终验前解决，BL-016）**：外部调度器"Hermes"（stdout 的消费方与投递方）的频率/消费方式/失败语义未验证——端到端投递正确性无法在本仓库内证明（DESIGN §5.5）。
- 详细设计：docs/DESIGN-watchdog.md §5.1/§5.3；AC-5；测试：test_watchdog.py（MonitorFlowTests）。

### REQ-014 雨/雪提前量可配置
- Priority: MAY · Status: **ACCEPTED**（2026-09-30，TASK-003 任务书批准；ADR-015）
- `precip_soon_in` 规则的提前量 SHALL 可由 `ALERT_LEAD_HOURS` 环境变量在运行时覆盖（默认 3 小时）；规则 JSON 亦 SHALL 支持字典形式精调（hours / text_keywords / pop_min / precip_min）。
- 详细设计：docs/DESIGN-watchdog.md §5.4；AC-1；测试：test_watchdog.py（PrecipSoonRuleTests）。

### REQ-015 部署路径
- Priority: MUST · Status: **UNKNOWN**
- 系统 SHALL 部署于用户确认的主路径并保持配置一致。当前三条路径并存：Railway（`railway.json`→`main.py --mode both`）、Render（`render.yaml`→`qywx_websocket.py`）、本地 Hermes-watchdog（日志证实活跃）。
- **所需证据**：用户对 STATE.md §6-2 的裁决（保留哪些、Hermes 配置在哪）。裁决后本条转 ACCEPTED 并驱动 ROADMAP M3。

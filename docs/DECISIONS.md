# DECISIONS — 架构决策记录（ADR）

> 规则：
> 1. 本文件只记录**有依据**的决策。依据 = 代码注释、git 历史、`.trae/` 规格、CHANGELOG。无依据的写 `Historical decision — rationale unknown.`，**不编造理由**。
> 2. 新的重大架构决策（换依赖、改协议、改数据流、改部署目标）必须按 §ADR 模板追加记录，格式：`ADR-NNN`。
> 3. 推翻旧决策时不要删旧条目，把 Status 改为 `Superseded by ADR-XXX`。

## ADR 模板（自 ADR-014 起，ADP-1.0 §11 要求 Alternatives）

```
### ADR-NNN: <标题>
- Date: YYYY-MM-DD
- Status: Accepted | Superseded by ADR-XXX
- Context: 为什么需要决策
- Decision: 决定了什么
- Alternatives: 考虑过哪些替代方案、为何不选（必填；"没考虑过"也要写明）
- Consequences: 带来的影响 / 代价
- Evidence: 依据（文件/commit/注释）
```

> **格式说明**：ADR-001..013 为 ADP 采纳前的旧格式（无 Alternatives 字段），按"不伪造历史"原则**不回溯改写**；自 ADR-014 起新条目必须包含 Alternatives。

---

### ADR-001: 采用模块化 Service 层架构（services/ + models/）
- Date: 2025-06（0.1.0）
- Status: Accepted
- Context: 初版是单文件脚本（wechat_weather.py → qywx_websocket.py 演进），需要语义规则、LLM、推送、调度可独立演进。
- Decision: 拆为 weather_service / semantic_engine / llm_service / push_service / scheduler 五个低耦合服务 + models 数据类层；数据流单向：取数→规则→LLM→推送。
- Consequences: 好处是可测试、可替换；代价是"模板变量构建"在 scheduler.py / main.py / weather_monitor.py 三处重复（历史演进造成，见 High Risk Areas）。
- Evidence: `.trae/specs/weather-alert-system/spec.md`（FR-1..FR-7、NFR-1）、commit `5ae1799`、`d01f1c3`。

### ADR-002: 定时调度用 APScheduler 替代 while 循环 / schedule 库
- Date: 2025-06
- Status: Accepted
- Context: spec 明确要求"不使用 while True 循环"，并预留迁移 Railway Cron。
- Decision: `services/scheduler.py` 用 APScheduler `BlockingScheduler` + `CronTrigger`；`main.py --mode both` 时在后台线程跑 BackgroundScheduler 语义等价的 BlockingScheduler。
- Consequences: 引入 apscheduler 依赖；`schedule==1.2.2` 从此闲置在 requirements.txt 中。
- Evidence: `.trae/specs/.../spec.md` AC-5、requirements.txt、services/scheduler.py。

### ADR-003: 时区统一为北京时间，调度器用 ZoneInfo("Asia/Shanghai")
- Date: 2025（commit `373f7d0` → `dca395e`）
- Status: Accepted
- Context: UTC 服务器上 CronTrigger 未指定时区导致推送从 08:00 偏移到 16:00。
- Decision: scheduler 用 `ZoneInfo("Asia/Shanghai")`；main/monitor/state 用固定 `timezone(timedelta(hours=8))`；日志 formatter 用东八区。
- Consequences: 存在两套等价实现（中国无夏令时，当前无实际差异）；改动时间逻辑时两处都要看。
- Evidence: CHANGELOG.md [Unreleased]、commits `373f7d0`、`1b346dd`、`dca395e`。

### ADR-004: LLM 调用用裸 requests 而非 openai SDK
- Date: 2025
- Status: Accepted
- Context: README 宣称集成 openai 兼容接口；requirements 里有 `openai==1.54.3`。
- Decision: `llm_service.py` 用 requests.Session + urllib3 Retry 直接 POST `/chat/completions`，并 `trust_env=False` + 启动前清除代理环境变量。
- Consequences: openai 依赖成为死重；但换来对超时/重试/代理行为的完全控制。
- Evidence: services/llm_service.py 全文、commit `2c60399`。为什么不用已安装的 openai SDK — Historical decision — rationale unknown.

### ADR-005: LLM 失败必须降级到固定模板，推送永不中断
- Date: 2025
- Status: Accepted
- Context: 天气提醒是定时任务，LLM 超时/欠费不应导致当天无推送。
- Decision: `generate_alert()` 捕获一切异常 → `generate_simple_alert()` markdown 模板；配置缺失直接走降级。
- Consequences: 排查 LLM 故障时必须看日志（"使用降级方案"），不能只看是否收到消息。
- Evidence: services/llm_service.py、commit `2c60399`（"添加重试和降级方案"）。

### ADR-006: 语义规则 = 代码内置核心规则 + 双层 JSON 叠加
- Date: 2025
- Status: Accepted
- Context: 需要"开箱即用 + 用户可自定义"的规则体系。
- Decision: 7 条核心规则硬编码在 `SemanticEngine._get_core_rules()`；`config/weather_rules_default.json`（9 条）与 `weather_rules_user.json` 依次追加；用户文件改坏只影响其自身。
- Consequences: 条件类型名成为 JSON 与代码间的字符串契约；每条 JSON 规则只能有一个条件（_load_rule_file 取 conditions 第一个 key）。
- Evidence: services/semantic_engine.py、commit `b0492a7`（"semantic engine now correctly loads rules from JSON config files"）。

### ADR-007: watchdog 的 stdout 即消息通道（Hermes 契约）
- Date: 2026-09（未提交工作区）
- Status: Accepted
- Context: 弃用常驻 WS 进程的方案后，需要一个外部调度器能直接投递的极简接口。
- Decision: `weather_monitor.py` 日志只写文件；stdout 仅在命中新告警时打印 LLM 文案（多城市用空行连接）；未命中静默。外部调度器（"Hermes"）读 stdout 投递微信。
- Consequences: 任何向 stdout 打印的改动（如 print 调试）都会污染投递内容；Hermes 的实现细节不在本仓库。
- Evidence: weather_monitor.py 模块 docstring、setup_logging 注释。Hermes 是什么 — UNKNOWN — requires verification。

### ADR-008: 告警去重以"规则标签"为指纹，按城市×标签持久化活动态
- Date: 2026-09（未提交工作区）
- Status: Accepted
- Context: watchdog 会被高频调度，天气数值微抖不应重复轰炸；同时雨雪等事件解除后应能再次提醒。
- Decision: 以 tag 为身份（不掺时间戳/数值）；每城市每 tag 一条活动态记录落盘 `state/weather_state.json`（原子写）；命中即登记，一次未命中即解除；不设全局冷却。
- Consequences: 规则阈值在边界附近抖动时可能产生"解除→再提醒"循环；状态文件是行为的一部分，清空它会导致重复提醒。
- Evidence: services/weather_state.py 模块 docstring（完整设计论证）。

### ADR-009: 企业微信消息固定 markdown 格式，心跳只被动响应 ping
- Date: 2025（commits `34d4d71`、`d323f82`、`4f3c38f`）
- Status: Accepted
- Context: 曾尝试其他 msgtype 与主动心跳，出现"发送成功但收不到消息"与"订阅失败"两类问题。
- Decision: `PushMessage.msgtype` 固定 `markdown`（代码注释"恢复为 markdown 格式，与旧版一致"）；不主动发心跳，收到服务器 `ping` 才回 `pong`。
- Consequences: push_service._on_message 的 pong 分支是存活性关键代码，勿删；消息格式调整需对照旧版 qywx_websocket.py。
- Evidence: services/push_service.py 注释、`.trae/documents/message_send_debug_plan.md`、commits `d323f82`、`34d4d71`。

### ADR-010: 启动时清除代理环境变量（国内网络必需）
- Date: 2025
- Status: Accepted
- Context: 开发/部署环境存在 HTTP(S)_PROXY 时，国内 API（和风、LLM、企业微信）请求失败或绕路。
- Decision: main.py 与 weather_monitor.py 在导入任何网络模块前 `os.environ.pop` 四个代理变量；LLM session 额外 `trust_env=False`。
- Consequences: 需要走代理的环境（如海外 CI）反而无法直接运行——这是有意取舍。
- Evidence: main.py 头部注释、weather_monitor.py 注释（"国内网络必需"）、llm_service.py。

### ADR-011: Windows 下 watchdog stdout 强制 UTF-8
- Date: 2026-09（未提交工作区）
- Status: Accepted
- Context: Windows 默认 stdout 编码 gbk，提醒文案中的 emoji 会触发 UnicodeEncodeError 使脚本崩溃。
- Decision: weather_monitor.py 入口 `sys.stdout.reconfigure(encoding="utf-8", errors="replace")`，失败则用 TextIOWrapper 兜底。
- Consequences: 无（防御性代码）。
- Evidence: weather_monitor.py 第 20-28 行注释。

### ADR-012: 旧版脚本 qywx_websocket.py / wechat_weather.py 保留不删
- Date: 2025
- Status: Accepted
- Context: README 称 qywx_websocket.py 为"旧版本 WebSocket（保留）"；render.yaml 启动命令仍指向它。
- Decision: 不删除旧脚本。
- Consequences: 旧脚本内含**硬编码的真实凭证**与独立重复逻辑，构成安全与技术债（见 STATE.md）；删除/清理需用户决策。
- Evidence: README.md 项目结构注释、render.yaml。为什么不清理 — Historical decision — rationale unknown.

### ADR-013: 部署目标从常驻云进程转向本地 watchdog（演进方向）
- Date: 2026-09（未提交工作区，未正式定稿）
- Status: Accepted（有日志证据）／待用户确认终态
- Context: Railway 免费实例休眠、企业微信 WS 常驻连接维护成本高。
- Decision（事实描述）: 2026-09 起新增 weather_monitor.py + weather_state.py + 多城市环境变量，且本地日志显示 watchdog 每日运行；Railway/Render 配置仍保留在仓库中未删。
- Consequences: 仓库内同时存在三条部署路径（Railway / Render / Hermes-watchdog），文档必须三者并述；最终废弃哪条由用户决定。
- Evidence: 未提交 diff（git status）、logs/weather_bot.log（2026-09-30 记录）、.env 中 CITY_SLUGS/ALERT_LEAD_HOURS。

### ADR-014: 采纳 ADP-1.0 作为项目开发治理协议（Phase A+B，Phase C 暂缓）
- Date: 2026-09-30
- Status: Accepted
- Context: 接管验证（2026-09-30）表明现有轻量体系能回答"不该碰什么"，但缺规划层（REQUIREMENTS/ROADMAP/BACKLOG/DEVELOPMENT_LOG 均不存在）与过程纪律（任务状态机、验证分级、No False Completion），冷启动 Agent 无法从仓库回答"现在该做什么"（ADP-1.0 §50 第一条不满足）。
- Decision: 正式采用 ADP-1.0。Phase A（流程层）：AGENTS.md 引入协议入口与七阶段生命周期、验证分级 L0-L4 声明、No False Completion、六态任务状态机、ADR 增 Alternatives 字段。Phase B（规划层）：新增 REQUIREMENTS.md / ROADMAP.md / BACKLOG.md / DEVELOPMENT_LOG.md，协议原文存档于 docs/ADP-1.0.md。Phase C（形式统一：HANDOFF 迁址 docs/、TASK 命名变更、contracts/）**暂缓，不属于本决策**。
- Alternatives: ① 维持现有轻量体系（否——规划层缺失使冷启动失败风险持续存在）；② 全量采纳含 Phase C（否——纯形式变更收益低，违背协议 §41 文档新鲜度原则，且现有 .ai/HANDOFF.md 已满足交接职能）；③ 只在 AGENTS.md 写纪律、不建新文件（否——协议 §2.1 Repository over Memory：不落盘的规划等于不存在）。
- Consequences: 自 TASK-000 起新任务必须走六态状态机并声明验证级别；watchdog 相关需求以 PROPOSED 进入 REQUIREMENTS（REQ-011..014），其收敛依赖用户裁决（M2 退出标准）；历史任务 001 与 ADR-001..013 保留旧格式不回溯；STATE.md 技术债条目迁移至 BACKLOG。
- Evidence: 用户 TASK-000 任务书（2026-09-30，含 Phase 裁决与 watchdog 迁移规则）；接管验证记录（.ai/HANDOFF.md 首条交接）；docs/ADP-1.0.md（协议原文存档）。

### ADR-015: Watchdog 产品化基线（REQ-011..014 批准）与双通道语义分离
- Date: 2026-09-30
- Status: Accepted
- Context: TASK-002 将 watchdog 逆向规格化为 REQ-011..014（PROPOSED）并提出 Q1-Q4；TASK-003 任务书由用户作出全部裁决，实现需收敛到该基线（修复 D1、补测试、state git 策略、文档对齐）。
- Decision: ① REQ-011..014 全部 ACCEPTED；② **事件告警与定时日报是两个独立语义通道**——事件告警走 WeatherState 去重，定时日报（REQ-005）不接入去重；③ 配置不得依赖 CWD——D1 以"默认目录锚定模块位置"修复，而非约束外部调度器；④ watchdog 自身不做真实消息投递，stdout 保持为外部投递边界；⑤ D3（无并发锁）与 D4（无迟滞）接受为已知风险，本期不实现；⑥ 运行时状态不入库（state/* gitignored，保留 .gitkeep）。
- Alternatives: ① 部分批准（仅 REQ-011+012 等）——否：四条需求是同一功能闭环，拆开产生半成品语义；② 日报也接入去重——否：用户明确两通道语义不同（日报=每日固定摘要，事件=新发生才提醒），接入去重反而吞掉日报；③ D1 用"约束 Hermes 固定 CWD"替代代码修复——否：配置健壮性属代码自身职责，依赖外部调度器的隐式约束脆弱且不可验证；④ 引入文件锁/迟滞——否：无 Hermes 并发语义证据，先记录风险待 Integration Evidence。
- Consequences: 语义引擎默认配置路径改变（相对 CWD → 相对模块），显式 config_dir 入参不变；test_watchdog.py 22 例进入 verify.py 闭环（L1+L2 offline）；M2 剩余收敛项=commit 授权（Review 后）+ BL-014 README 对齐 + BL-016 Hermes 证据；state/weather_state.json 从此不入库。
- Evidence: 用户 TASK-003 任务书（Authorization / Explicit Design Decisions / D3 D4 Handling / Hermes Information 节）；docs/DESIGN-watchdog.md（已冻结为基准）；REQUIREMENTS.md REQ-011..014。

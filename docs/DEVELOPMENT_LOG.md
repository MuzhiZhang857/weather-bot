# DEVELOPMENT_LOG — 重要开发事件（ADP-1.0 §43）

> 职责：记录里程碑完成、重大决策、重大事故、重要失败尝试、跨 Agent 交接检查点。
> **不记录**普通代码操作流水账（那是 git log 的职责）。建立于 TASK-000（2026-09-30）；此前事件按仓库证据回填。

## 2026-09-30 · Watchdog 实现收敛（TASK-003，READY_FOR_REVIEW）

- 用户批准 REQ-011..014 为 **ACCEPTED** 并给出显式设计决定（ADR-015）：事件告警与定时日报**双通道分离**（日报不接 WeatherState）；配置不得依赖 CWD；watchdog 不做真实投递（stdout 为投递边界）；D3/D4 接受为已知风险不实现锁/迟滞。
- **D1 修复**：SemanticEngine 默认配置目录由相对 CWD 改为相对模块定位（项目根/config），显式入参兼容——这是本任务唯一的业务代码行为变化（修复缺陷，非语义变更）。
- **D2 补测**：新增 `test_watchdog.py`（unittest，22 例，全离线）：状态机（新事件/去重/解除/再告警/持久化/恢复/损坏容错/多城市隔离/原子写）、precip_soon_in 三信号与窗口边界、ALERT_LEAD_HOURS 覆盖、城市解析全形式、CWD 无关加载（子进程验证）、monitor 流程离线集成（stdout 契约 + 取数失败冻结状态，mock 外部服务）。verify.py 升级为三步闭环。
- **State git 策略**：`state/*` gitignore（保留 .gitkeep），现有运行数据未动。
- **文档对齐**：DESIGN-watchdog 冻结为 ACCEPTED 基准（Q1-Q4 决议内嵌）；REQUIREMENTS/ARCHITECTURE/STATE/ROADMAP/BACKLOG 同步；Hermes 集成证据立案 BL-016（M2 终验前解决）。
- 验证级别：L0 + L1 + L2(offline)（详见任务 Completion Evidence）。无真实消息发送；未 commit（等 Review 后授权）。
- **Gate Review Round 1**（2026-09-30）：CONDITIONAL PASS。整改：AC-3 损坏容错补真实"非法 JSON"故障模式测试（tests/fixtures/ 静态 fixture + test_corrupted_json_starts_empty，测试 22→23 例）；ResourceWarning 立案 BL-017。教训入档：**验收标准的证据必须覆盖设计声明的每一类故障模式**——"文件不是文件"与"文件内容损坏"是两条不同的容错路径。
- **Final Review**（2026-09-30）：**PASS** → TASK-003 **COMPLETED**。Git checkpoint：单 atomic commit `feat: finalize watchdog implementation`（watchdog 实现 + D1 修复 + 23 例测试 + state git 策略 + REQ/DESIGN/ADR/任务记录；hash 见 git log）。M2 剩余：BL-014（README 对齐）、BL-016（Hermes 证据）。

## 2026-09-30 · Watchdog 需求与设计正式化（TASK-002）

- 用户指令对 watchdog 做"实现 → 需求 → 设计 → 缺陷 → 正式 REQ/Design/AC"分解。
- 产出 `docs/DESIGN-watchdog.md`（PROPOSED）：14 条运行时行为事实（file:line 级）、8 项 Agent 设计（S1-S8）及合理性论证、8 项缺陷（D1-D8）及处置方案、正式设计规格与 8 条验收标准（AC-1..8）。
- REQUIREMENTS.md REQ-011..014 精化为 SHALL 语句 + 不变量，**状态保持 PROPOSED**；4 个未决问题（Q1-Q4）提交用户裁决。
- 任务编号修正：watchdog 主任务为 **TASK-003**（此前文档口头所称"TASK-001"与已归档的 001-agent-handoff-bootstrap 冲突，以文件编号为准）。
- 业务代码零改动。

## 2026-09-30 · 项目正式采用 ADP-1.0（Phase A + B）

- 用户裁决采纳 ADP-1.0：**Phase A（流程层）与 Phase B（规划层）实施；Phase C（HANDOFF 迁址、TASK 改名、contracts/）暂缓**。
- 落地内容：协议原文存档 `docs/ADP-1.0.md`；新增 REQUIREMENTS.md / ROADMAP.md / BACKLOG.md / DEVELOPMENT_LOG.md；AGENTS.md、tasks/README.md、DECISIONS.md 升级（七阶段、验证分级 L0-L4、No False Completion、六态任务状态机、ADR 增 Alternatives）。
- 决策记录：ADR-014；执行任务：TASK-000（tasks/completed/）。
- 历史兼容决定：任务 001 与 ADR-001..013 为采纳前产物，保留原格式不回溯改写。

## 2026-09-30 · watchdog 真实开发状态盘点（TASK-000 迁移发现）

- watchdog 功能（多城市、24h 逐时、去重状态、stdout 契约）于 ADP 采纳前由前序 Agent 开发，**至今未提交**（git status：6 modified + 4 untracked）。
- 运行证据：`logs/weather_bot.log` 2026-09-30 12:57 双城市完整执行并静默去重退出。
- 需求判定：对应 REQ-011..014 全部记 **PROPOSED**——代码存在且已运行 ≠ 需求成立；无 PRD/正式设计来源，升级 ACCEPTED 需用户裁决（ROADMAP M2 Exit）。

## 2026-09-30 · ADP 采纳前历史问题归档（TASK-000 迁移确认）

以下问题已在 BACKLOG / STATE 建档，此处留事件记录防遗失：

- **凭据暴露面**：README"示例值"与 legacy 脚本硬编码疑似真实凭证 → 阻塞决策（STATE.md §6-1），处置将涉轮换与 Git 历史评估（ADP-1.0 §39 流程）。
- **已知缺陷 B1-B4**（损坏测试 / JSON 单条件 / CWD 相对路径 / 导出缺失）→ BL-001/007/008/009。
- **部署配置漂移**：render.yaml（旧脚本）vs railway.json（main.py both）vs 本地 watchdog（日志证实活跃）→ M3 BLOCKED。
- **任务 001 状态跳变**：其 Active→Done 不符合新六态状态机且无 Completion Evidence；按"不伪造历史"原则保留原样，仅在此声明其属 ADP 采纳前任务。

## 2025 年（ADP 采纳前）· 历史事故备查（证据：git log / .trae 文档）

- **消息"发送成功但收不到"**：对比新旧消息格式后，msgtype 恢复 markdown 并改用 response_url 回复（`.trae/documents/message_send_debug_plan.md`；commit `34d4d71`；ADR-009）。
- **心跳缺失致订阅失败**：企业微信 WS 需被动响应 ping/pong（commit `d323f82`；ADR-009，push_service 相关代码现列为存活性关键代码）。
- **UTC 服务器定时偏移**：CronTrigger 未指定时区致 08:00 变 16:00，改用 `ZoneInfo("Asia/Shanghai")`（commit `dca395e`；ADR-003；CHANGELOG [Unreleased] 有记）。
- **CHANGELOG.md 自 2025-06 起停滞**：此后事件以本文件 + git 历史为准；是否补记/归档见 BL-010。

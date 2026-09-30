# TASK-000: Adopt ADP-1.0

- ID: TASK-000
- Status: COMPLETED
- Requirement: 元任务——无对应产品 REQ；来源为用户直接决策（2026-09-30 任务书，记为 ADR-014）
- Created: 2026-09-30
- Completed: 2026-09-30

## Objective

将 weather-bot 正式迁移到 AI Development Protocol v1.0（ADP-1.0），建立可追踪、可验证、可跨 Agent 接管的开发流程。不开发任何业务功能。

## Why

接管验证（2026-09-30）表明现有体系缺规划层与过程纪律：冷启动 Agent 能知道"不该碰什么"，但无法从仓库回答"现在该做什么"（无 REQUIREMENTS/ROADMAP）。

## Evidence

- 用户任务书（本轮对话，裁决 Phase A+B 采纳、C 暂缓）
- ADP-1.0 协议原文（将存档至 docs/ADP-1.0.md）
- docs/STATE.md、docs/ARCHITECTURE.md、.ai/HANDOFF.md（现状）

## Scope

### Included

- Phase A：AGENTS.md 升级（协议入口、七阶段、验证分级 L0-L4、No False Completion、Scope 纪律、六态任务状态机、ADR 模板加 Alternatives、任务模板加 Requirement/Out of Scope/Completion Evidence）
- Phase B：新增 REQUIREMENTS.md、ROADMAP.md、BACKLOG.md、DEVELOPMENT_LOG.md
- 同步：STATE.md（技术债迁移、§7 改当前态）、.ai/HANDOFF.md（模板加 Milestone + 新记录）、DEVELOPMENT.md（轻量对齐）
- 归档协议原文至 docs/ADP-1.0.md

### Excluded（Phase C 及一切业务变更）

- HANDOFF 迁址 docs/、TASK 命名体系变更、contracts/ 建立
- 修改 watchdog 功能实现、修复 test_weather_service.py、修改 API/协议/部署配置/依赖
- 删除 legacy code、重构业务代码、修改 secrets、push Git、真实消息发送
- 回溯改写历史任务（001）与旧 ADR（001-013）的格式

## Design

按用户任务书直接实施；watchdog 相关需求一律记 PROPOSED（无 PRD/正式设计来源，运行日志不构成需求批准）；技术债等非阻塞事项迁移 BACKLOG，阻塞决策保留 STATE.md §6。

## Acceptance Criteria

- [x] AC-1 Phase A 完成（AGENTS.md / tasks/README.md / DECISIONS.md 升级）
- [x] AC-2 Phase B 完成（四个新文件建立）
- [x] AC-3 Phase C 未被执行
- [x] AC-4 watchdog 在 REQUIREMENTS 中为 PROPOSED，未升 ACCEPTED
- [x] AC-5 文档间无未记录冲突（职责不重叠）
- [x] AC-6 无未经授权的业务代码修改
- [x] AC-7 最小验证流程通过（L0+L1）

## Verification

`.venv2/Scripts/python.exe scripts/verify.py`（L0+L1）；grep 核查 REQ-011..014 状态；git diff 审计（仅 .md 变更）；交叉文档职责核查。

## Risks

- 文档职责重叠（STATE vs BACKLOG vs ROADMAP）——用"每事一处"原则规避，迁移后 STATE §5 只留指针
- 新旧模板并存造成 Agent 困惑——AGENTS.md 明确"自 TASK-000 起新任务用新状态机，历史不回溯"

## Dependencies

无外部依赖；依赖既有 docs/ 体系与本轮接管验证结论。

## Completion Evidence

- Tests: `scripts/verify.py` → compile PASS + semantic PASS（8 场景），退出码 0。验证级别：**L0+L1**（L2-L4 未执行——本次任务无外发行为，也无需真实网络验证）。
- Commands: `grep` 核查（REQ-011..014 全 PROPOSED；AGENTS.md 引用 ADP-1.0/REQUIREMENTS/ROADMAP/BACKLOG/DEVELOPMENT_LOG 全部命中；READY_FOR_REVIEW 已落地于 AGENTS.md 与 tasks/README.md）；`git diff --stat` 与任务前基线**逐字一致**（6 files, 241+/50-）→ 业务代码零改动。
- Git commit: 未提交（用户未授权 push/commit）。
- Review: 发现并当场修正 3 处本人引入的交叉引用错误（STATE §6 条数"五项"→四项 ×2 处、ROADMAP M2 Blockers "1/2/4/5"→"1/2/4"）；BL-011 与 STATE §6-4 职责重叠 → 已改为"裁决在 §6-4，执行项在 BL-011"的分工并互相引用。最终状态：无未记录冲突。收尾后按 Mimosa L2 复查意见微调 AGENTS.md §4 `.env` 行措辞（拆分凭据禁止语义与外发指引的同行共现，实质规则不变）。

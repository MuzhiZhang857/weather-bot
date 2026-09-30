# TASK-002: Watchdog 需求与设计正式化

- ID: TASK-002
- Status: COMPLETED
- Requirement: 用户直接指令（2026-09-30："现有 Watchdog 到底实现了什么 → 行为分类 → 缺陷 → 形成正式 REQ + Design + AC"）
- Created: 2026-09-30
- Completed: 2026-09-30

## Objective

对未提交的 watchdog 功能做逐文件、可追溯的事实分解，把 REQ-011..014 从一句话 PROPOSED 精化为完整 SHALL 语句，产出正式设计文档（含缺陷处置与验收标准），供用户裁决是否 ACCEPTED。

## Why

M2（Watchdog）收敛的第一道门槛：没有正式需求语句与设计文档，用户无法裁决"批准什么"；没有 AC，完成无法客观验证（ADP-1.0 GATE 1/3）。

## Evidence

- `weather_monitor.py`、`services/weather_state.py`、`services/weather_service.py`、`services/semantic_engine.py`、`models/weather_types.py`、`config/weather_rules_default.json`、`.env.example`（全部为未提交工作区版本）
- 既有决策：ADR-007/008/011/013；需求：REQ-001..003/007（被 watchdog 复用）
- 运行证据：logs/weather_bot.log（2026-09-19 起）、state/weather_state.json

## Scope

### Included

- docs/DESIGN-watchdog.md（实现事实清单、行为分类、缺陷处置、正式设计、AC）
- REQUIREMENTS.md REQ-011..014 精化为 SHALL 语句（状态保持 PROPOSED）
- STATE.md / .ai/HANDOFF.md / DEVELOPMENT_LOG.md 同步（含任务编号修正：watchdog 主任务为 TASK-003，非此前口头所称 TASK-001）

### Excluded

- 任何业务代码修改（含 B3 等缺陷修复——只登记处置方案）
- 需求状态升级为 ACCEPTED（须用户裁决）
- watchdog 功能提交/回滚（TASK-003 范畴）
- Phase C 类文件结构调整

## Design

纯文档任务：DESIGN 文档按"事实（FACT）→ 分类 → 缺陷 → 设计 → AC"组织；每条事实标注 file:line；每条 Agent 设计标注其 ADR 或"无记录"；每条缺陷给处置方案（M2 内修 / BACKLOG / 接受为已知风险）。

## Acceptance Criteria

- [x] AC-1 DESIGN-watchdog.md 覆盖 watchdog 全部 7 个相关文件，每条事实带 file:line
- [x] AC-2 行为分类四档完整（明确需求 / Agent 设计 / 合理未批准 / 缺陷），无事实遗漏
- [x] AC-3 REQ-011..014 均有 SHALL 语句 + 不变量，且 Status 仍为 PROPOSED
- [x] AC-4 每条缺陷有处置方案与去向（TASK-003 / BACKLOG / 已知风险）
- [x] AC-5 AC 集可客观验证，每条注明验证方式
- [x] AC-6 与 ROADMAP M2 Exit Criteria、BACKLOG 互相引用一致，无职责重叠

## Verification

文档一致性 grep 核查（REQ-011..014 状态、文件引用）；`scripts/verify.py` 回归（L0+L1，确认代码零改动）；交叉引用核对。

## Risks

- 设计文档与未来代码改动漂移——以"批准时冻结"规避：裁决后写入 ADR 并以此版本为基准
- 分类主观性——每条分类必须绑定证据，无法绑定的一律归 UNKNOWN

## Dependencies

- 用户对 REQ-011..014 的最终裁决（本任务的产出物是裁决的输入）
- TASK-003（提交/回滚）依赖本任务产出 + 用户裁决

## Completion Evidence

- Tests: `scripts/verify.py` → PASS，退出码 0（L0+L1 回归守护，业务代码零改动）。
- Commands: `grep -E "^### REQ-01[1-4]" -A1` → 四条全 PROPOSED；`grep -l DESIGN-watchdog` → REQUIREMENTS/ROADMAP/STATE/DEVELOPMENT_LOG/HANDOFF 五处引用全命中；`git diff --stat` 基线逐字一致（6 files, 241+/50-）。
- Git commit: 未提交（用户未授权）。
- Review: AC-1..6 逐条核对通过；无未记录冲突；任务编号修正（TASK-001→TASK-002/003）已同步 STATE/DEVELOPMENT_LOG/HANDOFF。

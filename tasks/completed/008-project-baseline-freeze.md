# TASK-008: Project Baseline Freeze（c556d59）

- ID: TASK-008
- Status: COMPLETED
- Requirement: 用户直接指令（2026-09-30 TASK-008 任务书）
- Created: 2026-10-01

## Objective

冻结 c556d59 版本的真实架构、需求状态与后续路线，产出权威基线快照文档，作为此后一切演进的参照点。**只允许文档变更，业务代码零修改。**

## Why

安全处置闭环（TASK-004..007 + P1-P3）与 watchdog 收敛（d37ed3a）之后，项目首次处于"无未决凭据风险、无未提交业务改动、需求全部定级"的稳定点——是建立冻结基线的最佳时机。

## Evidence

- commit c556d59（"chore: ignore local security artifacts"，HEAD，工作区干净）
- f2358de（安全 checkpoint）、d37ed3a（watchdog checkpoint）
- REQUIREMENTS/ROADMAP/ARCHITECTURE/SECURITY-REVIEW 当前状态

## Scope

### Included

- docs/BASELINE-c556d59.md：架构快照、需求状态快照（REQ-001..015）、后续路线、偏离政策、UNKNOWN 清单
- REQUIREMENTS.md 冻结期状态对齐：REQ-006（CONFLICT→ACCEPTED，冲突经 TASK-007 清理解除）、REQ-015（UNKNOWN→ACCEPTED，U5 确认主路径）
- ROADMAP.md 冻结标注 + M3 范围收敛说明
- STATE/HANDOFF/DEV_LOG 同步

### Excluded

- 业务代码修改（零）
- git tag / git 任何操作（标签化未获授权，仅在设计文档中作为可选项提及）
- 新任务创建；README/WIKI 内容对齐（BL-014）；SEC-T2/T3/R3 实施

## Design

单一冻结文档（commit 哈希命名，不再修改）；细节引用权威活文档（ARCHITECTURE/REQUIREMENTS/ROADMAP/SECURITY-REVIEW），快照只记状态与指针，避免复制漂移（ADP-1.0 §41）。

## Acceptance Criteria

- [x] AC-1 BASELINE 文档存在且锚定 c556d59（HEAD、工作区干净已核实）
- [x] AC-2 架构快照区分活跃/退役链路，与代码事实一致
- [x] AC-3 需求快照覆盖 REQ-001..015 全部状态
- [x] AC-4 后续路线含 M2 尾巴/M3 收敛/M4/PROPOSED 池与偏离政策
- [x] AC-5 零业务代码改动（git status 证实仅文档差异）
- [x] AC-6 与活文档引用一致（REQUIREMENTS/ROADMAP/SECURITY-REVIEW）

## Verification

文档交叉引用 grep；`scripts/verify.py`（L0 回归，零代码改动确认）。

## Risks

- 活文档继续演进导致快照过时——按设计：快照冻结不改，演进由 Task/ADR 记录， readers 以快照 + 后续 ADR 重建现状

## Dependencies

- 无外部依赖（c556d59 已为 HEAD）

## Completion Evidence

- Tests: `scripts/verify.py` 3/3 PASS @ c556d59 工作树（冻结底座验证；L0）。
- Commands: `git log/show --stat c556d59`（HEAD 确认、工作区干净）；grep 交叉引用（BASELINE 被 ROADMAP/STATE/HANDOFF/DEV_LOG 引用；REQ-006/015 状态核对）。
- Git commit: 基线文档已随 eb0886e 入库；**baseline-v1.0 tag 已创建**（TASK-009 只读核验确认，注释 "ADP baseline after watchdog convergence and credential remediation"）。
- Review: **Gate Review Round 1：CONDITIONAL PASS（三项整改已落）→ Final Review 通过（2026-10-01，TASK-009 确认）**。Round 1 整改明细：——
  1. 活跃链路数据流统一为 **weather_monitor（producer）→ stdout（integration boundary）→ Hermes（consumer/scheduler/transport）→ QQ（delivery target）**；BASELINE/ROADMAP/STATE/REQUIREMENTS/ARCHITECTURE/DEV_LOG/HANDOFF/归档 007 全仓反向表述清零。
  2. M3 恢复为 **Runtime Integration** 核心：Hermes integration contract/evidence（BL-016 七项 UNKNOWN 清零）为第一项，退役配置清理与 README runtime 对齐并列；ROADMAP/BASELINE/STATE/BACKLOG/DEV_LOG 同步。
  3. STATE.md 编辑异常证据分级：FACT 仅记录"一次编辑未持久化且磁盘与 HEAD 一致"；**Cause=UNKNOWN**；可能原因（editor reload/external process/checkout-restore/write race/filesystem interaction）仅列示不断言。记录落于 DEV_LOG 与 HANDOFF。
  另：Review 要点保持——①快照"活跃/退役"判定与 U5 一致性；②REQ-006 冲突解除判定；③M3 新退出标准；④git tag 授权（可选）。

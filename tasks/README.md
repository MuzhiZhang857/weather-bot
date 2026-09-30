# tasks/ — 任务协议（ADP-1.0 §12-14）

> 自 **TASK-000**（2026-09-30，采纳 ADP-1.0）起，所有**非平凡代码修改**必须对应一个任务文件。
> 一次性两行小修（改 typo、改一行配置）可以不开任务文件，但要更新 `docs/STATE.md`。
> 命名保持现有体系：`NNN-短横线-slug.md`（任务 ID 写作 TASK-NNN）。历史任务（≤ 001）为 ADP 采纳前产物，**不回溯改写**。

## 任务状态机（六态，ADP-1.0 §14）

```text
PLANNED → IN_PROGRESS → READY_FOR_REVIEW → COMPLETED
异常：IN_PROGRESS → BLOCKED（需外部决策/依赖/修复）；PLANNED → CANCELLED
```

- **COMPLETED** 仅当：验收标准全部有证据满足 + Verification 通过 + 记录已更新（RECORD 完成）。
- **No False Completion**：无法客观验证完成时，Status 停在 `READY_FOR_REVIEW`，不得标 `COMPLETED`。
- 完成的任务文件移入 `tasks/completed/`（文件名不变，Status 改 COMPLETED）。

## 任务文件模板（复制使用）

```markdown
# TASK-NNN: <标题>

- ID: TASK-NNN
- Status: PLANNED | IN_PROGRESS | BLOCKED | READY_FOR_REVIEW | COMPLETED | CANCELLED
- Requirement: REQ-XXX（指向 docs/REQUIREMENTS.md；元任务写"用户直接指令 + 日期"）
- Created: YYYY-MM-DD

## Objective
本任务解决什么问题。

## Why
为什么现在必须做。

## Evidence
- 相关源文件 / 既有测试 / ADR / 用户需求（可追溯清单）

## Scope
### Included
- ...
### Excluded
- ...

## Design
预期实现方式（涉及时才需要：新架构/新模块/数据结构/API/协议/并发/状态/安全）。

## Acceptance Criteria
- [ ] AC-1（每条必须能回答"什么证据证明完成"，ADP-1.0 §23）

## Verification
验证命令与预期（注明目标验证级别 L0-L4）。

## Risks
可能的回归或不确定点。

## Dependencies
其他任务 / 外部服务 / 用户决策。

## Completion Evidence
（完成后填写：Tests / Commands / Git commit / Review）
```

## 使用规则

1. **开工前**建文件，Status=PLANNED。**GATE 1**：Requirement 必须指向 REQUIREMENTS.md 中 ACCEPTED 的条目或用户直接指令；仅有 PROPOSED 需求支撑的功能开发先请求用户裁决。
2. **每次动工后**更新 Status 与 Completion Evidence 草稿——这是跨 Agent 交接的锚点。
3. **发现非阻塞问题** → 记入 `docs/BACKLOG.md`，禁止顺手扩大 Scope（ADP-1.0 §20）。
4. **完成时（RECORD，§27）**：勾验收项 + 填 Completion Evidence（含验证级别声明）+ 移入 `completed/` + 更新 STATE.md 与 .ai/HANDOFF.md。
5. 任务与 `docs/STATE.md` 冲突时，以 STATE.md 为准并修正任务文件。

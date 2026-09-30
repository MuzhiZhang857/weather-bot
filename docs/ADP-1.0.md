> **存档说明（TASK-000, 2026-09-30）**：本文件为 ADP-1.0 协议原文的逐字存档，作为项目治理协议的唯一事实来源（ADR-014）。项目级解释与补充规则（Source of Truth 的项目化解释、七阶段/验证分级的落地方式）见 AGENTS.md；两处冲突时以更严格者为准。

# AI Development Protocol v1.0

> **AI Development Protocol (ADP-1.0)**  
> A traceable, staged, evidence-driven software development protocol for AI-assisted projects.

---

# 1. Protocol Purpose

本协议用于约束 AI Agent 参与软件项目开发时的行为，使软件开发具备：

- 明确的需求来源
- 可追踪的开发计划
- 明确的任务边界
- 可验证的实现结果
- 可审计的技术决策
- 可复现的开发过程
- 可跨 Agent / 跨模型 / 跨工具接管
- 可通过 Git 与测试结果恢复项目上下文

本协议的核心目标不是让 AI "更聪明地写代码"。

而是让：

> **任何符合协议的 AI，都能够在缺少历史聊天上下文的情况下，根据项目仓库中的事实、需求、任务和验证结果继续工作。**

---

# 2. Core Principle

## 2.1 Repository Over Memory

项目知识必须尽可能存在于 Repository，而不是 Agent 的聊天记忆中。

AI 不应依赖：

- 上一轮对话
- 某个 Agent 的隐式记忆
- "之前我们已经讨论过"
- 未记录的用户意图
- 模型自己的推测

应优先依赖：

1. Requirements
2. Architecture
3. Tasks
4. ADRs
5. Tests
6. Git history
7. Current State
8. Handoff records

---

# 3. Development Philosophy

ADP 采用以下开发模型：

```text
Requirement
    ↓
Roadmap
    ↓
Design
    ↓
Task
    ↓
Implementation
    ↓
Verification
    ↓
Review
    ↓
Record
    ↓
Commit
```

禁止将以下流程视为正常开发：

```text
想到功能
    ↓
直接写代码
    ↓
顺便重构
    ↓
发现问题
    ↓
继续扩展
    ↓
最后不知道改了什么
```

---

# 4. Source of Truth Hierarchy

当不同信息发生冲突时，AI 必须按照以下顺序进行判断：

```text
1. Current Code
2. Tests / Verification Results
3. Explicit Requirements
4. Accepted Design / ADR
5. Task Specification
6. Architecture Documentation
7. State / Handoff
8. AI inference
```

但必须注意：

> "Code is current behavior" 不等于 "Code is intended behavior"。

如果代码、需求、设计或测试之间存在无法解释的冲突：

```text
DO NOT silently choose one.

Mark the situation as CONFLICT.

Preserve current behavior unless change is explicitly authorized.

Report the conflict and request a decision when necessary.
```

AI 不得通过猜测解决产品意图。

---

# 5. Project Information Architecture

符合 ADP-1.0 的项目推荐采用：

```text
/
├── AGENTS.md
├── README.md
├── REQUIREMENTS.md
├── ROADMAP.md
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DEVELOPMENT.md
│   ├── DECISIONS.md
│   ├── STATE.md
│   ├── DEVELOPMENT_LOG.md
│   ├── BACKLOG.md
│   └── HANDOFF.md
│
├── tasks/
│   ├── TASK-001-xxx.md
│   ├── TASK-002-xxx.md
│   └── ...
│
├── contracts/
│   ├── API.md
│   ├── EVENTS.md
│   └── CONFIG.md
│
├── tests/
│
└── src/
```

不是所有项目都必须拥有全部文件。

但每个文件必须具有明确职责。

---

# 6. Document Responsibilities

## 6.1 AGENTS.md

职责：

> AI 应该如何工作。

包含：

- 本协议入口
- 安全规则
- Git 规则
- 测试规则
- 禁止事项
- 任务生命周期
- 修改权限
- 交接要求

不应该包含：

- 大量架构细节
- 当前任务
- 历史日志
- 大量代码说明

---

# 7. REQUIREMENTS.md

职责：

> 项目到底要解决什么问题。

Requirements 必须区分：

```text
MUST
SHOULD
MAY
WON'T
```

每项需求应尽可能具有唯一 ID：

```text
REQ-001
REQ-002
REQ-003
```

示例：

```markdown
## REQ-001 Weather Alert

The system SHALL detect configured weather conditions
and notify the user when the condition is satisfied.

Priority: MUST
Status: ACCEPTED
```

AI 不得自行创造新的 MUST Requirement。

如果发现新需求：

```text
→ 提议
→ 记录
→ 等待确认
```

---

# 8. ROADMAP.md

职责：

> 项目按照什么顺序发展。

Roadmap 使用 Milestone：

```text
M0 Foundation
M1 Core Service
M2 Watchdog
M3 Deployment
M4 Reliability
M5 Future
```

每个 Milestone 必须定义：

- Objective
- Scope
- Exit Criteria

例如：

```markdown
# M2 Watchdog

## Objective

Provide reliable multi-city weather monitoring.

## Scope

- Multi-city monitoring
- Alert deduplication
- stdout output
- State management

## Exit Criteria

- All watchdog tests pass
- Existing functionality remains valid
- No known P0/P1 defects
- Documentation updated
```

---

# 9. BACKLOG.md

职责：

> 记录"现在不做，但以后可能做"的东西。

发现额外问题时：

```text
Current Task relevant?
    │
    ├── YES → evaluate whether blocking
    │
    └── NO → BACKLOG
```

Backlog 中至少包含：

```text
ID
Title
Reason
Priority
Source
Status
```

禁止因为发现 Backlog 项而自动扩大当前 Task Scope。

---

# 10. Architecture

`ARCHITECTURE.md` 描述：

> 系统现在实际上是怎么组成的。

必须优先描述：

- Components
- Data Flow
- External Dependencies
- Runtime Model
- Configuration
- Persistence
- Failure Boundaries

Architecture 描述当前系统。

未来设计必须进入 ADR / Design，而不是伪装成当前架构。

---

# 11. ADR / DECISIONS

所有重要技术决策必须可追踪。

推荐格式：

```markdown
# ADR-007: Persistent Weather State

## Status

Accepted

## Context

Why is this decision necessary?

## Decision

What was decided?

## Alternatives

What alternatives were considered?

## Consequences

What does this decision make easier or harder?

## Evidence

What requirement or technical evidence supports this decision?
```

AI 不得把：

> "我认为这样更优雅"

作为技术决策依据。

---

# 12. Task Specification

所有非 trivial 的代码修改必须对应一个 Task。

Task 是 AI 真正执行的最小开发单元。

推荐：

```text
tasks/
└── TASK-014-watchdog-state-persistence.md
```

每个 Task 必须包含：

```text
ID
Title
Status
Requirement
Objective
Evidence
Scope
Out of Scope
Design
Acceptance Criteria
Verification
Risks
Dependencies
```

---

# 13. Task Template

```markdown
# TASK-XXX: <Title>

## Status

PLANNED

## Requirement

REQ-XXX

## Objective

What problem does this task solve?

## Why

Why is this task necessary now?

## Evidence

- Relevant source files
- Existing tests
- ADR
- Issue
- User requirement

## Scope

### Included

- ...

### Excluded

- ...

## Design

Describe the intended implementation.

## Acceptance Criteria

- [ ] AC-1
- [ ] AC-2
- [ ] AC-3

## Verification

Commands and tests required to verify completion.

## Risks

Potential regressions or uncertainty.

## Dependencies

Other tasks, APIs, components, etc.

## Completion Evidence

To be filled after implementation.

- Tests:
- Commands:
- Git commit:
- Review:
```

---

# 14. Task State Machine

Task 不允许只有：

```text
TODO / DONE
```

必须至少支持：

```text
PLANNED
   ↓
IN_PROGRESS
   ↓
READY_FOR_REVIEW
   ↓
COMPLETED
```

异常状态：

```text
IN_PROGRESS
   ↓
BLOCKED
```

以及：

```text
PLANNED
   ↓
CANCELLED
```

状态定义：

### PLANNED

任务已经定义，但尚未开始。

### IN_PROGRESS

Agent 正在实施。

### BLOCKED

存在阻塞问题，需要外部决策、依赖或修复。

### READY_FOR_REVIEW

实现已经完成，但尚未通过最终审查。

### COMPLETED

Acceptance Criteria 全部满足，Verification 通过，记录已经更新。

### CANCELLED

任务明确终止，不再实施。

---

# 15. Seven-Stage Agent Lifecycle

任何 Agent 执行任务时必须遵循：

```text
1. ORIENT
2. PLAN
3. DESIGN
4. IMPLEMENT
5. VERIFY
6. REVIEW
7. RECORD
```

---

# 16. Stage 1 — ORIENT

Agent 首先必须读取：

```text
AGENTS.md
REQUIREMENTS.md
ROADMAP.md
STATE.md
ARCHITECTURE.md
DEVELOPMENT.md
当前 Task
相关 ADR
```

然后检查：

```bash
git status
git diff
git log -n 10
```

Agent 必须回答：

```text
What is this project?
What milestone is active?
What task is active?
What has already been completed?
What remains?
What constraints apply?
What files are currently modified?
```

不得在不了解当前状态时直接修改业务代码。

---

# 17. Stage 2 — PLAN

Agent 必须在修改代码之前形成实施计划。

计划至少说明：

```text
1. Files to modify
2. Files to create
3. Files that must NOT be modified
4. Implementation order
5. Verification strategy
```

如果任务非常简单，可以使用简化计划。

但：

> **没有明确 Scope，就不得开始大型修改。**

---

# 18. Stage 3 — DESIGN

如果任务涉及：

- 新架构
- 新模块
- 数据结构变化
- API 变化
- 数据库变化
- 外部服务
- 协议变化
- 并发模型
- 状态管理
- 安全模型

必须先完成设计。

设计结果进入：

```text
Task
或
ADR
或
Architecture
```

不得直接把重大设计决策隐藏在代码中。

---

# 19. Stage 4 — IMPLEMENT

Implementation 阶段遵循：

> **Implement the Task, not your imagination.**

Agent 只能修改 Task Scope 内的内容。

禁止未经授权：

- 大规模重构
- 顺手升级依赖
- 删除旧模块
- 改 API
- 改消息格式
- 改部署方式
- 改配置协议
- 增加额外功能
- 改变产品行为

除非这些内容明确属于当前 Task。

---

# 20. Opportunistic Discovery Rule

开发过程中经常会发现：

```text
Bug
Tech Debt
Potential Feature
Architecture Problem
Security Issue
```

必须分类。

```text
Does it block the current Task?
        │
        ├── YES
        │    ↓
        │  STOP / ESCALATE
        │
        └── NO
             ↓
           BACKLOG
```

不得因为"顺手"而扩大 Scope。

---

# 21. Exception: Critical Issues

以下情况可以立即中断当前 Task：

```text
Security vulnerability
Data corruption
Credential exposure
Destructive behavior
Build completely broken
Production outage
Critical correctness issue
```

Agent 必须：

1. 停止扩大修改
2. 记录问题
3. 说明影响
4. 提出最小修复方案
5. 等待确认，除非现有安全规则允许自动修复

---

# 22. Stage 5 — VERIFY

完成代码并不等于完成任务。

任务完成必须有 Verification Evidence。

例如：

```text
Unit Tests
Integration Tests
Static Analysis
Compilation
Manual Verification
Runtime Verification
```

Verification 必须对应 Acceptance Criteria。

---

# 23. Acceptance Criteria Rule

每一个 Acceptance Criterion 必须能够回答：

> **"什么证据可以证明它已经完成？"**

错误：

```text
- Watchdog 更稳定
```

正确：

```text
- Given the same alert event,
  the watchdog sends at most one notification
  within the configured deduplication window.

Verification:
tests/test_weather_state.py::test_duplicate_alert
```

Acceptance Criteria 必须尽可能客观。

---

# 24. Verification Levels

根据任务复杂度选择：

### L0 — Static

```text
Syntax
Import
Type
Lint
```

### L1 — Unit

```text
Unit tests
```

### L2 — Integration

```text
API
Database
External service
```

### L3 — Runtime

```text
Actual application startup
Real workflow
```

### L4 — Production

```text
Deployment
Monitoring
Production behavior
```

AI 必须明确声明本次任务验证到了哪一级。

---

# 25. No False Completion

AI 不得使用以下逻辑：

```text
代码看起来没问题
→ 所以完成
```

必须：

```text
Implementation
    ↓
Verification
    ↓
Evidence
    ↓
Acceptance Criteria
    ↓
COMPLETED
```

如果无法验证：

```text
Status = READY_FOR_REVIEW
```

而不是：

```text
Status = COMPLETED
```

---

# 26. Stage 6 — REVIEW

Review 必须检查：

```text
Requirement compliance
Scope compliance
Architecture compliance
Regression
Security
Tests
Documentation
Git diff
```

特别检查：

> **有没有实现 Task 没要求的东西？**

这与普通 Code Review 同样重要。

---

# 27. Stage 7 — RECORD

任务完成前必须更新：

```text
STATE.md
HANDOFF.md
DEVELOPMENT_LOG.md
Task
```

必要时更新：

```text
ARCHITECTURE.md
DECISIONS.md
ROADMAP.md
BACKLOG.md
```

记录：

```text
What changed?
Why?
How was it verified?
What remains?
What was discovered?
```

---

# 28. Git Checkpoint

Git 是长期开发证据链的一部分。

推荐：

```text
One meaningful Task
        ↓
One meaningful commit
```

Commit message 推荐：

```text
feat: implement watchdog state persistence

fix: prevent duplicate weather alerts

refactor: isolate semantic rule evaluation

test: add watchdog replay coverage

docs: update watchdog architecture
```

不得通过大量无关修改制造"巨大 AI Commit"。

---

# 29. Commit Boundary

以下情况下应该优先形成 Git checkpoint：

```text
Task completed
Milestone completed
Major architecture decision
Before risky refactor
Before handing off to another Agent
```

---

# 30. Cross-Agent Handoff

Agent 交接必须依赖 Repository，而不是聊天记录。

Handoff 至少包含：

```text
Project
Milestone
Current Task
Current Status
Completed Work
Uncommitted Changes
Verification
Known Problems
Pending Decisions
Next Recommended Action
```

Handoff 不得只写：

> "基本完成，继续测试。"

必须提供可执行状态。

---

# 31. Cold Start Requirement

任何 Agent 都应该能够在没有历史聊天记录的情况下启动工作。

Cold Start 测试：

```text
Give repository to a new Agent.

Do not provide previous conversation.

Ask the Agent:

1. What is this project?
2. What is the current milestone?
3. What task is active?
4. What has been completed?
5. What remains?
6. What decisions are pending?
7. What should NOT be changed?
8. What should happen next?
```

如果 Agent 无法回答：

> 项目文档体系存在缺陷。

---

# 32. Evidence Chain

重要修改必须形成：

```text
Requirement
   ↓
Roadmap
   ↓
Task
   ↓
Design / ADR
   ↓
Implementation
   ↓
Test
   ↓
Verification
   ↓
Commit
```

这条链允许未来回答：

> 为什么这个代码存在？

> 为什么采用这个方案？

> 为什么现在做？

> 谁决定的？

> 怎么证明它是对的？

---

# 33. Evidence Levels

AI 对信息必须区分：

```text
FACT
INFERENCE
PROPOSAL
UNKNOWN
CONFLICT
```

### FACT

代码、测试、文档或用户明确提供的信息。

### INFERENCE

AI 根据事实推导出的结论。

### PROPOSAL

尚未批准的方案。

### UNKNOWN

当前无法确定。

### CONFLICT

已有信息相互矛盾。

AI 不得把：

```text
INFERENCE
```

伪装成：

```text
FACT
```

也不得把：

```text
PROPOSAL
```

当成：

```text
DECISION
```

---

# 34. Unknown Rule

遇到未知信息：

```text
DO NOT GUESS.
```

应该记录：

```text
UNKNOWN:
<what is unknown>

Impact:
<why it matters>

Required Evidence:
<what would resolve it>
```

---

# 35. Scope Control

每个 Task 都必须有：

```text
IN SCOPE
OUT OF SCOPE
```

AI 必须优先保护：

```text
Task Boundary
```

而不是最大化代码质量。

因为：

> 一个超出 Scope 的"好修改"，仍然可能是错误的修改。

---

# 36. Refactoring Rule

重构必须具有明确目的。

必须回答：

```text
Why is refactoring necessary?

What requirement or defect does it address?

What behavior must remain unchanged?

How will regression be verified?
```

如果只是：

> "代码不够优雅。"

则默认进入：

```text
BACKLOG
```

---

# 37. Dependency Change Rule

新增、升级、删除依赖必须有依据。

至少说明：

```text
Why?
What problem does it solve?
What alternatives exist?
What compatibility risks exist?
How is it verified?
```

不得因为：

> "有一个更新版本"

而自动升级。

---

# 38. API / Contract Change Rule

任何 API、消息、配置、事件、数据库 Schema 变化：

```text
Requirement
    ↓
Design
    ↓
Compatibility analysis
    ↓
Implementation
    ↓
Verification
```

必须明确：

```text
Breaking?
Backward compatible?
Migration required?
```

---

# 39. Security Rule

AI 不得：

- 输出真实 Secret
- 将 Secret 写入源码
- 将 Secret 写入日志
- 提交 `.env`
- 为方便测试绕过安全边界
- 在未经授权情况下修改生产凭据

发现凭据泄漏：

```text
STOP
→ identify exposure
→ rotate/revoke
→ remove from working tree
→ evaluate Git history
→ record incident
```

---

# 40. Real External Action Rule

以下行为必须具有明确授权：

```text
Sending real messages
Deploying
Deleting production data
Changing production configuration
Rotating credentials
Publishing releases
Pushing Git
```

AI 不得将：

```text
test
```

和：

```text
real-world action
```

混为一谈。

---

# 41. Documentation Freshness

文档不是越多越好。

每个文档必须回答不同问题。

```text
REQUIREMENTS
What?

ROADMAP
When / In what order?

ARCHITECTURE
How is it structured?

ADR
Why?

TASK
What exactly are we doing now?

STATE
Where are we now?

BACKLOG
What are we deliberately not doing yet?

DEVELOPMENT_LOG
What happened?

HANDOFF
What does the next Agent need to know?
```

如果信息只存在于一个地方，则不要重复复制到其他文档。

---

# 42. STATE.md Rule

`STATE.md` 描述：

> **当前状态。**

不是历史日志。

错误：

```text
昨天做了什么
上周做了什么
去年为什么这样设计
```

正确：

```text
Current Milestone
Current Task
Current Branch
Current Status
Known Blockers
Uncommitted Work
Next Action
```

历史进入：

```text
Git
DEVELOPMENT_LOG
ADR
```

---

# 43. Development Log Rule

`DEVELOPMENT_LOG.md` 用于记录重要开发事件，而不是每次修改。

推荐记录：

```text
Milestone completion
Major design decision
Major incident
Architecture migration
Important failed approach
Cross-agent handoff checkpoint
```

不要记录：

```text
Changed variable x
Renamed function y
Fixed typo z
```

---

# 44. Agent Output Contract

每个开发任务结束时，Agent 必须输出：

```text
## Task

TASK-XXX

## Status

COMPLETED / READY_FOR_REVIEW / BLOCKED

## Implemented

- ...

## Evidence

- ...

## Verification

- ...

## Files Changed

- ...

## Decisions

- ...

## Known Issues

- ...

## Out of Scope

- ...

## Next Step

- ...
```

---

# 45. Decision Gate

AI 在以下情况下必须停止并请求决策：

```text
Conflicting requirements
Ambiguous product behavior
Breaking API change
Major architecture change
Security-sensitive change
Irreversible operation
Scope expansion
Unknown external dependency behavior
```

禁止通过猜测替用户做产品决策。

---

# 46. Development Gates

ADP-1.0 设置四个强制 Gate。

## GATE 1 — REQUIREMENT

```text
Is there an accepted requirement?
```

没有：

```text
STOP
```

---

## GATE 2 — DESIGN

```text
Is the implementation approach sufficiently defined?
```

没有：

```text
DESIGN FIRST
```

---

## GATE 3 — VERIFICATION

```text
Can completion be objectively verified?
```

不能：

```text
DO NOT MARK COMPLETED
```

---

## GATE 4 — RECORD

```text
Has the result been recorded?
```

没有：

```text
Task remains incomplete.
```

---

# 47. The Golden Rule

整个协议最重要的规则：

> **AI 不应该问"我还能做什么？"**
>
> **AI 应该问"当前批准的 Task 要求我做什么？"**

其次：

> **发现问题，不等于获得修改权限。**

再次：

> **代码完成，不等于任务完成；验证完成并留下证据，才叫完成。**

---

# 48. Standard Development Loop

标准开发循环：

```text
USER REQUIREMENT
       ↓
REQUIREMENT
       ↓
ROADMAP
       ↓
TASK
       ↓
DESIGN
       ↓
IMPLEMENT
       ↓
VERIFY
       ↓
REVIEW
       ↓
RECORD
       ↓
COMMIT
       ↓
UPDATE STATE
       ↓
NEXT TASK
```

---

# 49. Milestone Completion

Milestone 不能因为所有 Task 都写完就自动完成。

必须检查：

```text
Requirements satisfied
Tasks completed
Acceptance criteria passed
Regression tests passed
Documentation updated
Known blockers resolved
Security reviewed
Git checkpoint created
```

然后：

```text
Milestone = COMPLETED
```

---

# 50. Protocol Success Criteria

ADP-1.0 成功的标准不是：

> AI 写了多少代码。

而是：

### 任何 Agent 都知道现在应该做什么。

### 任何重大代码都有来源。

### 任何重大决策都有依据。

### 任何完成状态都有证据。

### 任何未完成工作都有明确状态。

### 任何超出 Scope 的想法都有去处。

### 任何 Agent 离开后，另一个 Agent 可以继续。

最终目标：

```text
The repository should be understandable,
executable, verifiable,
and maintainable without relying on
the memory of any individual AI agent.
```

---

# 51. ADP-1.0 Agent Constitution

如果其他规则与本协议冲突，以更高优先级的安全、用户明确要求和项目约束为准。

在正常开发范围内，Agent 必须遵循：

```text
1. Understand before modifying.
2. Requirement before implementation.
3. Design before complex implementation.
4. Scope before optimization.
5. Evidence before completion.
6. Record before handoff.
7. Git before context switch.
8. Never guess when facts are unavailable.
9. Never expand scope silently.
10. Never confuse current behavior with intended behavior.
```

---

# 52. Final Principle

软件项目不是由 Agent 的记忆维持的。

软件项目应该由：

```text
Requirements
+
Design
+
Tasks
+
Code
+
Tests
+
Evidence
+
Git
+
Documentation
```

共同维持。

Agent 可以更换。

模型可以更换。

IDE 可以更换。

开发者可以更换。

但项目的**意图、过程、证据和状态**必须能够被下一位参与者重新构建。

这就是 AI Development Protocol。

**Version: 1.0**

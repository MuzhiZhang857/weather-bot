# TASK-006: WeCom Credential Rotation Preparation（仅设计，不执行）

- ID: TASK-006
- Status: COMPLETED
- Requirement: 用户直接指令（2026-09-30 TASK-006 任务书）；细化 TASK-005 SEC-R1 的 WeCom SECRET 部分
- Created: 2026-09-30
- Completed: 2026-09-30

## Objective

在执行 SEC-R1 轮换前，完成 WeCom SECRET 的使用方盘点、部署面确认与轮换步骤设计（Before / Rotation / After 含验证与回滚）。**只产出 docs/SECURITY-CREDENTIAL-ROTATION-PLAN.md。**

## Why

TASK-005 已确认泄露值 = 在用值（活凭据公开）；SEC-R1 授权前必须先回答"谁在用、在哪配、轮换会打断谁、怎么验证与回滚"。

## Evidence

- 消费方取证（值已掩码）：services/push_service.py:61/151、qywx_websocket.py:45/176、wechat_weather.py:8/105/134；weather_monitor.py 零依赖
- 部署面：railway.json、render.yaml（在库）；.env（本地活跃）；Hermes UNKNOWN（BL-016）
- TASK-005：泄露值 = 在用值（SAME）；QYWX_WEBHOOK_KEY 与 SECRET 同串

## Scope

### Included

- docs/SECURITY-CREDENTIAL-ROTATION-PLAN.md：SECRET 使用方清单（路径/变量名/环境来源/迁移需求，值零记录）、部署面确认（Railway/Render/本地/Hermes）、轮换三段步骤（Before/Rotation/After）、AC（全 PROPOSED）

### Excluded

- 执行轮换、修改 `.env`/代码/平台配置、真实消息发送
- HEFENG 旧 key 处置与 CHAT_ID 讨论（TASK-005 SEC-R1 已覆盖，本文只做引用）
- 创建后续任务

## Design

纯文档。消费方清单按"代码消费点 + 环境来源 + 是否需迁移"组织；轮换步骤按 Before/Rotation/After 三段；回滚按"轮换不可逆"前提设计。

## Acceptance Criteria

- [x] AC-1 使用方清单完整（全部 4 处代码消费点 + watchdog 零依赖 + Hermes UNKNOWN），值零记录
- [x] AC-2 部署面四方状态明确（Railway/Render/本地/Hermes），UNKNOWN 项注明解决动作
- [x] AC-3 Before/Rotation/After 步骤可操作，含验证与回滚
- [x] AC-4 AC 全部 PROPOSED 且可验证
- [x] AC-5 与 TASK-005 SEC-R1、SECURITY-REVIEW.md 引用一致

## Verification

grep 消费点复核（值掩码）；文档交叉引用核查；`scripts/verify.py` 回归（L0）。

## Risks

- 平台账号侧状态（Railway/Render 变量、Hermes）离线不可知 → 全部以 checklist 形式留给用户执行前确认

## Dependencies

- 用户批准本计划后才进入实际轮换（轮换本身为用户平台操作）
- U5 使用方盘点收尾、BL-016（Hermes）为 Before 段的确认项

## Completion Evidence

- Tests: 本任务纯文档；回归守护 `scripts/verify.py` 3/3 PASS（TASK-004 后未变）。
- Commands: 消费方取证 `grep -rn SECRET`（值掩码输出）→ 4 处消费点 + watchdog 零依赖；.env 键存在性计数；wechat_weather webhook 用法（key=<masked>）。
- Git commit: 未提交（无授权）。
- Review: **PASS（附两项修正，已全部落文档）**——
  1. **失效语义 FACT→UNKNOWN**："重置后旧值立即失效/无并存窗口"降级为规划假设；ROTATION-PLAN §3.2-5 新增执行期双重验证要求（新值生效 + 旧值失效，或明确记录"无法验证"）；§3.1 窗口、§3.3 After、§3.4 回滚同步改为 UNKNOWN 措辞；
  2. **独立凭据对象建模**：QYWX_WEBHOOK_KEY 与 AI Bot SECRET 建模为两个独立对象——历史字符串相同不得推断轮换互涉；legacy webhook 使用状态 UNKNOWN 待用户确认，仍使用→独立处置其 webhook key，已废弃→静态清理任务处理。联动修正 CREDENTIAL-REMEDIATION SEC-R1 与 SECURITY-REVIEW SEC-01。

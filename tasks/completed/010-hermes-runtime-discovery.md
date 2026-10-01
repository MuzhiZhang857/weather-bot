# TASK-010: BL-016 Hermes Runtime Discovery（只读取证）

- ID: TASK-010
- Status: COMPLETED
- Requirement: 用户直接指令（2026-10-01 TASK-010 授权）；M3 Runtime Integration 核心项 BL-016
- Created: 2026-10-01
- Completed: 2026-10-01

## Objective

以只读方式从仓库内可观测证据（logs/ 轮转日志、state 文件、代码契约）对 BL-016 七项 UNKNOWN 逐项取证，将"观测类"未知推进到有证据结论，明确"消费侧"未知仍需 Hermes 侧信息的清单。**不改代码、不运行被测对象、不做真实推送。**

## Why

M3 Runtime Integration 的第一步是取得 Hermes 集成证据；watchdog 日志是仓库内唯一的运行面观测源。

## Evidence

- `logs/weather_bot.log` 及轮转备份（RotatingFileHandler 10MB×5）
- `state/weather_state.json`（当前活动态快照）
- `weather_monitor.py` 代码契约（exit/stdout/日志行为）

## Scope

### Included

- docs/HERMES-RUNTIME-EVIDENCE.md：七项 UNKNOWN 逐项证据分级（OBSERVED / INFERENCE / STILL-UNKNOWN）、运行统计、边界契约确认、剩余缺口清单
- BACKLOG BL-016 / STATE / HANDOFF / DEV_LOG 同步

### Excluded

- 修改任何代码/配置；运行 weather_monitor 或任何被测对象
- 读取/展示任何凭据值；Hermes 侧配置的直接访问（仓库外，不可达）
- 关闭 BL-016（若消费侧语义仍缺证据，保持 Open 并注明已解决子项）

## Design

以"weather_monitor 开始运行/执行完成/运行异常"三类日志行为运行边界，跨全部轮转文件重建运行时间线；以时间差计算观测频率与重叠；以关键词计数统计去重/命中/降级/异常事件。所有输出为统计量与时间戳，不含敏感内容。

## Acceptance Criteria

- [x] AC-1 运行时间线覆盖全部可用日志轮转文件
- [x] AC-2 七项 UNKNOWN 逐项给出证据状态（OBSERVED/INFERENCE/STILL-UNKNOWN）
- [x] AC-3 观测频率、重叠执行、失败/异常有量化结论
- [x] AC-4 消费侧语义（stdout/空输出/exit code 的 Hermes 处理）明确标注 STILL-UNKNOWN 及所需证据
- [x] AC-5 全程只读（无文件写入日志目录、无代码改动）
- [x] AC-6 BL-016 状态更新反映"部分证据已取得"

## Verification

统计脚本输出复核；证据文档与日志原始行抽查对照；`git status` 确认 logs/ 无新写入。

## Risks

- 日志轮转可能丢失早期运行（观测窗口有限）——结论限定于"观测窗口内"
- 日志由 main.py 与 weather_monitor 共用——需按 logger 名称区分入口

## Dependencies

- 无；消费侧剩余缺口需用户/Hermes 侧信息（不在本任务）

## Completion Evidence

- Tests: 只读取证任务；`scripts/verify.py` 3/3 PASS（exit 0，确认零代码改动）。
- Commands: 日志 forensic 三批（运行边界/时间线重建、事件关键词统计、倍增窗口分诊判别）；`git status` 确认 logs/ 零写入；交叉引用 grep（HERMES-RUNTIME-EVIDENCE 被 BACKLOG/STATE/HANDOFF 引用）。
- Git commit: checkpoint 已授权（"docs: capture Hermes runtime evidence baseline"）并 push origin main（hash 见 git log）。
- Review: **Gate Review Round 1：CONDITIONAL PASS（三项整改 + G3 输入已落）→ Final Review 通过（2026-10-01，TASK-010 状态同步确认）**。整改明细：——
  1. "未产生同 tag 重复投递"修正为"未观察到同 tag 被 weather_monitor 重复 emit；Hermes→QQ 投递是否重复 UNKNOWN"（producer 幂等不外推投递层）。
  2. re-alert ≈4.8/日降级为行为观测，**Cause=UNKNOWN**（D4 为候选解释之一，未经证实）。
  3. 倍增窗口保持 UNKNOWN：**G3 用户已排除手动触发**；剩余假设（Agent/工具触发、多实例并发、重复 handler、多 writer、其他）仅列示不断言。
  保留项：544 启动/26 活跃日/03–09 死区/9–10 月停运窗口/exit 0·1 monitor 侧证据均不变。
  原 Review 要点存档：①频率结论符合性；②倍增触发源；③G1/G2 补齐方式。

# DEVELOPMENT_LOG — 重要开发事件（ADP-1.0 §43）

> 职责：记录里程碑完成、重大决策、重大事故、重要失败尝试、跨 Agent 交接检查点。
> **不记录**普通代码操作流水账（那是 git log 的职责）。建立于 TASK-000（2026-09-30）；此前事件按仓库证据回填。

## 2026-09-30 · 凭据暴露处置设计（TASK-005，READY_FOR_REVIEW）

- 用户指令针对 SEC-01/07/08（Public 仓库凭据暴露）产出处置设计；零代码改动、零凭据值输出。
- 产出 `docs/SECURITY-CREDENTIAL-REMEDIATION.md`：资产清单 A1-A8、四维影响分析、SEC-R1（轮换）/R2（清理）/R3（历史重写评估：默认 Skip）/R4（环境迁移）、风险与回滚、AC 全 PROPOSED。
- **关键事实（布尔取证，零值输出）**：SECRET/BOT_ID/SCHEDULE_CHAT_ID 泄露值 = .env 在用值（SAME）→ **活凭据对互联网公开**；HEFENG 泄露为旧值（DIFFER，在用 key 未暴露）；QYWX_WEBHOOK_KEY 与 SECRET 同串（别名暴露）；LLM_API_KEY 为 7 字符占位符——无真实暴露（附带发现：LLM 文案当前实际不可用，一直走降级模板）。
- 修复设计要点：轮换（R1）先于清理（R2）；历史重写（R3）默认 Skip（轮换已使旧值失效，重写破坏性高）；SCHEDULE_CHAT_ID 不可轮换（标识符），单独泄露依赖凭据配对才可利用。

## 2026-09-30 · 凭据退役与静态暴露清理（TASK-007，READY_FOR_REVIEW）

- **U5 运行面决议（用户）**：Railway/Render/WeCom AI Bot/legacy webhook 均不再使用；Hermes 活跃用于 **QQ 推送**（BL-016 部分决议）。处置策略随之变更：从"轮换 + 迁移"改为"废弃凭据失效 + 静态暴露清理"。
- **静态清理已执行（Agent 侧）**：README 5 处（4 表行 + 1 日志示例）、WIKI 4 处占位符化；qywx_websocket.py 4 处 getenv 默认值清空；wechat_weather.py 2 处字面量改 os.getenv（补 import os）。**HEAD 工作树对全部在用/旧凭据值 0 命中**；verify.py 3/3 PASS（legacy 仍可编译）。
- **平台失效 PENDING（用户 P1-P3）**：WeCom 停用 AI Bot / 处置 legacy webhook 对象 / 和风禁用旧 key——确认后 SEC-01/07/08 方可降级为"历史暴露，凭据已失效"。
- 附带：README.md:228 的会话 ID 日志示例（非表格行）在复扫中发现并一并清除——教训：**凭据扫描不能只盯表格结构，需以值本身做全文布尔扫描**。
- **Finalization（2026-09-30）**：P1-P3 平台失效完成（用户确认）→ SEC-01/07/08 最终状态 = Historical Exposure CONFIRMED / Credential RETIRED-REVOKED / Compromise UNKNOWN（不做任何第三方访问断言）；SEC-R3 维持 PROPOSED/Skip；Hermes QQ 推送链路未受影响（用户确认）。TASK-007 COMPLETED。

## 2026-09-30 · WeCom SECRET 轮换准备（TASK-006，READY_FOR_REVIEW）

- 用户指令产出轮换前准备计划；零代码改动、零值输出、未执行轮换。
- 产出 `docs/SECURITY-CREDENTIAL-ROTATION-PLAN.md`：SECRET 消费方清单（C1 push_service 全模式 / C2 legacy getenv 泄露默认值 / C3 wechat_weather webhook 字面量——AI Bot SECRET 与群机器人 webhook key 是不同对象，legacy 用法有效性 UNKNOWN / C4 watchdog 零依赖 / C5 Hermes UNKNOWN）、部署面四方（Railway/Render UNKNOWN 需用户确认、本地 CONFIRMED、Hermes BL-016）、Before/Rotation/After 三段步骤与不可逆回滚设计。
- 关键结论：轮换强制性迁移面 = C1（本地 .env + 活跃云平台）；watchdog 当前活跃路径零中断；C3 legacy webhook 用法是否曾成功投递 UNKNOWN。
- **Review（2026-09-30）：PASS，附两项修正，已落文档**：①"重置后旧值立即失效"由 FACT 降级为 UNKNOWN——失效语义缺平台证据，执行期必须验证新值生效与旧值失效（或记录无法验证）；②QYWX_WEBHOOK_KEY 与 AI Bot SECRET 建模为独立凭据对象——同串不构成轮换互涉依据，legacy webhook 使用状态 UNKNOWN 待用户确认。联动修正 CREDENTIAL-REMEDIATION SEC-R1 与 SECURITY-REVIEW SEC-01。教训入档：**平台行为（失效语义/重试/并存）在取得运行证据前一律 UNKNOWN，不得写成 FACT**。

## 2026-09-30 · 安全基线与修复设计（TASK-004，READY_FOR_REVIEW）

- 用户指令对 BL-018 全部 findings 及相关安全面做事实确认、风险建模与修复设计；零代码改动。
- 产出 `docs/SECURITY-REVIEW.md`：攻击面总览、S-01..S-10 登记册（分类 TP×6 / FP×4 / 历史×3）、修复设计 SEC-T1（凭据轮换与静态清理）/ SEC-T2（response_url SSRF 加固）/ SEC-T3（WS 证书校验恢复），全部 PROPOSED。
- **核心结论**：全项目最可信攻击链 = SEC-06（WS 证书校验禁用，MITM 可截订阅凭据）→ SEC-03（response_url 无校验，盲 SSRF）。
- 取证全程凭据零打印（仅行号/计数/布尔）；发现并记录 U1-U6 六项 UNKNOWN（仓库可见性最关键）。
- BACKLOG 同步：BL-012 关联 SEC-06、BL-018 关联定级、新增 BL-019。

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

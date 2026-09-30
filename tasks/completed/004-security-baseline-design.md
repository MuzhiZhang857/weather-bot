# TASK-004: Security Baseline & Remediation Design

- ID: TASK-004
- Status: COMPLETED
- Requirement: 用户直接指令（2026-09-30 TASK-004 任务书）；承接 BL-018（Mimosa L3 findings）与 STATE §6-3（凭据决策）
- Created: 2026-09-30
- Completed: 2026-10-01（TASK-009 状态同步）

## Objective

对 BL-018 全部 findings 及相关安全面做事实确认、风险建模与修复设计，产出正式安全设计文档。**只做分析与设计，零业务代码修改。**

## Why

TASK-003 checkpoint 经用户裁决"带已知发现提交"（BL-018），但发现从未被系统定级；没有正式的安全基线文档，后续修复任务无需求与验收依据。

## Evidence

- BL-018 五项 Mimosa L3 findings；services/push_service.py:128、qywx_websocket.py:291（CERT_NONE）
- main.py:100-116（response_url 处理）；services/llm_service.py:17/148（base_url）
- wechat_weather.py:4-8、qywx_websocket.py:44-53、README.md:136-159、WIKI.md:274-291（凭据暴露面，值未读取）
- git 历史（77c705d 起三文件在库）；origin = github.com/MuzhiZhang857/weather-bot

## Scope

### Included

- `docs/SECURITY-REVIEW.md`：攻击面总览、S-01..S-10 finding 登记册（Evidence / Classification / Reachability / Impact / Existing Controls / Proposed Remediation / Compatibility Risk / AC / Verification Method）、TLS/出网边界矩阵、修复设计 SEC-T1..T3（全部 PROPOSED）、Unknowns
- BACKLOG/STATE/DEVELOPMENT_LOG/HANDOFF 同步
- 安全取证命令（全部只输出行号/计数/布尔值，凭据值零打印零复制）

### Excluded

- 修改任何业务代码（含 main.py / legacy / push_service）
- 凭据轮换、`.env` 修改、Mimosa 配置变更或扫描豁免
- 真实网络请求 / 消息发送（含"抓一次真实 response_url 样本"——列为待授权 L3 项）
- git 历史重写（仅在设计中作为 PROPOSED 选项记录）
- WIKI.md 内容处理（只评估风险，不改文件）

## Design

纯分析任务。分类采用用户定义四档：TRUE POSITIVE / FALSE POSITIVE / HISTORICAL RISK / UNKNOWN（可叠加）。每条 finding 绑定 file:line 证据；凭据以"文件:行号 + 变量名"指认，任何输出不含值。

## Acceptance Criteria

- [x] AC-1 BL-018 五项全部登记并定级（SEC-01..05）
- [x] AC-2 新增安全面覆盖：WS TLS 禁用（SEC-06）、qywx_websocket getenv 凭据默认值（SEC-07）、README 凭据表（SEC-08）、WIKI.md 泄漏面（SEC-09）、LLM_BASE_URL scheme（SEC-10）
- [x] AC-3 取证全程未打印任何凭据值（命令仅输出行号/计数/布尔值）
- [x] AC-4 真实风险均有修复设计（SEC-T1/T2/T3，含 Compatibility Risk 与 AC）；全部 PROPOSED
- [x] AC-5 FALSE POSITIVE（SEC-02/04/05/10）均给出复核依据
- [x] AC-6 Unknowns（U1-U6）显式列出且注明解决所需证据
- [x] AC-7 verify.py 回归通过（确认零代码改动）

## Verification

文档交叉引用核查；grep 布尔取证复跑；`scripts/verify.py`（L0，确认零代码改动）。验证级别：L0（本任务无运行时验证需求）。

## Risks

- 安全结论依赖代码静态阅读，未经动态验证（真实 callback 样本、MITM 演示均未做）——已在 Unknowns 声明
- 分类含主观判断（FP 判定）——每条附复核依据供 Review 挑战

## Dependencies

- 用户后续批准 SEC-T1/T2/T3 才进入修复实施
- M2 终验（BL-014/BL-016）与本任务并行不冲突

## Completion Evidence

- Tests: `scripts/verify.py` → compile/semantic/watchdog 3/3 PASS，exit 0（L0 回归守护；本任务无代码改动，无运行时验证需求）。
- Commands: 安全取证 A-M 批次（TLS/CERT_NONE 分布、URL sink 清单、凭据字面量定位与非占位符布尔判定、git 历史深度、origin）——**全部仅输出行号/计数/布尔值，凭据值零打印零复制**；grep 交叉引用核查（SECURITY-REVIEW 被 BACKLOG×3 处引用）。
- Git commit: 未提交（无授权）。
- Review: 以 TASK-009 状态同步闭环（2026-10-01）。
- **完成依据（TASK-009 任务书）**：①SECURITY-REVIEW 已完成；②Public repository 暴露事实已确认（U1）；③SEC-01/07/08 已通过 TASK-006/007 完成处置闭环（Historical Exposure CONFIRMED / Credential RETIRED/REVOKED / Compromise UNKNOWN）；④剩余 SEC-T2/T3/R3 保持独立 PROPOSED（BL-019/BL-012），不影响本任务完成。
- 原 Review 要点存档：①FP 定级是否成立（SEC-02/04/05/10）；②SEC-03 可达性判断；③SEC-T1/T2/T3 Compatibility Risk；④U1 仓库可见性（已确认 Public）。
- **U1 决议补充（2026-09-30，用户确认）**：Repository Visibility = **Public** → SEC-01/07/08 Exposure = CONFIRMED（互联网公开，自 77c705d 持续），Compromise = UNKNOWN；凭据轮换（SEC-T1 第①步）紧急度升为最高。已同步 SECURITY-REVIEW.md §2/§3/§5。

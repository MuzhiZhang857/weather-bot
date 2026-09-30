# TASK-005: Credential Exposure Remediation Design（仅设计，不执行）

- ID: TASK-005
- Status: READY_FOR_REVIEW
- Requirement: 用户直接指令（2026-09-30 TASK-005 任务书）；承接 SECURITY-REVIEW.md SEC-01/07/08（Exposure=CONFIRMED PUBLIC，U1 决议）
- Created: 2026-09-30

## Objective

针对 Public 仓库凭据暴露（SEC-01/07/08）制定正式处置方案：暴露资产清单、影响分析、SEC-R1..R4 修复方案、风险与回滚、验收标准。**只产出设计文档。**

## Why

U1 已确认仓库 Public → 凭据按"已泄露"处理，轮换为最高优先；无正式处置方案则修复无法立项与验收。

## Evidence

- SECURITY-REVIEW.md SEC-01/07/08（Exposure=CONFIRMED）；BL-018
- 暴露位置（值零打印，方法见设计文档 §0）：wechat_weather.py:4/5/6/8、qywx_websocket.py:44/45/48/53、README.md:136/137/142/159、WIKI.md:274/275/282/291
- git 历史：三文件自 77c705d（Initial commit）在库；origin = GitHub Public

## Scope

### Included

- docs/SECURITY-CREDENTIAL-REMEDIATION.md：资产清单（路径/行号/变量名/暴露类型，值零记录）、四维影响分析（HEAD/历史/公开可见性/部署环境）、SEC-R1 轮换方案、SEC-R2 代码与文档清理、SEC-R3 历史重写评估、SEC-R4 部署环境变量迁移、风险与回滚、AC（全 PROPOSED）
- 泄露值与在用值（.env）的同/异判定（布尔输出）
- STATE/HANDOFF/DEV_LOG/BACKLOG 关联同步

### Excluded

- 执行任何修复（轮换/清理/重写/迁移均未实施）
- 修改业务代码、legacy、`.env`、git 历史、WIKI.md 内容
- 读取/展示/复制任何凭据值（比对在 shell 内存完成，仅输出同/异与文件名）
- 创建后续任务

## Design

见 docs/SECURITY-CREDENTIAL-REMEDIATION.md。关键设计前提：以"泄露值是否等于在用值"的布尔判定划分紧急度；轮换（R1）先于一切清理（R2）；历史重写（R3）默认不建议、独立决策。

## Acceptance Criteria

- [x] AC-1 资产清单覆盖全部 4 类凭据 + 其他敏感配置，且值零记录
- [x] AC-2 影响分析覆盖 HEAD / 历史 / 公开可见性 / 部署环境四维
- [x] AC-3 SEC-R1..R4 各含步骤、风险、回滚
- [x] AC-4 AC 全部标记 PROPOSED 且可验证（方法注明）
- [x] AC-5 泄露值 vs 在用值判定完成（决定 R1 紧急度的事实）
- [x] AC-6 与 SECURITY-REVIEW.md / BL-018 / STATE §6-3 引用一致

## Verification

文档交叉引用核查；资产清单以离线布尔/文件名取证复跑（零值输出）；`scripts/verify.py` 回归（L0，确认零代码改动）。

## Risks

- 同/异判定依赖 .env 当前值即为"在用值"的假设（Hermes 实际消费 .env）——已在文档声明
- 无法离线验证 Compromise（第三方是否已获取）——按已泄露处理的保守假设贯穿全文

## Dependencies

- 用户批准本设计后才可立项实施任务（轮换步骤本身是用户平台操作）
- U5（旧凭据使用方盘点）为 R1 的前置

## Completion Evidence

- Tests: 本任务纯文档；`scripts/verify.py` 3/3 PASS（前轮回归，零代码改动）。
- Commands: 暴露扫描（git grep -lF 按 HEAD 树 + WIKI.md 布尔）与泄露值 vs 在用值同/异判定——**全部仅输出文件名与同/异布尔，凭据值零打印**；LLM_API_KEY 计划外命中已定性为占位符（长度 7 + 字符集布尔判定，值零打印）。
- Git commit: 未提交（无授权）。
- Review: 待用户执行。Review 要点：①R1 轮换顺序与中断窗口是否可接受；②R3 默认 Skip 是否同意；③SCHEDULE_CHAT_ID 不可轮换的定性；④附带发现（LLM 占位符）是否需要运营动作。

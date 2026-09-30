# TASK-003: Watchdog 实现收敛（Implementation Convergence）

- ID: TASK-003
- Status: COMPLETED
- Requirement: REQ-011..014（**ACCEPTED**，用户 2026-09-30 TASK-003 任务书批准）+ DESIGN-watchdog.md + AC-1..8
- Created: 2026-09-30
- Completed: 2026-09-30

## Objective

使现有 watchdog 实现收敛到已批准的 REQ-011..014 + DESIGN-watchdog.md：修复 D1（CWD 依赖）、补齐 D2 测试、落地 state git 策略、完成文档对齐，产出 AC-1..AC-8 的可验证证据。

## Why

M2 收敛的实现门槛：用户已批准需求基线（含两项显式设计决定：事件告警与日报双通道分离；配置不依赖 CWD），实现需与之对齐并补齐可验证性。

## Evidence

- docs/DESIGN-watchdog.md（§4 缺陷 D1/D2、§5 设计、§6 AC）
- REQ-011..014（SHALL 语句）；BACKLOG BL-008/011/015
- semantic_engine.py:20（CWD 缺陷现场）；state/weather_state.json（运行态数据）

## Scope

### Included

- D1 修复：SemanticEngine 默认配置目录改为相对模块定位（不改规则语义，显式 config_dir 入参保持兼容）
- D2：新增 test_watchdog.py（unittest，全离线）——状态机去重/解除/再告警/持久化/恢复/损坏容错、precip_soon_in 三信号规则、城市解析、monitor 流程级离线集成（stdout 契约 + 取数失败冻结状态）；verify.py 接入
- State git 策略：.gitignore 增加 state/*（保留 .gitkeep）；不删改现有运行态数据
- 文档对齐：REQUIREMENTS（状态升 ACCEPTED，记录授权来源）、DESIGN（状态/未决问题闭环）、DECISIONS（ADR-015：批准基线 + 双通道决定）、ARCHITECTURE（D1 相关风险与未知项更新）、STATE/ROADMAP/BACKLOG/DEVELOPMENT_LOG/HANDOFF

### Excluded

- Hermes 改造/信息获取（→ BL-016 Integration Evidence，M2 终验前解决）
- D3 锁机制 / D4 迟滞（按任务书记录为已知风险，不实现）
- 新增数据库/Redis、重写 PushService、改协议/日报语义/LLM/天气 API/部署平台/credentials、删 legacy、升级无关依赖、push Git、真实消息发送
- README/WIKI 重写（BL-014，属 M2 终验对齐；TASK-003 AC-7 限定协议内文档）

## Design

D1 修复采用"默认路径锚定模块位置"方案：`config_dir or <repo>/config`，显式传参兼容不变。测试全部离线：unittest + unittest.mock 替换天气/LLM 外部服务，monitor 流程测试以 redirect_stdout 捕获验证 stdout 契约与状态冻结。

## Acceptance Criteria

- [x] AC-1 规则三信号（文本/pop/precip）行为符合 DESIGN §5（PrecipSoonRuleTests 5 例）
- [x] AC-2 去重状态机 new→send→persist→suppress→release→re-alert（WeatherStateTests + MonitorFlowTests）
- [x] AC-3 状态持久化：正常写入/恢复/**损坏容错（两种故障模式：非法 JSON + 路径不可读）**/单进程无中间态污染（WeatherStateTests）
- [x] AC-4 城市配置解析支持 DESIGN §5.4 全部形式（ConfigResolutionTests.test_city_parsing_forms）
- [x] AC-5 stdout 契约：新告警输出、未命中/重复零业务输出、无调试文本混入（MonitorFlowTests，redirect_stdout 捕获）
- [x] AC-6 任意 CWD 启动规则完整加载（test_rules_load_regardless_of_cwd，子进程 cwd=系统临时目录）
- [x] AC-7 实现/REQ/Design/Architecture/State/Task 文档一致（REQUIREMENTS 升 ACCEPTED、DESIGN 冻结、ADR-015、ARCHITECTURE D1/测试表、STATE/ROADMAP/BACKLOG 同步）
- [x] AC-8 verify.py 全绿（compile/semantic/watchdog 三步 PASS）

## Verification

L0（编译/静态/交叉引用/git diff 审计）+ L1（新增单测）+ L2 离线集成（mock 外部服务的 monitor 流程测试）。不进行真实消息发送。目标声明：L2(offline)。

## Risks

- chdir 类测试污染同进程其他测试 → 已规避：CWD 测试改为子进程方案，无 chdir
- 流程测试写真实 state 文件 → 已规避：全部注入 tmp 路径
- D1 改变了"从其他目录启动时读到彼处 config"的边角行为 → 即缺陷本体，经用户批准修复（ADR-015）

## Dependencies

- 用户已批准 REQ-011..014 与两项显式设计决定（Q2/Q3 已决；Q4 Hermes → BL-016）

## Completion Evidence

- Tests: `scripts/verify.py` → compile PASS + semantic PASS + watchdog PASS（test_watchdog.py **23/23**），退出码 0。
- Commands: `git diff --stat` 审计（业务文件仅 semantic_engine.py 增加 D1 修复 +11/-4；.gitignore +4；总 256+/54-）；`git check-ignore state/weather_state.json` → 命中 .gitignore:54；`grep` 核查 REQ-011..014 全 ACCEPTED、DESIGN 状态 ACCEPTED、ADR-015 存在、DESIGN 被 5 处文档引用。
- Git commit: 未提交——**等待 Review 后由用户授权**（AGENTS.md §6：用户明确要求才 commit）。
- Review: 交由用户执行（本任务按任务书停在 READY_FOR_REVIEW）。Review 要点：①semantic_engine.py 的 D1 diff；②test_watchdog.py 覆盖面与断言强度；③state git 策略；④文档基线一致性。已知遗留：D3/D4（决定接受）、D5-D7（BACKLOG/记录）、BL-014/BL-016（M2 终验前）。

### Review Round 1（Gate Review，2026-09-30）：CONDITIONAL PASS → 已整改

- **整改项（唯一）**：AC-3 的"损坏容错"证据不完整——原测试只覆盖"路径不可读"（目录占位，IsADirectoryError），未覆盖 DESIGN §5.3 明确的"文件可打开但内容非法 JSON"（json 解码失败）故障模式。**已修复**：新增静态 fixture `tests/fixtures/corrupted_weather_state.json`（截断的非法 JSON，模拟写入中途崩溃）+ `test_corrupted_json_starts_empty`（复制 fixture 到临时路径 → 加载容错 → 按新告警重建 → 自愈后重载语义正常）；原目录占位测试保留并注明为另一故障模式。测试 22→23 例，verify.py 重跑 3/3 PASS。
- **Review 意见采纳记录**：ResourceWarning（日志 handler 未 close）按 Review 要求立案 **BL-017**（本任务不修）。
- **本轮边界声明（沿用 Review 声明）**：本轮整改仅补测试证据与文档痕迹，**零业务代码改动**；DESIGN-watchdog.md AC-3 描述同步更新。

### Final Review（2026-09-30）：PASS → COMPLETED

- Final Review: **PASS**（用户）；Review Round 1: CONDITIONAL PASS → 整改完成（见上）。
- AC-1..AC-8 全部通过；watchdog tests **23/23 PASS**；`scripts/verify.py` **3/3 PASS**（compile / semantic / watchdog），exit code 0。
- Verification Level: **L0 + L1 + offline L2**（未做真实网络/消息验证；Hermes 端到端证据 → BL-016）。
- D1：已修复；D2：已完成；D3/D4：按决议保留为已知风险；Hermes：仍为 UNKNOWN / Deferred（BL-016）。
- Business code change：仅 D1 修复（services/semantic_engine.py）；Scope：无未授权扩张。
- Git checkpoint: 单 atomic commit `feat: finalize watchdog implementation`（含本任务及此前未入库的 watchdog 实现与 ADP 治理文档；hash 见 `git log`）。
- 用户裁决（checkpoint 阶段，2026-09-30）：**方案 3**——授权在已知 Mimosa L3 安全发现存在下提交（发现清单与分类见 BACKLOG BL-018，均非本任务 diff 引入）；**checkpoint 不代表这些发现已解决**，处置归独立安全任务。

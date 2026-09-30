# HANDOFF — Agent 交接协议

> **规则**：任何 Agent 结束一段工作（会话结束 / 任务暂停 / 切换给别人）时，必须在本文末尾"交接记录"区追加一条记录。
> 目标：Claude Code → Codex → Gemini → Cursor 任意方向都能无缝接管。
> 交接记录按时间倒序排列（最新的在最上面）。超过 10 条后，把最旧的移入 `.ai/history/`。

## 交接记录必须包含的字段

| 字段 | 说明 |
|---|---|
| Date / Agent | 交接时间与留下记录的 Agent（工具名） |
| Project / Milestone | 项目名与当前里程碑（ADP-1.0 §30 要求；见 docs/ROADMAP.md） |
| Current Task | 正在做的任务（引用 `tasks/NNN-*.md`）及其状态机状态 |
| Completed | 本次完成了什么（具体到可验证的事实） |
| Not Completed | 计划内但没做的，以及为什么 |
| Files Changed | 修改/新增的文件清单（区分业务代码与文档） |
| New Findings | 过程中新发现的问题/风险（同步进 docs/STATE.md） |
| Test Results | 运行了哪些验证命令，结果原文摘要 |
| Git State | `git status` 摘要：改了哪些、哪些是前人遗留未提交的 |
| Next Step | 接手者第一步做什么 |
| Needs User Decision | 需要用户拍板的事项（没有则写"无"） |

## 交接记录模板（复制使用）

```markdown
## YYYY-MM-DD HH:MM — <Agent 名>
- **Project / Milestone**: weather-bot · M?（见 docs/ROADMAP.md）
- **Current Task**: tasks/NNN-xxx.md（六态状态机状态）
- **Completed**: …
- **Not Completed**: …
- **Files Changed**: …
- **New Findings**: …（非阻塞 → BACKLOG；阻塞 → STATE.md §6）
- **Test Results**: 验证命令 + 验证级别（L0-L4）+ 结果
- **Git State**: …
- **Next Step**: …
- **Needs User Decision**: …
```

## 接手者操作顺序

1. 读 `AGENTS.md`；
2. 读 `docs/STATE.md`（现状 + 阻塞）；
3. 读本文最上面一条交接记录；
4. 读对应 `tasks/NNN-*.md`；
5. `git status` + `git diff` 核实工作区与交接描述一致；
6. 有出入 → 以实际工作区为准，先在任务文件里更正记录再动工。

---

## 交接记录

## 2026-09-30（夜 4）— ZCode（TASK-007：凭据退役与静态暴露清理）
- **Project / Milestone**: weather-bot · 安全处置进行中（M2 终验尾巴 BL-014/BL-016 部分）
- **Current Task**: tasks/completed/007-credential-retirement-cleanup.md（**COMPLETED**——P1-P3 平台失效确认 + Finalization 完成）
- **Completed**: 执行计划（P/A/V/N 四类责任划分）；静态清理落地——README 5 处、WIKI 4 处占位符化，qywx_websocket.py 4 处 getenv 默认值清空，wechat_weather.py 2 处字面量改 os.getenv（+import os）；离线验证 V1-V4 全过（HEAD 工作树 0 命中）；SECURITY-REVIEW/CREDENTIAL-REMEDIATION/ROTATION-PLAN 状态同步（SEC-01/07/08 = 静态清理完成、平台失效 PENDING，**未降级**）。
- **Not Completed**: R3 历史重写（独立 PROPOSED/Skip）；未 commit（等 checkpoint Review）。P1-P3 ✅ 用户已完成（2026-09-30）。
- **Files Changed**: README.md、WIKI.md、qywx_websocket.py（getenv 默认值）、wechat_weather.py（getenv + import os）、docs/SECURITY-REVIEW.md、docs/SECURITY-CREDENTIAL-REMEDIATION.md、docs/SECURITY-CREDENTIAL-ROTATION-PLAN.md、docs/STATE/DEVELOPMENT_LOG、BACKLOG、HANDOFF、tasks/007。**weather_monitor.py / .env / Hermes 链路零改动**。
- **New Findings**: README.md:228 非表格形式的会话 ID 日志示例逃过首轮表格清洗——复扫（按值全文布尔）补清；教训见 DEV_LOG。
- **Test Results**: `scripts/verify.py` 3/3 PASS（legacy 修改后仍可编译）；布尔扫描 tracked 树 0 命中。
- **Git State**: README/qywx/wechat_weather/多份文档未提交修改 + WIKI.md untracked（已占位符化）；HEAD d37ed3a；未 push。
- **Next Step**: 用户执行 P1-P3 平台失效 → 回告 → Agent 降级 SEC-01/07/08 并更新基线（轻量，不新建任务）→ M2 终验收尾。
- **Needs User Decision**: TASK-007 Git checkpoint Review；commit 授权。SEC-01/07/08 最终状态 = Historical Exposure CONFIRMED / Credential RETIRED/REVOKED / Compromise UNKNOWN。


## 2026-09-30（夜 3）— ZCode（TASK-006：WeCom SECRET 轮换准备）
- **Project / Milestone**: weather-bot · 安全基线（TASK-004/005 READY_FOR_REVIEW、TASK-006 COMPLETED）· M2 终验尾巴不变
- **Current Task**: tasks/completed/006-wecom-secret-rotation-prep.md（**COMPLETED**——Review PASS，两项修正已落）
- **Completed**: docs/SECURITY-CREDENTIAL-ROTATION-PLAN.md（SECRET 消费方 C1-C5、部署面四方确认表、Before/Rotation/After 步骤、不可逆回滚设计）；STATE/BACKLOG/DEV_LOG 同步。
- **Not Completed**: 轮换执行（待批准+待部署面确认）；SEC-R2 清理；U5/部署面 UNKNOWN 项（用户确认）。
- **Files Changed**: 新增 tasks/006-*.md 与 docs/SECURITY-CREDENTIAL-ROTATION-PLAN.md；修改 STATE/BACKLOG/DEV_LOG/HANDOFF。**业务代码零改动**。
- **New Findings**: wechat_weather.py 的 webhook 用法把 AI Bot SECRET 字符串当群机器人 webhook key 使用——该对象语义不同，此用法是否曾成功投递 UNKNOWN；轮换后该字面量必然失效，默认建议随 legacy 下线。
- **Test Results**: 纯文档任务；消费方取证值已掩码输出。
- **Git State**: 工作区 = TASK-004/005/006 安全文档 + 前轮遗留（.gitignore、WIKI.md OUT OF SCOPE）；HEAD d37ed3a；未 commit。
- **Next Step**: 用户 Review 三份安全文档（SECURITY-REVIEW / CREDENTIAL-REMEDIATION / ROTATION-PLAN）→ 确认部署面 → 批准后按 ROTATION-PLAN 执行轮换（用户平台操作）。
- **Review 结果**：PASS（两项修正已落文档：失效语义 UNKNOWN 化 + 独立凭据对象建模；联动 CREDENTIAL-REMEDIATION/SECURITY-REVIEW）。
- **Needs User Decision**: **U5 运行面确认（轮换执行前置）**：Railway/Render 活跃性与配置、legacy webhook 路径是否仍被使用；轮换窗口；SEC-T2/T3 是否立项。


## 2026-09-30（夜 2）— ZCode（TASK-005：凭据暴露处置设计）
- **Project / Milestone**: weather-bot · 安全基线（TASK-004/005 均待 Review）· M2 终验尾巴不变
- **Current Task**: tasks/005-credential-exposure-remediation-design.md（**READY_FOR_REVIEW**）
- **Completed**: docs/SECURITY-CREDENTIAL-REMEDIATION.md（资产清单 A1-A8、四维影响分析、SEC-R1..R4、风险与回滚、AC 全 PROPOSED）；泄露值 vs 在用值布尔判定完成；STATE/BACKLOG/DEV_LOG 同步。
- **Not Completed**: 一切执行（轮换/清理/重写/迁移均未实施，待批准立项）；U5 使用方盘点（用户）。
- **Files Changed**: 新增 tasks/005-*.md 与 docs/SECURITY-CREDENTIAL-REMEDIATION.md；修改 BACKLOG/STATE/DEV_LOG/HANDOFF。**业务代码零改动**。
- **New Findings**: ①SECRET/BOT_ID/CHAT_ID 泄露值=在用值（活凭据公开，轮换最高优先）；②HEFENG 泄露为旧值，在用 key 未暴露；③LLM_API_KEY=.env 占位符 → LLM 文案当前实际不可用（一直降级模板）——运营事实，待用户决定是否配置真实 key。
- **Test Results**: 本任务为纯文档任务；取证命令仅输出行号/计数/同异布尔，凭据值零打印。
- **Git State**: 工作区 = TASK-004/005 文档 + 前轮遗留（.gitignore 的 .mimosa 忽略项、WIKI.md OUT OF SCOPE）；HEAD d37ed3a；未 commit。
- **Next Step**: 用户 Review 两份安全文档（SECURITY-REVIEW.md + SECURITY-CREDENTIAL-REMEDIATION.md）→ 批准后立项实施（SEC-T1/R1 为最高优先）。
- **Needs User Decision**: 批准 SEC-R1..R4 执行范围与顺序；U5 使用方盘点；是否配置真实 LLM key（附带发现）。


## 2026-09-30（夜）— ZCode（TASK-004：安全基线与修复设计）
- **Project / Milestone**: weather-bot · M2 Watchdog（终验尾巴 BL-014/BL-016）+ 安全基线建立
- **Current Task**: tasks/004-security-baseline-design.md（**READY_FOR_REVIEW**）
- **Completed**: docs/SECURITY-REVIEW.md（攻击面总览、S-01..S-10 定级 TP×6/FP×4、SEC-T1/T2/T3 修复设计全部 PROPOSED、U1-U6 Unknowns）；BL-012/BL-018 关联定级、BL-019 立案；STATE/DEV_LOG 同步。
- **Not Completed**: 一切修复实施（SEC-T1/T2/T3 均待批准）；凭据轮换（用户平台操作）；真实样本取证（U3/U4 需 L3 授权）。
- **Files Changed**: 仅新增 tasks/004-*.md 与 docs/SECURITY-REVIEW.md，修改 BACKLOG/STATE/DEV_LOG/HANDOFF。**业务代码零改动**。
- **New Findings**: SEC-06（WS 证书校验禁用→订阅凭据可被 MITM 截获，全项目最高危单点）；SEC-08/09（README 已提交 + WIKI 未跟踪均含非占位符凭据内容，值零打印）；U1 仓库可见性 UNKNOWN。
- **Test Results**: `scripts/verify.py` 3/3 PASS（回归守护，L0）。
- **Git State**: 工作区 = 本任务文档新增/修改 + 前轮遗留的 ` M .gitignore`（.mimosa 忽略项）与 `?? WIKI.md`（OUT OF SCOPE）；HEAD d37ed3a；未 commit。
- **Next Step**: 用户 Review SECURITY-REVIEW.md → 批准 SEC-T1/T2/T3 中任意项即立项实施；建议同步完成 U1（仓库可见性，1 分钟）。
- **Needs User Decision**: SEC-T1/T2/T3 批准与否；凭据轮换时机（U1 已决议：仓库 Public，2026-09-30 → SEC-01/07/08 Exposure=CONFIRMED，轮换紧急度最高；Compromise=UNKNOWN）。SECURITY-REVIEW.md §2/§3/§5 已同步该事实。


## 2026-09-30（晚）— ZCode（TASK-003：Watchdog 实现收敛）
- **Project / Milestone**: weather-bot · M2 Watchdog（IN_PROGRESS——实现收敛已完成并入库，剩终验尾巴 BL-014/BL-016）
- **Current Task**: tasks/completed/003-watchdog-convergence.md（**COMPLETED**，Final Review PASS）
- **Completed**: D1 修复（semantic_engine 默认配置目录锚定项目根，显式入参兼容）；D2 补测（test_watchdog.py 22 例全绿：状态机/规则三信号/城市解析/CWD 子进程验证/monitor 流程 stdout 契约与失败冻结）；verify.py 升级三步闭环（compile+semantic+watchdog）；state git 策略（state/* gitignored + .gitkeep，运行数据未动）；文档对齐（REQ-011..014→ACCEPTED、DESIGN 冻结为基准、ADR-015、ARCHITECTURE/STATE/ROADMAP/BACKLOG 同步、BL-016 立案）。
- **Not Completed**: commit（等 Review 后授权）；D3 锁/D4 迟滞（任务书决定不做）；README/WIKI 对齐（BL-014，M2 终验）；Hermes 证据（BL-016）。
- **Files Changed**: 业务代码仅 `services/semantic_engine.py`（D1，+6/-3 行）；新增 `test_watchdog.py`、`state/.gitkeep`；修改 `.gitignore`、`scripts/verify.py` 及 9 个文档（REQUIREMENTS/DESIGN/DECISIONS/ARCHITECTURE/STATE/ROADMAP/BACKLOG/DEVELOPMENT_LOG/HANDOFF）。
- **New Findings**: 流程测试暴露 weather_monitor setup_logging 的 ResourceWarning（handler 未 close）——无害（单次初始化+GC 兜底），未在 Scope 内处理，如需清理走 BACKLOG。
- **Test Results**: `scripts/verify.py` → compile PASS / semantic PASS / watchdog PASS（22/22），退出码 0。**Verification Level: L0 + L1 + L2(offline)**（mock 外部服务；未做真实网络/消息验证——L3/L4 未达）。
- **Git State**: 业务文件 diff 现为 watchdog 原有改动 + D1 修复；HEAD 仍 dca395e；全部未 add/commit。
- **Next Step**: 用户 Review（重点：semantic_engine.py 的 D1 diff、test_watchdog.py 覆盖面、git diff 审计）→ 授权 commit → M2 终验前补 BL-014/BL-016。
- **Needs User Decision**: Review 结论（通过/整改项）；commit 拆分方式与授权。
- **Review Round 1（Gate Review）结果**：CONDITIONAL PASS——唯一整改项（AC-3 损坏容错证据不完整）**已补齐**：静态 fixture `tests/fixtures/corrupted_weather_state.json` + `test_corrupted_json_starts_empty`（23/23，verify.py 3/3 PASS）；ResourceWarning 立案 BL-017。任务**保持 READY_FOR_REVIEW**，等待最终 Review；本轮零业务代码改动。
- **Final Review（2026-09-30）结果**：**PASS** → TASK-003 **COMPLETED**（tasks/completed/003-watchdog-convergence.md）。Git checkpoint：单 atomic commit `feat: finalize watchdog implementation`（hash 见 git log）。M2 终验剩余：BL-014（README/WIKI 对齐）、BL-016（Hermes 证据）。**Next Step：等待用户授权下一项 Task。**

## 2026-09-30（傍晚）— ZCode（TASK-002：watchdog 需求与设计正式化）
- **Project / Milestone**: weather-bot · M2 Watchdog（IN_PROGRESS，等用户 Q1-Q4 裁决）
- **Current Task**: tasks/completed/002-watchdog-formalization.md（COMPLETED）
- **Completed**: docs/DESIGN-watchdog.md（14 条 FACT 行为清单、S1-S8 设计分类与合理性论证、D1-D8 缺陷处置、正式设计规格、AC-1..8）；REQUIREMENTS.md REQ-011..014 SHALL 化（保持 PROPOSED）；STATE/ROADMAP/DEVELOPMENT_LOG 同步；任务编号修正（watchdog 主任务=TASK-003）。
- **Not Completed**: 需求状态升级（等你 Q1-Q4）；D1 修复与功能提交（TASK-003 范畴）；业务代码零改动。
- **Files Changed**: 仅 .md（DESIGN-watchdog.md 新增；REQUIREMENTS/STATE/ROADMAP/DEVELOPMENT_LOG/HANDOFF/tasks 修改）。
- **New Findings**: D3（状态文件无并发保护）、D4（告警抖动无迟滞）、D7（--once 空参数/ALERT_LEAD_HOURS fail-fast）、D8（Hermes 不可验证）——均已入 DESIGN §4 并给处置；无新代码缺陷需要立即修复。
- **Test Results**: `scripts/verify.py` PASS 退出码 0（L0+L1 回归守护）；文档交叉引用核查通过。
- **Git State**: watchdog 未提交改动（6 M + 4 untracked）原样保留；HEAD dca395e；本次全部为文档变更，未 add/commit。
- **Next Step**: 你回答 DESIGN-watchdog.md §7 的 Q1-Q4 → 授权启动 TASK-003（D1 修复 + 单测 + gitignore 决策落地 + 提交/回滚 + 文档对齐）。
- **Needs User Decision**: Q1（REQ-011..014 批准范围）、Q2（D1 修 or 确认 Hermes CWD）、Q3（双通道去重语义）、Q4（Hermes 信息提供）。

## 2026-09-30（下午）— ZCode（TASK-000：ADP-1.0 正式采纳）
- **Project / Milestone**: weather-bot · M2 Watchdog（IN_PROGRESS，BLOCKED 于用户裁决）；本次任务属流程层，不改变里程碑。
- **Current Task**: tasks/completed/000-adopt-adp-1.0.md（COMPLETED，Completion Evidence 已填）
- **Completed**: Phase A——AGENTS.md（协议入口 + §0.5 事实来源解释 + 阅读顺序 + 需求裁决门 + Opportunistic Discovery + 六态状态机 + 七阶段/验证分级/No False Completion）、tasks/README.md（六态模板）、DECISIONS.md（ADR 模板加 Alternatives + ADR-014）。Phase B——新增 REQUIREMENTS.md（REQ-001..015）、ROADMAP.md（M0-M4）、BACKLOG.md（BL-001..015）、DEVELOPMENT_LOG.md（bootstrap）、docs/ADP-1.0.md（协议逐字存档）。同步——STATE.md §5 迁移 BACKLOG、§7 改为当前未提交工作区、§8 指向 TASK-001；HANDOFF 模板加 Milestone。收尾后按 Mimosa L2 复查微调 AGENTS.md §4 `.env` 行措辞（纯文档安全措辞，实质规则不变）。
- **Not Completed**: Phase C（按裁决暂缓）；未 commit（用户未授权）；watchdog 需求裁决（REQ-011..014 保持 PROPOSED）。
- **Files Changed**: 仅 .md 文件（AGENTS.md、tasks/README.md、docs/DECISIONS.md、docs/STATE.md、.ai/HANDOFF.md 修改；docs/ADP-1.0.md、REQUIREMENTS.md、ROADMAP.md、BACKLOG.md、docs/DEVELOPMENT_LOG.md、tasks/000-*.md 新增）。**业务代码零改动**。
- **New Findings**: 无新缺陷；迁移中确认 BL-015（watchdog 去重逻辑无 L1 测试覆盖）已入 BACKLOG。
- **Test Results**: `$PY scripts/verify.py` → PASS，退出码 0（验证级别 L0+L1；L2-L4 未执行——无外发授权）。
- **Git State**: 前序 watchdog 未提交改动（6 M + 4 untracked）原样保留；本次全部为文档新增/修改，均未 add/commit；HEAD 仍为 dca395e。
- **Next Step**: 用户裁决 STATE.md §6 → 启动 TASK-001「watchdog 裁决与提交（M2 收敛）」。
- **Needs User Decision**: STATE.md §6 四项（其中 §6-1 即 REQ-011..014 的 ACCEPTED/弃用裁决）。

## 2026-09-30 — ZCode（本条为协议建立时的首次交接）
- **Current Task**: tasks/001-agent-handoff-bootstrap.md（Status: Active，验收项已全部勾选，待用户审阅后移入 completed/）
- **Completed**: 全量只读审计；创建 AGENTS.md、docs/{ARCHITECTURE,DEVELOPMENT,DECISIONS,STATE}.md、tasks/（README + 001）、.ai/HANDOFF.md、scripts/verify.py；核查文档与代码一致性（CONFLICT 见 docs/STATE.md §5 与 ARCHITECTURE.md）。业务代码零改动。收尾阶段按 Mimosa L2 安全复查意见加固 AGENTS.md 凭据红线（禁止读取/展示/上传凭据值，清理只做占位符替换，外发操作逐次确认）。
- **Not Completed**: 未修复 test_weather_service.py 语法错误（属行为变更，需用户取舍）；未提交任何 git 变更；未清理疑似泄露的凭证（需先轮换，用户决策）。
- **Files Changed**: 仅新增文档与 scripts/verify.py；未触碰 services/、models/、main.py、weather_monitor.py、config/。
- **New Findings**: ①test_weather_service.py:10 语法损坏；②requirements 的 openai/schedule 无 import；③.venv 指向已卸载的解释器、.venv2 无 pip；④三处重复的模板变量构建；⑤两套时区实现并存；⑥SemanticEngine 相对 CWD 读 config；⑦render.yaml 与 railway.json 启动命令漂移。均已记入 docs/STATE.md。
- **Test Results**: `.venv2/Scripts/python.exe scripts/verify.py` → 全项目 17 个 .py 编译检查（1 个已知损坏文件按预期标注）+ test_semantic_engine 8 场景标签断言，全部 PASS，退出码 0。
- **Git State**: 前序遗留未提交改动 6 个文件（.env.example、config/weather_rules_default.json、models/weather_types.py、services/{llm_service,semantic_engine,weather_service}.py）与未跟踪（WIKI.md、weather_monitor.py、services/weather_state.py、state/、.mimosa/）**原样保留未动**；本次新增文档均未 add/commit。
- **Next Step**: 用户审阅本文档体系 → 决定 STATE.md §6 四个决策项 → 按 STATE.md §8 顺序执行（优先：提交 watchdog 功能、处置凭证）。
- **Needs User Decision**: ①未提交 watchdog 功能是否入库；②三条部署路径保留哪些 / Hermes 调度配置在哪；③凭证轮换与清理范围；④state/ 是否 gitignore；⑤损坏的 test_weather_service.py 修复还是删除。

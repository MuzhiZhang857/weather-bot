# AGENTS.md — AI Agent 协作规范

> 本文件面向任何在本仓库工作的 AI Agent（Claude Code、Codex、Gemini CLI、Cursor 等）。
> 目标：不依赖某个特定 Agent 的历史上下文，也能安全地继续开发、测试和交接。
> **治理协议**：本项目自 2026-09-30 起正式采用 **ADP-1.0**（原文存档：[docs/ADP-1.0.md](docs/ADP-1.0.md)；决策记录：docs/DECISIONS.md ADR-014）。本文件是协议在项目的落地解释与补充规则；两者冲突时以更严格者为准。

## 0. 铁律（永远优先）

> **Never invent project facts.**
> **Never assume undocumented behavior.**
> **When uncertain, inspect the code, tests, configuration, or git history.**
> **Do not perform large refactors unless explicitly requested.**
> **Preserve existing behavior unless the task requires changing it.**

无法从代码/测试/配置/git 历史确认的事，明确写 `UNKNOWN — requires verification`，不要编造看似合理的答案。

## 0.5 事实来源与冲突处理（ADP-1.0 §4 的项目解释）

- **Current Code** = 当前系统的实际行为；**Tests** = 已验证过的行为；**Requirements** = 系统应满足的产品目标；**ADR/Design** = 已确认的技术设计及其理由；**Task** = 当前被授权实施的工作范围。
- 它们**不是简单的绝对优先级**。发生冲突时：① 不擅自判断产品意图；② 标记 `CONFLICT` 并记录具体冲突（docs/STATE.md §9）；③ 判断是否阻塞当前任务；④ 必要时请求用户决策（STATE.md §6）。
- 证据分级 **FACT / INFERENCE / PROPOSAL / UNKNOWN / CONFLICT**（ADP-1.0 §33）：不得把 INFERENCE 伪装成 FACT，不得把 PROPOSAL 当成 DECISION。

## 1. 项目是什么

中文天气提醒机器人：和风天气 API 取数 → 语义规则引擎打标签 → OpenAI 兼容 LLM 生成文案（失败降级模板）→ 企业微信机器人 WebSocket 推送 / stdout（watchdog 模式）。Python 3.11，无数据库，单机 + 云两条部署路径。

## 2. 开始任何工作前，按序阅读

| 顺序 | 文件 | 作用 |
|---|---|---|
| 1 | `AGENTS.md`（本文件） | 工作规则与协议落地解释 |
| 2 | `docs/ADP-1.0.md` | 治理协议原文（流程争议时查原文） |
| 3 | `docs/STATE.md` | 当前状态、已知 Bug、阻塞问题（**动态文件，先看再动**） |
| 4 | `docs/REQUIREMENTS.md` | 需求清单与状态（ACCEPTED/PROPOSED/UNKNOWN/CONFLICT）——动手前先确认需求依据 |
| 5 | `docs/ROADMAP.md` | 当前里程碑（M0-M4）与退出标准 |
| 6 | `docs/ARCHITECTURE.md` | 实际架构的唯一事实来源（README/WIKI 可能过时） |
| 7 | `docs/DEVELOPMENT.md` | 命令、环境变量、实际使用的工具链 |
| 8 | `docs/DECISIONS.md` | 历史决策及其理由（ADR）；不要推翻未记录理由的决策 |
| 9 | `docs/BACKLOG.md` | 明确"暂不做"的事项——**禁止顺手捞回当前 Scope** |
| 10 | `tasks/`（活动任务）+ `.ai/HANDOFF.md` 最新记录 | 当前任务与最近交接 |
| 11 | 相关源码 + `git log --oneline -10` | 验证文档与代码是否一致 |

若文档与代码冲突：**以代码为准**，并把冲突记录到 `docs/STATE.md`（标注 CONFLICT），不要静默修改任何一方。

## 3. 如何运行 / 测试

```bash
# 统一解释器：.venv2（Python 3.11.15，依赖已装好）。不要用 .venv（已损坏）
PY=".venv2/Scripts/python.exe"

$PY scripts/verify.py        # 最小验证闭环：全模块编译 + 离线语义引擎测试（改码后必跑）
$PY test_semantic_engine.py  # 离线语义测试（无断言，需目检输出）
$PY main.py --mode once      # 真实推送一次（见 §6 需确认事项）
$PY weather_monitor.py       # watchdog 单次检查（真实调用天气/LLM API）
```

- `test_weather_service.py` 当前**语法损坏**（STATE.md Bug B1），运行失败不是你的环境问题。
- 无 pytest / lint / typecheck / CI——不要假设存在，也不要在未要求时引入。
- Windows 环境（Git Bash）。watchdog 的 stdout 是消息通道，**不要**给它加 print。

## 4. 禁止随意修改的目录/文件

| 路径 | 原因 |
|---|---|
| `.env` | 真实凭证文件（已 gitignore，严禁提交）。**内容值不得读取、展示或复制出该文件**；只允许按变量名引用（如 `os.getenv("LLM_API_KEY")`）。涉及该文件的任何操作类别与授权要求见 §5 |
| `state/weather_state.json` | 运行时告警状态；手工改动会导致重复提醒或漏报 |
| `logs/` | 运行时日志，已 gitignore |
| `.venv` / `.venv2` | 环境目录，不入库不修改 |
| `qywx_websocket.py`、`wechat_weather.py` | 旧版脚本（ADR-012），内含硬编码凭证；除非任务明确要求，不改动不删除。涉及凭证时**只说"此处有硬编码凭证"，禁止把值写进任何输出** |
| `prompts/weather_alert.txt` | 占位符与代码变量是字符串契约（ARCHITECTURE.md §8.2）；改模板必须同步 scheduler.py / main.py / weather_monitor.py 三处变量构建 |
| `config/weather_rules_*.json` | 用户可调的规则；规则条件每条只能一个 key（ADR-006 的限制 B2） |
| `services/push_service.py` 的 ping/pong 分支 | 存活性关键代码（ADR-009） |

**凭据安全红线**：任何情况下不得把凭据值（`.env` 内容、代码/文档中的硬编码 Key、群 ID 等）读取到对话、日志、代码示例、commit 信息或任何对外输出中。需要指认时一律用"文件:行号 + 变量名"。

## 5. 需要用户确认才能进行的操作

- **需求裁决**：将任何需求从 PROPOSED 升级为 ACCEPTED、新增 MUST 级需求、或修改 WON'T 边界（REQUIREMENTS.md 的状态变更归用户）；
- 一切 `git push`、force push、历史改写（**每次逐项确认，上一次的同意不顺延**）；
- 真实发送消息的验证（`main.py --mode once/listen/both`、`qywx_websocket.py`）——同样**每次执行前逐次征得用户同意**；
- 修改/移动/删除任何凭证（含清理 README 与旧脚本中的硬编码值）。清理方式：**只做占位符替换**（如 `SECRET=` 留空或写 `<YOUR_SECRET>`），凭据轮换由用户在对应平台后台完成，Agent 不经手任何值；
- 修改部署配置（railway.json / render.yaml）或废弃某条部署路径；
- 升级/移除依赖（尤其 requirements.txt 中未使用的 `openai`、`schedule`）；
- 修改企业微信消息格式、`aibot` 协议字段、和风 API 参数；
- 删除"看起来没用"的代码/文件（本项目多处保留物有记录在案的原因，先查 DECISIONS.md）；
- 大规模重构、目录重组、改数据结构字段名。

## 6. Git 操作规则

- 单 `main` 分支工作流；提交信息用中文 + `feat:` / `fix:` / `docs:` 前缀（沿用现有风格）。
- 只有在用户明确要求时才 commit / push；**默认只改工作区**。
- 提交前跑 `$PY scripts/verify.py`。
- 工作区常有他人/前序 Agent 的未提交改动：动手前先 `git status` + `git diff`，**不要混入、回滚或覆盖不相关的未提交改动**。

## 7. 遇到未知问题与额外发现怎么办

**Opportunistic Discovery Rule（ADP-1.0 §20）**：开发中发现 Bug / 技术债 / 新功能想法 / 架构问题时，先问"它阻塞当前任务吗？"——**阻塞** → 停下升级（安全类可按 §21 立即中断）；**不阻塞** → 记入 `docs/BACKLOG.md`，**不得因为"顺手"而扩大当前 Scope**。发现问题是发现，不等于获得修改权限。

1. 先查 `docs/ARCHITECTURE.md` 的 Unknown Areas 与 `docs/DECISIONS.md`；
2. 再查 `git log` / `git show <commit>` 与 `.trae/` 历史规格文档；
3. 仍无法确认 → 在产出物（代码注释除外）中写 `UNKNOWN — requires verification` 并汇总到 `docs/STATE.md` §6 阻塞问题；
4. 现象与文档矛盾 → 信任代码行为，记录 CONFLICT；
5. 绝不为了"让程序跑通"而静默改变现有行为（尤其降级路径、去重逻辑、时区）。

## 8. 如何记录架构决策

产生新的重大决策（换依赖、改协议、改数据流、改部署目标、新入口）时，在 `docs/DECISIONS.md` 按其中 ADR 模板追加 `ADR-NNN` 条目，写清 **Context / Decision / Alternatives / Consequences / Evidence**（ADP-1.0 §11 要求 Alternatives；ADR-001..013 为采纳前旧格式，不回溯补写，自 ADR-014 起必须包含）。不确定原因的历史行为不要补写理由；"我认为更优雅"不构成决策依据。

## 9. 如何更新 STATE.md 与 BACKLOG.md

每次完成重要工作（功能、修复、部署变更、发现重大问题）后更新 `docs/STATE.md`：**§4 已知 Bug、§6 阻塞问题、§7 未提交工作区、§8 下一动作**，并刷新顶部"最后更新"日期。STATE.md 只描述**当前状态**，不写历史叙事（历史进 git / DEVELOPMENT_LOG / ADR，ADP-1.0 §42）。开发中发现的**非阻塞**问题记入 `docs/BACKLOG.md`（§20），不要塞进 STATE 或当前任务。

## 10. 任务与交接（六态状态机）

- **所有非平凡代码修改必须对应一个任务文件**（模板与状态机见 `tasks/README.md`，ADP-1.0 §12-14）：`PLANNED → IN_PROGRESS → READY_FOR_REVIEW → COMPLETED`，异常态 `BLOCKED` / `CANCELLED`。禁止只有 TODO/DONE 两态。
- 需求依据（GATE 1）：任务文件的 Requirement 必须指向 `docs/REQUIREMENTS.md` 中 **ACCEPTED** 的条目，或用户直接指令；只有 PROPOSED 需求支撑的功能开发须先获用户裁决。
- 任务完成后移入 `tasks/completed/`，Completion Evidence 填写验证命令与结果。
- 结束工作时**必须**按 `.ai/HANDOFF.md` 的协议留交接记录（含 Milestone 字段）。
- 接手他人任务时：读 STATE.md → 读任务文件 → 读最近 HANDOFF → `git status`/`git diff` 核实工作区。

## 11. 七阶段生命周期与验证分级

每次任务执行遵循 **ORIENT → PLAN → DESIGN → IMPLEMENT → VERIFY → REVIEW → RECORD**（ADP-1.0 §15）：

- **ORIENT** = 本文 §2 的阅读顺序 + `git status/diff/log -n 10`，回答"项目是什么/里程碑/任务/已完成/待办/约束/当前改动"；
- **VERIFY** 必须声明本次达到的验证级别（§24）：**L0** 静态 / **L1** 单元 / **L2** 集成 / **L3** 运行时 / **L4** 生产。本项目当前闭环：`$PY scripts/verify.py` = **L0+L1**；涉及真实网络/外发的 L2+ 验证需用户逐次授权；
- **No False Completion（§25）**：验收标准未全部有证据满足时，任务状态只能是 `READY_FOR_REVIEW` 或 `BLOCKED`，**不得标 COMPLETED**。"代码看起来没问题"不构成完成；
- **REVIEW（§26）**必须回答：*有没有实现了 Task 没要求的东西？*

## 12. 最小验证闭环（每次改码后）

```
ORIENT（读 STATE/Task）→ 修改代码 → $PY scripts/verify.py（L0+L1）
→ 按任务声明更高级别验证（真实外发先获用户授权）→ REVIEW（diff 是否越界）
→ RECORD（STATE.md / BACKLOG.md / 任务文件）→ HANDOFF
```

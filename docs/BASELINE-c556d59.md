# PROJECT BASELINE — c556d59（冻结快照）

> **冻结声明**：本文档是 commit **c556d59**（"chore: ignore local security artifacts"，2026-10-01，HEAD，工作区干净）的权威基线快照，由 TASK-008 建立。**冻结后本文不再修改**——此后任何架构/需求/路线变化一律通过 Task/ADR 记录；需要重建现状时，以本快照 + 其后的 ADR/Task/DEV_LOG 为准。
> **验证底座**：`scripts/verify.py` 3/3 PASS @ c556d59；无未提交业务改动。
> **快照可信度**：基于 2026-09-30 全量接管审计 + TASK-003..007 的逐文件验证（证据链见 docs/DEVELOPMENT_LOG.md）。

---

## 1. 真实架构（as-built @ c556d59）

### 1.1 链路状态

| 链路 | 状态 | 构成 |
|---|---|---|
| **watchdog（唯一活跃链路）** | ✅ 活跃 | **weather_monitor.py**（producer：多城市 watchdog，告警去重）→ **stdout**（integration boundary）→ **Hermes**（consumer / scheduler / transport——具体行为含 UNKNOWN，BL-016）→ **QQ**（delivery target） |
| 企业微信 WS（scheduled/once/listen/both） | 🔒 退役保留 | `main.py` → scheduler / push_service |
| legacy 整合脚本 | 🔒 退役保留（已去硬编码） | `qywx_websocket.py`、`wechat_weather.py` |
| 云部署 | 🔒 退役保留 | Railway（`railway.json`）、Render（`render.yaml`）——文件在库，账号侧不再使用 |

> **数据流方向（Gate Review 修正）**：告警内容流向为 **weather_monitor（producer）→ stdout（integration boundary）→ Hermes（consumer/scheduler/transport）→ QQ（delivery target）**；Hermes 对 producer 的"启动/调度"是控制流，不是数据流的反向。Hermes 具体行为（频率/重叠执行/stdout 消费/空输出/exit code/失败重试等）含 UNKNOWN（BL-016 → M3 Runtime Integration 核心）。

### 1.2 模块清单（一句话粒度，细节见 ARCHITECTURE.md）

- `weather_service.py`：和风 API 取数（实况/7d/24h/指数），多城市（CITY_SLUGS）
- `semantic_engine.py`：规则引擎（7 核心 + 9 默认 JSON + 用户规则；9 种条件类型；配置锚定项目根）
- `llm_service.py`：OpenAI 兼容调用 + 失败降级模板（当前 LLM_API_KEY 为占位符 → 实际持续走降级，见 §4 U-LLM）
- `push_service.py`：企业微信 WS 客户端（退役链路组件，保留在库；CERT_NONE 待 SEC-T3）
- `scheduler.py`：APScheduler 定时（退役链路组件，保留在库）
- `weather_state.py`：告警去重状态机（tag 指纹、原子落盘 `state/*.json`，gitignored）
- `weather_monitor.py`：活跃入口 / **producer**（多城市 → 规则 → 去重 → LLM → stdout；**不消费 WeCom 凭据**）

### 1.3 安全姿态 @ c556d59

| Finding | 状态 |
|---|---|
| SEC-01/07/08（凭据暴露） | **Historical Exposure = CONFIRMED；Credential Status = RETIRED/REVOKED；Compromise = UNKNOWN**（静态清理 ✅ + 平台失效 ✅；暴露窗口 77c705d 起至失效日；git 历史仍含旧值） |
| SEC-02/04/05/10 | FALSE POSITIVE 备案（SEC-10 附 LOW 加固建议） |
| SEC-03（response_url SSRF）/ SEC-06（WS 证书校验禁用） | TRUE POSITIVE，**退役路径可达**（仅路径重启时成立）；处置 PROPOSED：SEC-T2（BL-019）/ SEC-T3（BL-012） |
| R3 git 历史重写 | PROPOSED / Skip（退役+清理已使旧值失效） |

### 1.4 配置与持久化

- 环境配置：本地 `.env`（untracked）——含在用 HEFENG key、LLM 占位符、**已退役的 WeCom 凭据键值（LOW，未清理）**；
- 持久化：`state/weather_state.json`（运行时去重状态，gitignored）；
- 无数据库；无 CI/lint（M4 范畴）。

## 2. 需求状态快照（@ c556d59）

| REQ | 主题 | 状态 |
|---|---|---|
| REQ-001..005 | 取数/规则/LLM+降级/企微推送/定时工作流 | ACCEPTED（Historical）——RET 链路退役后 REQ-004/005 的实现保留在库，重启企微时可复活 |
| REQ-006 | 配置无硬编码 | **ACCEPTED**（原 CONFLICT 冲突已由 TASK-007 静态清理解除；git 历史残留 → R3 独立 PROPOSED） |
| REQ-007/008 | 日志 / 模块化 | ACCEPTED（Historical） |
| REQ-009 | 产品边界（Non-Goals） | ACCEPTED（WON'T 清单） |
| REQ-010 | @ 消息监听回复（listen/both） | ACCEPTED（Historical）——退役链路 |
| REQ-011..014 | watchdog 多监控/去重/stdout 契约/提前量 | **ACCEPTED**（ADR-015；测试 23 例在 verify.py 闭环） |
| REQ-015 | 部署路径 | **ACCEPTED**（U5 决议：主路径 = 本地 Hermes watchdog/QQ 推送；Railway/Render 退役；退役配置文件处置归 M3 收敛） |

## 3. 后续路线（自 c556d59 起）

| 优先级 | 事项 | 出处 |
|---|---|---|
| 立即 | **M2 终验收尾**：BL-014（README/WIKI 内容对齐，凭据部分已清）、BL-016 剩余（Hermes 调度频率/失败语义） | ROADMAP M2 |
| 次之 | **M3 Runtime Integration（核心）**：① Hermes integration contract/evidence——BL-016 七项 UNKNOWN（调度频率 / 是否允许重叠执行 / stdout 消费语义 / 空输出语义 / exit code 语义 / 失败重试语义 / 重试与去重关系）逐项取证；② 退役部署配置文件处置（railway.json/render.yaml 删除或标注退役）；③ README runtime 对齐 | ROADMAP M3 |
| 之后 | **M4 Reliability**：BL-006（lint/CI/pytest 化）、BL-003（三处变量构建合并）、BL-004（时区统一）、BL-001（损坏测试处置） | ROADMAP M4 |
| PROPOSED 池 | SEC-T2 response_url 加固（BL-019）、SEC-T3 WS 证书校验（BL-012）——仅路径重启时需要；R3 历史重写；LLM key 配置（运营决策）；Phase C（contracts/ 等） | BACKLOG / SECURITY-REVIEW |

**偏离政策**：自本快照起，任何架构变化、需求状态变化（PROPOSED→ACCEPTED、WON'T 调整）或路线调整必须对应 Task/ADR；本文件是 c556d59 的定格记录，不随演进改写。

## 4. 快照期 UNKNOWN 清单

| # | UNKNOWN | 状态 |
|---|---|---|
| U2 | 暴露窗口内凭据是否被第三方收集 | **永久 UNKNOWN**（已按最保守假设处置，不做断言） |
| U4 剩余 | Hermes 七项集成 UNKNOWN（调度频率/重叠执行/stdout 消费/空输出/exit code/失败重试/重试与去重关系） | **M3 Runtime Integration 核心（BL-016）**——Gate Review 修正：由 M2 尾巴升级为 M3 核心 |
| U6 | 和风自定义 host 来源 | 静态无证据，低影响 |
| U-LLM | LLM_API_KEY 为占位符 → LLM 功能实际未启用 | 运营决策（配置真实 key 即启用，无安全风险） |
| — | `.env` 中已退役 WeCom 凭据键值残留 | LOW（本地文件）；可在未来清理任务中移除 |

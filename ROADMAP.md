# ROADMAP — 里程碑（ADP-1.0 §8）

> 职责：回答"项目按什么顺序发展"。每个里程碑必须有 Objective / Scope / Exit Criteria。
> **基线冻结（TASK-008）**：项目基线冻结于 commit **c556d59**（docs/BASELINE-c556d59.md）——本路线自该基线起演进，偏离须走 Task/ADR。
> 状态：COMPLETED / IN_PROGRESS / BLOCKED / PLANNED。**Future 想法进 BACKLOG，不进本文**——不把愿望伪装成计划。
> 历史里程碑按仓库证据回填（TASK-000，2026-09-30）。

## M0 — Foundation · COMPLETED

- **Objective**: 打通"取数 → 推送"最小闭环（单脚本时代）。
- **Scope**: `wechat_weather.py`、`qywx_websocket.py`（均为 legacy，ADR-012 保留）。
- **Evidence**: git `77c705d`（Initial commit）至 `822dbba` 区间；`.trae/documents/weather_bot_schedule_plan.md`（当期计划）。
- 注：ADP 采纳前完成，Exit Criteria 不回溯补写。

## M1 — Core Weather Service · COMPLETED

- **Objective**: 模块化服务层 + 语义规则引擎 + LLM 生成 + 企业微信 WS 推送 + APScheduler 定时。
- **Scope**: REQ-001..008、REQ-010。
- **Evidence**: git `d01f1c3`（完成智能天气提醒系统）、`5ae1799`（整合功能单文件+LLM+websocket）、`dca395e`（时区修复收尾）；`services/*` 已提交；`.trae/specs/weather-alert-system/spec.md` AC-1..AC-5 对应实现。
- **Exit 核对**: 核心功能可运行 ✅（`scripts/verify.py` L0+L1 通过；真实推送验证未做，属 M4/运行授权范畴）。

## M2 — Watchdog · IN_PROGRESS

- **Objective**: 多城市天气监控 + 告警去重状态 + stdout 消息契约（REQ-011..014，**全部 PROPOSED**）。
- **Design**: docs/DESIGN-watchdog.md（TASK-002 逆向规格化产出，含缺陷处置与 AC——PROPOSED，批准后冻结为基准）。
- **Scope**: 未提交工作区——修改 6 文件（`.env.example`、`config/weather_rules_default.json`、`models/weather_types.py`、`services/{llm_service,semantic_engine,weather_service}.py`）+ 未跟踪（`weather_monitor.py`、`services/weather_state.py`、`state/`、`WIKI.md`）。
- **Exit Criteria**:
  - [x] 用户裁决 REQ-011..014 状态（✅ ACCEPTED，2026-09-30，ADR-015）
  - [x] 功能以独立 commit 入库（✅ checkpoint `feat: finalize watchdog implementation`，2026-09-30，hash 见 git log）
  - [x] `weather_state` 去重逻辑单元测试入库并入 `scripts/verify.py` 闭环（✅ test_watchdog.py 22 例，TASK-003）
  - [ ] README / ARCHITECTURE 与最终形态一致（ARCHITECTURE 已更新；README→BL-014，终验对齐）
  - [x] 无 P0/P1 已知缺陷（✅ D1 已修复、D2 已补测；D3/D4 经用户决定记录为接受风险；B1 属测试资产缺陷→BL-001）
- **Blockers**: 仅剩 commit 授权（Review 后）与 BL-014（终验内容对齐）；BL-016 已移入 M3 Runtime Integration 核心（Gate Review 修正）。

## M3 — Runtime Integration · IN_PROGRESS

- **Objective**: 为唯一活跃链路建立 **Hermes integration contract 与证据**（关闭 BL-016），并完成退役部署配置清理与 README runtime 对齐。Hermes integration 是本里程碑**核心项**，不是附属尾巴。
- **Scope**:
  1. **Hermes integration contract/evidence（核心）**——逐项取证并契约化 BL-016 七项 UNKNOWN：调度频率；是否允许重叠执行；stdout 消费语义；空输出语义；exit code 语义；失败/重试语义；重试与去重（weather_state）的关系。
  2. **Retired deployment configuration cleanup**——railway.json / render.yaml 删除或标注退役（需 ADR）。
  3. **README runtime alignment**——以 producer → stdout → Hermes → QQ 的规范方向重述活跃链路。
- **Exit Criteria**: BL-016 关闭（七项 UNKNOWN 全部有证据，或明确记录"不可得"及其影响）；退役配置处置完成（含 ADR）；README 与 BASELINE-c556d59 链路表述一致。
- **Blockers**: 需用户提供 Hermes 运行面信息，或授权运行期取证（L3）。

## M4 — Reliability · PLANNED

- **Objective**: 测试覆盖、凭据治理、验证体系升级。
- **Scope**: BACKLOG 中高优先项——BL-001（损坏测试）、BL-006（lint/typecheck/CI）、BL-007/008（语义引擎缺陷）、凭据处置完成后的清理任务（依赖 STATE.md §6-1 决策）。
- **Exit Criteria**: **启动本里程碑时定义**——现在写具体标准即违反"Future 不伪装成当前计划"。

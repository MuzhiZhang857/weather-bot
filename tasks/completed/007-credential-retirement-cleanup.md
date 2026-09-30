# TASK-007: Credential Retirement & Exposure Cleanup

- ID: TASK-007
- Status: COMPLETED
- Requirement: 用户直接指令（2026-09-30 TASK-007 任务书）；U5 运行面确认（Railway/Render/WeCom AI Bot/legacy webhook 均不再使用；Hermes 活跃用于 QQ 推送）
- Created: 2026-09-30

## Objective

按"废弃凭据撤销 + 静态暴露清理"策略处置 SEC-01/07/08：Agent 完成仓库静态清理（真实值 → 安全占位符/空默认值），用户完成平台侧旧值失效；SEC-01/07/08 的状态降级**等待平台侧失效确认**。

## Why

U5 确认 WeCom 链路整体退役、活跃路径为 Hermes→QQ 推送（不消费任何泄露凭据）→ 处置从"轮换+迁移"改为"废弃+清理"，不再需要配置新的生产 Secret。

## Evidence

- U5 运行面确认（用户提供，2026-09-30）
- TASK-005 资产清单 A1-A8（泄露位置与值状态：SECRET/BOT_ID/CHAT_ID 泄露值=在用值；HEFENG 泄露为旧值）
- docs/SECURITY-REVIEW.md SEC-01/07/08、docs/SECURITY-CREDENTIAL-REMEDIATION.md SEC-R1/R2

## Scope

### Included

- **执行计划**（本文件 §Execution Plan，四类责任划分）
- **Agent 侧静态清理**（本任务内执行）：README.md 4 行、WIKI.md 4 行占位符化；qywx_websocket.py 4 处 getenv 默认值清空；wechat_weather.py 2 处字面量改为 os.getenv（含补 import os）
- 离线验证（HEAD 树布尔扫描归零 + verify.py 回归）
- 安全文档状态更新（SECURITY-REVIEW / CREDENTIAL-REMEDIATION / ROTATION-PLAN / STATE / BACKLOG / DEV_LOG / HANDOFF）

### Excluded

- 平台侧操作（WeCom 应用停用/SECRET 重置、legacy webhook 对象处置、和风旧 key 禁用）——**用户亲自执行**
- 修改 `.env`、weather_monitor.py、Hermes 链路
- Git history rewrite（独立 PROPOSED 项）
- 修改当前在用 HEFENG key（除非另有暴露证据）
- push / 真实消息发送 / 创建后续任务

## Execution Plan（四类责任划分）

### P. 用户必须亲自完成的平台操作（本任务内**不执行**，PENDING）

| # | 操作 | 目标 | 完成后效果 |
|---|---|---|---|
| P1 | 企业微信管理后台：**停用/删除 AI Bot 应用**（或重置 Secret 且不再下发） | 使公开暴露的旧 SECRET 失效 | SEC-01 的"有效"成分解除 |
| P2 | 企业微信：处置 legacy webhook 对象（若后台仍存在对应群机器人/webhook） | 使 QYWX_WEBHOOK_KEY 别名失效 | SEC-07 的别名暴露失效 |
| P3 | 和风控制台：**禁用/删除旧 key**（wechat_weather.py:4 暴露的那枚） | 旧和风 key 失效 | SEC-01 的 HEFENG 成分失效 |
| P4 | 向 Agent 确认 P1-P3 完成 | 触发 SEC-01/07/08 降级为"历史暴露，凭据已失效" | 状态降级（SECURITY-REVIEW.md） |

### A. Agent 可以完成的仓库静态清理（本任务内执行）

| # | 文件 | 动作 |
|---|---|---|
| A1 | `README.md:136/137/142/159` | 凭据表值列 → `<YOUR_BOT_ID>` / `<YOUR_SECRET>` / `<YOUR_HEFENG_KEY>` / `<YOUR_CHAT_ID>` |
| A2 | `WIKI.md:274/275/282/291` | 同 A1（WIKI 保持不入库直至 BL-014） |
| A3 | `qywx_websocket.py:44/45/48/53` | getenv 默认值 → 空串（缺配置 fail-fast，退役路径不提供兜底凭据） |
| A4 | `wechat_weather.py:4/8` + `import os` | 字面量 → `os.getenv(名称, "")`（移除活凭据/旧 key 字面量） |

### V. 可离线验证项

| # | 验证 | 方法 |
|---|---|---|
| V1 | 工作树（tracked）中 4 类在用/旧值 0 命中 | 内存值 + `git grep -lF` → 文件名计数（预期 0） |
| V2 | WIKI.md 值列非占位符内容 = false | 布尔取证 |
| V3 | 占位符形如 `<YOUR_*>`，与真实值可稳定区分 | 取证模式核对 |
| V4 | legacy 修改后仍可编译、verify.py 全绿 | `scripts/verify.py` |

### N. 无法离线验证项

| # | 项 | 原因 |
|---|---|---|
| N1 | 平台侧旧值是否已失效（P1-P3 结果） | 需用户在平台确认并回告 |
| N2 | Compromise（凭据是否已被第三方收集） | 公开仓库 + 时间窗口，不可追溯 |
| N3 | 退役 WS/webhook 路径若被重新启用时的行为 | 需真实运行（退役路径，默认不做） |

## Acceptance Criteria

- [x] AC-1 静态清理完成：A1-A4 全部落地且 HEAD 工作树布尔扫描归零（V1/V2）
- [x] AC-2 legacy 修改后可编译、verify.py 3/3 PASS（V4）
- [x] AC-3 weather_monitor.py / Hermes 链路零改动
- [x] AC-4 SEC-01/07/08 在 SECURITY-REVIEW.md 标注"静态清理完成（TASK-007）；平台失效 PENDING"——**不降级**
- [x] AC-5 全程值零打印零复制（取证与 diff 均无值）
- [x] AC-6 未 push、未改 .env、未做历史重写

## Verification

V1-V4 离线验证 + `scripts/verify.py`（L0+L1+L2 offline 回归）。

## Risks

- legacy 脚本行为变化：缺 env 时不再有凭据兜底（fail-fast）——退役路径，可接受且为本任务目的
- 清理不消除 git 历史暴露——由 SEC-R3（PROPOSED）与 R1 平台失效共同兜底

## Dependencies

- 用户执行 P1-P3 后回告 → 才能降级 SEC-01/07/08（后续轻量更新，不新建任务）

## Completion Evidence

- **Finalization（2026-09-30）**：P1-P3 平台失效完成（用户确认）→ SEC-01/07/08 降级为 Historical Exposure CONFIRMED / Credential RETIRED/REVOKED / Compromise UNKNOWN（未做任何"未被攻击/访问/泄露"断言）；R3 维持 PROPOSED/Skip；Hermes QQ 推送链路未受影响（用户确认）。全部状态文档已收敛。
- Tests: `scripts/verify.py` → compile/semantic/watchdog 3/3 PASS，exit 0（legacy 修改后仍可编译）。
- Commands: V1 布尔扫描——SECRET/BOT_ID tracked 0 命中、SCHEDULE_CHAT_ID 初扫 1 命中（README.md:228 非表格日志示例）→ 补清后 **0 命中**；WIKI SECRET 在用值 0；V1b 结构检查——wechat_weather 字面量赋值 0 行、qywx 非空 getenv 默认值 0 行；V2 占位符 README/WIKI 各 4 处 `<YOUR_*>`；diff 计数核对（-1 字面量/+1 getenv 形式）。**所有命令与输出零值打印**。
- Git commit: 未提交（无授权，不自动 push）。
- Review: 待用户执行。Review 要点：①占位符形式（<YOUR_*>）是否可接受；②legacy getenv fail-fast 行为变化是否接受；③P1-P3 清单是否与平台后台实际对象对齐。

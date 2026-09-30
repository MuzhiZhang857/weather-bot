# SECURITY CREDENTIAL ROTATION PLAN — WeCom SECRET（PROPOSED）

> **文档地位**：TASK-006（2026-09-30）产出，细化 TASK-005 SEC-R1 中 WeCom SECRET 的轮换准备。状态 **PROPOSED**——本文是执行前的准备与计划，**不代表任何轮换已执行**。
> **凭据纪律**：全文以"文件:行号 + 变量名"指认，值零记录；新值只进密码管理器与环境变量，**永不入库**。
> **关联**：TASK-005（SEC-R1 全景）、docs/SECURITY-REVIEW.md（SEC-01/06/07/08）、BL-018/BL-016。
> **⚠️ U5 决议后状态（TASK-007，2026-09-30）**：Railway/Render/WeCom AI Bot/legacy webhook 均不再使用 → 本计划的 "Rotation=配置新生产 Secret" 部分**不再适用**；轮换目标收缩为**使旧值失效**（P1-P3 平台操作，见 TASK-007 Execution Plan）。本文件保留作为失效语义验证（§3.2-5）与回滚（§3.4）的参考。
> **执行收尾（2026-09-30）**：P1-P3 平台失效已完成（用户确认）——旧凭据按 RETIRED/REVOKED 记录，Compromise=UNKNOWN（不做断言）；"配置新生产 Secret" 仅在未来重新启用企微时按本计划框架重启。当前 Hermes QQ 推送链路未受影响（用户确认）。

---

## 1. WeCom SECRET 使用方清单（值零记录）

| # | 消费点 | 变量名 | 环境来源 | 消费方式 | 是否需要迁移 |
|---|---|---|---|---|---|
| C1 | `services/push_service.py:61`（`PushConfig.secret` → `subscribe_bot` 载荷） | `SECRET` | 进程环境：本地 `.env` / Railway / Render 变量 | WS 订阅认证（scheduled/once/listen/both 全模式） | **是**——轮换后所有活跃部署的环境变量需更新并重启进程 |
| C2 | `qywx_websocket.py:45`（`os.getenv("SECRET", <泄露的在用值>)`，消费于 `:176` 订阅载荷） | `SECRET` | 进程环境；**getenv 默认值即泄露的在用值**（SEC-07） | legacy 整合脚本的 WS 订阅（Render 启动命令指向此文件） | **是（条件）**——仅当 Render/legacy 路径保留时更新；同时按 SEC-R2 清理默认值 |
| C3 | `wechat_weather.py:8`（字面量 `QYWX_WEBHOOK_KEY`）消费于 `:105/:134`（`https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=<masked>` HTTP POST） | `QYWX_WEBHOOK_KEY` | **源码字面量**（非 env） | 群机器人 webhook 推送（legacy） | **独立凭据对象建模（Review Round 1 修正）**：与 AI Bot SECRET 是**两个独立对象**——历史源码字符串相同（TASK-005 取证 SAME）**不得推断轮换一个会自动撤销另一个**。legacy webhook 是否仍被使用 = **UNKNOWN（待用户确认）**：仍使用 → 需独立处置（轮换其群机器人 webhook key，非 AI Bot Secret）；已废弃 → 后续静态清理任务处理。**默认建议：随 legacy 下线，不迁移** |
| C4 | `weather_monitor.py` | — | — | **零依赖**（watchdog 不用 WS 凭据，取证 B 确认） | **否**——轮换对当前活跃路径零中断 |
| C5 | Hermes（外部调度器） | — | UNKNOWN | 按 ADR-007 仅消费 stdout，**大概率非 SECRET 消费方**；其调度环境是否携带变量不可知 | **UNKNOWN（BL-016）**——Before 段向用户确认 |

**结论**：轮换的**强制性迁移面 = C1（本地 .env + 活跃云平台）**；C2 取决于 legacy 处置决策；**C3 为独立凭据对象——其 key 不随 AI Bot SECRET 轮换自动失效，处置独立评估**；C4 零影响；C5 待确认。

## 2. 部署面确认（执行前必须逐项落定）

| 平台 | 库内证据 | 账号侧状态 | 轮换时动作 |
|---|---|---|---|
| Railway | `railway.json`（`main.py --mode both`） | **UNKNOWN**——变量在 Railway 控制台，离线不可知；项目是否仍活跃 UNKNOWN | Before 段确认活跃性；若活跃 → Rotation 后在控制台更新 `SECRET`（与 `BOT_ID` 保持配对） |
| Render | `render.yaml`（`qywx_websocket.py` legacy） | **UNKNOWN** | 同上；若活跃且决定保留 legacy → 更新变量 + 同步 SEC-R2 清理默认值 |
| 本地 `.env` | 存在且活跃（Hermes watchdog 日志证据；SECRET 键存在） | **CONFIRMED 活跃** | Rotation 后用户手工更新 `SECRET=<新值>`（不入库） |
| Hermes | 仅 stdout 契约（ADR-007） | **UNKNOWN（BL-016）** | 确认其不消费 SECRET；若其调度环境携带变量，纳入迁移清单 |

## 3. 轮换步骤设计

### 3.1 Before（轮换前，全部为准备/确认，不改任何值）

1. **部署面落定**：完成 §2 四项确认（Railway/Render 活跃性、Hermes 配置）——结果记入本文件 §2 表格与 DEVELOPMENT_LOG（无值）。
2. **使用方盘点收尾（U5）**：确认没有仓库之外的脚本/系统在用旧 SECRET（如个人自动化、其他机器的 .env 拷贝）；同时确认 **C3 legacy webhook 路径是否仍被使用**（UNKNOWN——决定其 key 走独立轮换还是随静态清理废弃）。
3. **备份**：
   - `.env` 当前版本复制到密码管理器/离线保险（仅取证与事故比对用——旧值轮换后即失效，**不要**作为回滚凭据使用）；
   - Railway/Render 变量清单导出存密码管理器；
   - `git status` 干净（本计划已入库）。
4. **窗口选择**：按最保守假设（重置后旧值**可能**立即失效——实际失效语义 UNKNOWN，见 §3.2-5）规划——WS 三模式（scheduled/once/listen/both）可能中断直至新值下发，选择低峰窗口（非推送时刻）；**watchdog 路径零依赖**，不受窗口约束。
5. **预案**：新值先存密码管理器；准备好 C1/C2 各环境的新值下发顺序（§3.3）。

### 3.2 Rotation（平台侧，用户操作）

1. 登录企业微信管理后台 → 应用管理 → 对应 AI Bot 应用；
2. 重置 Secret → 复制新值 → **立即存入密码管理器**（不落聊天记录/文档/剪贴板久留）；
3. 同一页面核对 BOT_ID 未变（对象标识，预期不变）；
4. 若 §1-C3 决定保留 legacy webhook 路径：在目标群添加/查看群机器人，获取**独立的** webhook key（与 AI Bot SECRET 是不同对象）；
5. **失效语义 = UNKNOWN（Review Round 1 修正）**：旧 Secret 在重置后是否立即失效、是否存在并存窗口，平台未提供充分证据——本文不得将其作为既定事实。规划按**最保守假设**安排窗口与下发顺序；**执行任务必须在重置后完成两项验证**：①新凭据生效（C1 订阅成功日志）；②旧凭据已失效（旧值订阅失败日志）——若平台侧无法验证旧值状态，在 DEVELOPMENT_LOG 明确记录"旧值失效状态无法验证"。

### 3.3 After（验证与收尾）

1. **新值下发**（按 §1 迁移列）：本地 `.env` 手工更新 → Railway/Render 控制台更新（若活跃）→ 重启对应进程/重新部署；
2. **验证（分级）**：
   - **L3-a（需授权）**：`main.py --mode once` → 日志出现订阅成功 + 推送成功；
   - **L3-b（需授权）**：`weather_monitor.py` 单次运行正常（验证零依赖路径不受牵连）；
   - **L0**：`grep` 确认新值未出现在任何 tracked/untracked 文件（布尔输出）；
   - **旧值失效验证（必做，Review Round 1）**：用旧值尝试订阅 → 记录结果（预期认证失败如 errcode 40001 族）；**若无法验证（如平台不支持旧值重试），必须在 DEVELOPMENT_LOG 明确记录"旧值失效状态无法验证"及其原因**。
3. **收尾记录**：DEVELOPMENT_LOG 记录轮换事件（日期/对象/影响窗口，无值）；SECURITY-REVIEW.md SEC-01/07/08 状态更新为 Rotated（原暴露 CONFIRMED PUBLIC，历史保留）。
4. **遗留**：SEC-R2 静态清理（README/WIKI/legacy 默认值）此时执行最稳妥（TASK-005 §SEC-R2）。

### 3.4 回滚方式

- **前提认知（Review Round 1 修正）**：重置后旧值的可用性 = **UNKNOWN**（失效语义未验证）。回滚策略因此**不假设"回到旧值"可行**，统一设计为**向前重置**：
- 若新值录入错误 → 重新执行一次重置获取全新值，按 §3.3 重发；
- 若新值在平台侧工作但某环境未更新导致该环境故障 → 补发该环境（§3.3-1）；
- **若执行中验证发现旧值仍有效（存在并存窗口）** → 如实记录该事实，并由用户决定是否需要平台侧进一步吊销动作；
- Before 段的备份与清单核对仍是唯一的"保险"（旧值本身不作为回滚凭据）。

## 4. 验收标准（全部 PROPOSED，待批准后生效）

- **AC-1**：§1 消费方清单与实际代码一致（`grep` 复核，值掩码）；未发现第 5 处消费点。
- **AC-2**：§2 四个部署面状态全部由用户确认落定（含 UNKNOWN 清零或显式保留）。
- **AC-3**：轮换执行后——C1 全部活跃环境以新值订阅成功（L3-a 日志证据）；旧值认证失败（可选验证）。
- **AC-4**：watchdog 路径轮换前后行为一致（L3-b）。
- **AC-5**：新值零入库（`git grep` 布尔 + status 无新增敏感文件）；DEVELOPMENT_LOG/HANDOFF 记录轮换事件（无值）。
- **AC-6**：SEC-R2 静态清理随轮换完成或明确排期（任务化）。

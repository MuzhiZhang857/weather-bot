# SECURITY CREDENTIAL REMEDIATION DESIGN — PROPOSED

> **文档地位**：TASK-005（2026-09-30）产出的凭据暴露处置方案设计。状态 **PROPOSED**——SEC-R1..R4 全部待批准；本文档**不代表任何轮换/清理/重写已执行**。
> **凭据纪律**：全文以"文件:行号 + 变量名"指认凭据，**不包含任何凭据值**。取证方法：泄露值与在用值（`.env`）的比对在 shell/Python 内存中完成，输出仅为 同/异 布尔与文件名（方法已在 TASK-005 声明并披露）。
> **事实基础**：SECURITY-REVIEW.md SEC-01/07/08 + U1 决议（仓库 **Public**，Exposure=CONFIRMED）；本文所有扫描基于 HEAD 树（d37ed3a）与工作区。
> **⚠️ U5 决议后的策略变更（TASK-007，2026-09-30）**：Railway/Render/WeCom AI Bot/legacy webhook 均不再使用，活跃链路 = Hermes（QQ 推送）。处置从"轮换 + 迁移"改为"**废弃凭据失效 + 静态暴露清理**"：SEC-R1 的"配置新生产 Secret"取消（除非未来重新启用企微），目标改为使旧值失效；SEC-R4 的迁移目标只剩本地 `.env`（watchdog 零 WS 依赖，实际无需变更）；SEC-R3 维持默认 Skip。SEC-R2 已由 TASK-007 执行（HEAD 工作树对在用/旧值 0 命中）。
> **执行收尾（2026-09-30，P1-P3 用户确认完成）**：SEC-R1 平台失效 ✅（AI Bot 停用/删除、legacy webhook 对象退役、和风旧 key 处置）；SEC-R2 ✅；SEC-R3 维持 PROPOSED/Skip；SEC-R4 收敛——活跃环境仅本地 `.env`（watchdog 链路）与 Hermes（QQ 推送），均不依赖已退役凭据，**Hermes QQ 推送链路未受影响（用户确认）**。最终状态：SEC-01/07/08 = Historical Exposure CONFIRMED / Credential RETIRED/REVOKED / Compromise UNKNOWN。

---

## 1. 暴露资产分类清单（值零记录）

### 1.1 凭据类

| # | 资产（变量名） | 暴露位置（文件:行号） | 暴露类型 | 值状态（关键事实） |
|---|---|---|---|---|
| A1 | **SECRET** | `qywx_websocket.py:45`（getenv 默认值）；`wechat_weather.py:8`（字面量，变量名 QYWX_WEBHOOK_KEY——**同一字符串的别名暴露**）；`README.md:137`（文档示例值）；`WIKI.md:275`（未跟踪） | getenv 默认值 / 源码字面量 / 文档示例 | **泄露值 = 在用值（SAME）→ 活凭据对互联网公开** |
| A2 | **BOT_ID** | `qywx_websocket.py:44`；`README.md:136`；`WIKI.md:274` | getenv 默认值 / 文档示例值 | 泄露值 = 在用值（SAME）。标识符非密钥，但与 A1 组合成完整凭证 |
| A3 | **HEFENG_API_KEY** | `wechat_weather.py:4`（字面量） | 源码字面量 | 泄露值 ≠ 在用值（**DIFFER**）→ 暴露的是**旧 key**（存活状态 UNKNOWN，U5）；**当前在用的和风 key 未暴露** |
| A4 | **SCHEDULE_CHAT_ID** | `qywx_websocket.py:53`；`README.md:159`；`WIKI.md:291` | getenv 默认值 / 文档示例值 | 泄露值 = 在用值（SAME）。**会话标识符，不可轮换**——单独泄露仅在与有效凭据配对时可被利用 |

### 1.2 其他可能敏感配置

| # | 资产 | 位置 | 敏感度 | 说明 |
|---|---|---|---|---|
| A5 | QWeather 自定义 host | `weather_service.py:24`（tracked） | LOW | 非凭据；端点隐私。随 SEC-T1 清理一并评估是否泛化 |
| A6 | CITY_ID / CITY_NAME | wechat_weather.py:5/6、qywx_websocket.py:46/47、README、WIKI | LOW | 隐私：暴露监控城市（呼和浩特/包头），无滥用路径 |
| A7 | LLM_API_KEY | `.env`（在用值）、`README.md:149`、`WIKI.md:298` | **无真实暴露** | 布尔取证：在用值为 **7 字符占位符形态**（非真实密钥）；README/WIKI 命中的是同一占位符示例 → 对照组通过 |
| A8 | `.env` 本身 | untracked（.gitignore 覆盖）✅ | — | 全部在用值的唯一载体，未泄露 |

### 1.3 附带发现（INFORMATIONAL，INFERENCE）

A7 表明 `.env` 中的 LLM_API_KEY 为占位符 → **LLM 文案生成当前实际不可用，每次调用必然失败并走降级模板**（llm_service 降级路径，ADR-005）。若需要真实 LLM 文案，用户应在 `.env` 配置真实 key（该操作不在本任务范围，且无暴露风险——.env 不入库）。

## 2. 影响分析（四维）

### 2.1 Git 当前 HEAD
SECRET/BOT_ID/SCHEDULE_CHAT_ID 的**在用值**存在于 3 个 tracked 文件（README + 两个 legacy 脚本）；HEFENG 旧值存在于 1 个 tracked 文件。任何 `git clone` 即获得全部在用凭据。

### 2.2 Git 历史
三个文件自 `77c705d`（Initial commit）起**每个历史版本都含这些值**——即使未来 HEAD 清理完成，历史仍可回溯。历史深度 = 全部提交（~26 个）。见 SEC-R3 评估。

### 2.3 Public repository 可见性
仓库 **Public**（U1 决议，2026-09-30）→ Exposure = **CONFIRMED**：任意互联网用户/自动化爬虫可读取。注意：GitHub secret scanning 对 WeCom AI Bot 自定义凭据**无自动识别/撤销机制**（覆盖主流 token 类型），因此不会有平台侧告警——暴露是**静默**的。被第三方收集的时间与事实 **Compromise = UNKNOWN**。

### 2.4 部署环境影响
| 环境 | 是否使用泄露值 | 轮换影响 |
|---|---|---|
| 本地 `.env`（Hermes watchdog，**当前活跃路径**） | **是（SAME 实证）** | 轮换后必须更新 `.env`，否则 watchdog 的 WS 依赖项失效（watchdog 本身不用 SECRET，**零中断**；受影响的是 scheduled/listen 模式） |
| Railway（活跃性 UNKNOWN） | 若配置同值则受影响 | 需在控制台同步更新（SEC-R4 清单项） |
| Render（活跃性 UNKNOWN，启动命令指向 legacy） | legacy 硬编码值=在用值 | 轮换后 **legacy 脚本内字面量必须同步更新**（或该路径下线） |
| 未知第三方 | 若已收集泄露值 | 轮换使其失效——这是唯一可靠的"撤销"手段 |

## 3. 修复方案设计（全部 PROPOSED）

### SEC-R1 平台侧凭据轮换方案（最高优先，用户平台操作）
- **前置**：U5 盘点——确认旧凭据是否仍有未知使用方（避免轮换导致未知系统中断）。
- **对象与动作**：
  1. **SECRET**（企业微信 AI Bot）：管理后台重置。**旧值失效语义 UNKNOWN（Review Round 1 修正，详见 ROTATION-PLAN §3.2-5）**——重置后是否立即失效/是否存在并存窗口未经平台证据确认；执行时必须验证新值生效与旧值失效状态（或明确记录无法验证）。
  2. **HEFENG 旧 key**（wechat_weather.py:4 暴露的那枚）：和风控制台**删除/禁用**（可能早已失效；删除无害）。当前在用 key 未暴露，**无需轮换**。
  3. **BOT_ID**：对象标识，不轮换；风险由 1 覆盖。
  4. **SCHEDULE_CHAT_ID**：会话标识，**不可轮换**；如需彻底隔离可迁移群（产品决策，PROPOSED，默认不动）。
- **顺序**：轮换 → SEC-R2 清理 → SEC-R4 环境更新 → 验证。
- **影响窗口**：WeCom SECRET 重置后，scheduled/listen/both 模式需更新环境变量后重启；watchdog 路径零中断。

### SEC-R2 代码/文档清理方案（轮换完成后执行）
| 位置 | 动作 |
|---|---|
| `README.md:136/137/142/159` | 值列替换为 `<YOUR_BOT_ID>` / `<YOUR_SECRET>` / `<YOUR_HEFENG_KEY>` / `<YOUR_CHAT_ID>` |
| `qywx_websocket.py:44/45/48/53` | getenv 第二参数改为空串 + 缺配置时 fail-fast |
| `wechat_weather.py:4/8` | 随 legacy 处置决策：删除文件或同样清空 |
| `WIKI.md:274/275/282/291` | 值列占位符化后**方可**入库（BL-014 前置） |
- **注意**：清理只消除 HEAD 静态暴露，**历史仍在**——真正的失效靠 R1 轮换，因此 R2 必须在 R1 之后（否则清理动作本身提醒扫描者"这里曾有活凭据"且旧值依然有效）。

### SEC-R3 Git history 是否需要 rewrite 的评估
- **建议（PROPOSED）**：**Skip**。理由：①轮换后旧值全部失效，历史残留的字符串不再可用；②重写是破坏性操作（force push、fork 失效——仓库存在已知 fork MuzhiZhang857/*、协作者克隆断裂）；③收益仅剩"历史整洁"。
- **例外**：若用户有合规要求必须抹除，或确认无法轮换某凭据（如 SCHEDULE_CHAT_ID 类不可轮换标识符，其历史暴露无法通过轮换消除——但该标识符单独无害），再单独立项。
- **若执行**：`git filter-repo --replace-text`（值 → `<REDACTED>`）→ 先 `git bundle create backup.bundle --all` → force push → 通知 fork 持有者 → 全员重新克隆。
- **Compatibility Risk**：所有克隆失效、GitHub PR/issue 引用漂移、fork 永久分叉。

### SEC-R4 部署环境变量迁移方案
- **环境清单**（核对用）：①本地 `.env`（活跃）②Railway 变量（活跃性 UNKNOWN，先确认）③Render 变量（活跃性 UNKNOWN）④Hermes 侧配置（若存在独立配置，UNKNOWN——BL-016）。
- **动作**：轮换完成后，把新 SECRET 更新到①②③④中所有确认活跃的环境；HEFENG 在用 key 不变（未泄露）；BOT_ID/CHAT_ID 不变。
- **原则**：新值只进环境变量/密钥存储，**永不入库**（本设计不改变该原则）。

## 4. 风险与回滚方案

| 方案 | 主要风险 | 回滚 |
|---|---|---|
| SEC-R1 轮换 | 旧值失效语义 UNKNOWN（规划按"可能立即失效"做保守假设）→ 使用旧值的环境**可能**中断（scheduled/listen 模式、未知第三方使用方 U5）；重置动作不可回退到旧值 | **向前重置**设计（详见 ROTATION-PLAN §3.4）：U5 盘点完成；新值先行存入密码管理器；低峰窗口执行；执行后验证新值生效与旧值失效状态（或记录无法验证）；和风侧可"先建新 key 验证、后删旧 key"平滑过渡 |
| SEC-R2 清理 | 极低——纯文档/默认值变更 | `git revert` 对应清理 commit |
| SEC-R3 重写 | 破坏性最高：fork/克隆/引用断裂 | 执行前 `git bundle create backup.bundle --all`；从 bundle 恢复 |
| SEC-R4 迁移 | 环境遗漏导致某环境仍用旧值（轮换后即故障） | AC-4 的环境清单逐一核对；漏项按告警日志定位 |

## 5. Acceptance Criteria（全部 PROPOSED，待批准后生效）

- **AC-R1-1**：旧 SECRET 在 WeCom 平台认证失败（用户平台侧确认）；新 SECRET 在 .env 与全部活跃部署环境生效。
- **AC-R1-2**：旧 HEFENG key 已在和风控制台禁用/删除（用户确认）；当前在用 key 保持有效（watchdog 不中断）。
- **AC-R1-3**：L3 实测——`main.py --mode once` 以新凭据成功推送（待用户授权执行）。
- **AC-R2-1**：布尔取证——README/WIKI 凭据表值列非占位符内容 = false；legacy 两文件 getenv 默认值非占位符字面量 = false。
- **AC-R2-2**：新占位符形如 `<YOUR_...>`，与真实值模式（长度/字符集）可区分，取证命令可稳定判定。
- **AC-R3-1**（仅当执行重写）：`git grep <旧值> $(git rev-list --all)` 计数 = 0（布尔输出），且 `backup.bundle` 存在。
- **AC-R4-1**：环境清单（§SEC-R4）逐一核对并记录于 DEVELOPMENT_LOG（无值）。
- **AC-G-1**：全程无凭据值进入任何输出/文档/commit。
- **AC-G-2**：SEC-R1 完成后，SECURITY-REVIEW.md 的 SEC-01/07/08 Exposure 状态更新为 "Rotated（原暴露 CONFIRMED PUBLIC）"，Compromise 历史记录保留。

## 6. 执行顺序总览（批准后）

```
U5 盘点使用方（用户）
  → SEC-R1 轮换（WeCom SECRET 重置；和风旧 key 禁用）
  → SEC-R2 静态清理（README/WIKI/legacy）
  → SEC-R4 环境更新（.env + 活跃平台）
  → L3 验证（AC-R1-3）
  → SEC-R3 决策（默认 Skip，记录 ADR）
```

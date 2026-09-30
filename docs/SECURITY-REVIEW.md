# SECURITY REVIEW — 安全基线与修复设计（PROPOSED）

> **文档地位**：TASK-004（2026-09-30）产出的安全事实基线、风险建模与修复设计。状态 **PROPOSED**——所有需要产品行为变化、协议限制、凭据轮换、legacy 删除或扫描器配置变化的事项均待用户批准；本文档**不代表任何修复已实施**。
> **凭据纪律**：全文以"文件:行号 + 变量名"指认凭据，**不包含任何凭据值**（取证命令仅输出行号/计数/布尔值，见 TASK-004）。
> **方法边界**：纯静态代码阅读 + 离线取证。未做动态验证（无真实 callback 样本、无 MITM 演示、无网络探测）；凡静态无法确认的均标 UNKNOWN。

---

## 1. 攻击面总览（Entry Points 与信任边界）

| 入口 | 通道 | 输入来源 | 信任边界 |

> **U5 决议（2026-09-30，用户提供）**：Railway/Render/WeCom AI Bot/legacy webhook **均不再使用**；当前活跃链路 = **Hermes（QQ 推送）+ weather_monitor（不消费 WeCom 凭据）**。因此 WS 三模式与 legacy webhook 为**退役路径**——SEC-03/SEC-06 的可达性仅在退役路径被重新启用时成立；静态凭据暴露（SEC-01/07/08）与链路退役无关，仍按下方各条处置。
|---|---|---|---|
| 企业微信 WS（scheduled/listen/both） | `wss://openws.work.weixin.qq.com`，**证书校验被禁用**（SEC-06） | 平台回调（aibot_msg_callback：文本 + response_url） | 平台名义可信；**传输层不可信（无证书校验）→ on-path 攻击者可注入/篡改** |
| response_url webhook 回复 | HTTP POST（`main.py:110`） | 平台下发 URL（外部影响） | 无校验（SEC-03） |
| watchdog stdout | 文件外通道 | 规则引擎 + LLM 输出 | 由仓库外 Hermes 消费（不在本文范围） |
| LLM API | HTTPS POST（`llm_service.py:148`） | 运营者配置的 `LLM_BASE_URL` | 证书校验开启 ✅；URL 为配置面输入（SEC-10，低危） |
| 天气 API | HTTPS GET（`weather_service.py:85`） | 硬编码 base_url + 内部 endpoint | 证书校验开启 ✅；无外部可控成分（SEC-04，FP） |
| legacy 脚本 | CLI 直接运行（无导入方） | 无 | 不在活跃路径；风险为**静态暴露**而非运行时（SEC-01/02/07） |

**最可信攻击链（本评审核心结论）**：
```
push_service 禁用证书校验（SEC-06）
   ↓ on-path 攻击者可 MITM WebSocket
注入伪造 aibot_msg_callback（任意 response_url + 文本）
   ↓
main.py:110 无校验 POST 任意 URL（SEC-03，SSRF）
   + 伪造订阅状态下的消息代发
```
两个环节均修复前，此链可达性取决于攻击者能否处于网络路径上（云主机内网/局域网）。

## 2. Finding 登记册

### SEC-01 legacy 脚本硬编码凭据字面量
- **Evidence**: `wechat_weather.py:4`（HEFENG_API_KEY）、`:8`（QYWX_WEBHOOK_KEY）；布尔取证：两处均为**非占位符字面量 = true**。文件自 `77c705d`（Initial commit）即在库。
- **Classification**: **TRUE POSITIVE + HISTORICAL RISK**
- **Reachability**: 零导入方（取证 D）；仅当有人手动运行该脚本时被使用。真正的暴露面是**仓库与 git 历史**（自首次提交即存在）。**Exposure = CONFIRMED（2026-09-30 用户确认仓库为 Public，U1）→ 凭据对互联网公开**；Compromise = UNKNOWN（无法离线判定是否已被第三方获取，仅轮换可消除）。
- **处置状态（TASK-007 Finalization，2026-09-30）**：静态清理 ✅（HEAD 工作树 0 命中）；平台失效 ✅（P1 完成，用户确认）。
- **最终状态**：**Historical Exposure = CONFIRMED；Credential Status = RETIRED/REVOKED；Compromise = UNKNOWN**（暴露窗口：77c705d 起至失效日；窗口内是否被第三方获取无法验证，本文不做任何相关断言）。
- **Impact**: 持有者可消耗和风天气配额（HEFENG key）、以机器人身份向目标群发消息（QYWX webhook key）。无数据窃取路径。**仓库公开使"持有者"扩展为任意互联网用户，轮换紧急度：最高。**
- **Existing Controls**: 无（.gitignore 只覆盖 .env，不覆盖源码字面量）。
- **Proposed Remediation**（→ SEC-T1，PROPOSED）: ①用户在对应平台**轮换**两枚凭据；②轮换后清理 wechat_weather.py 字面量（替换 env 读取或随 legacy 删除决策一并处理）；③git 历史是否重写单独立项（破坏性操作，默认不建议）。**对象建模修正（Review Round 1，TASK-006）**：`QYWX_WEBHOOK_KEY` 与 AI Bot SECRET 建模为**两个独立凭据对象**——历史字符串相同不构成"轮换一个即自动撤销另一个"的依据；legacy webhook 使用状态 UNKNOWN（待用户确认），仍使用则需独立轮换其 webhook key。
- **Compatibility Risk**: 轮换会使旧值失效——若仍有未知系统使用旧值（UNKNOWN）会中断；需用户确认凭据使用方清单。
- **Acceptance Criteria**: 取证模式（非占位符布尔检查）对 wechat_weather.py 返回 false；轮换记录进入 DEVELOPMENT_LOG（不含值）。
- **Verification Method**: 离线 grep 布尔命令（同 TASK-004 取证模式）；轮换有效性由用户在平台侧确认。

### SEC-02 wechat_weather.py SSRF ×4（Mimosa L3）
- **Evidence**: `wechat_weather.py:13/35/55/134`——`requests.get/post(url, ...)`，url 均为**模块内硬编码常量**（和风/QYWX API 端点），无外部输入进入 URL。
- **Classification**: **FALSE POSITIVE**（启发式："带变量的 HTTP 调用"模式）
- **Reachability**: 无（无攻击者可控 URL 输入路径；脚本无服务端接口）。
- **Impact**: N/A。
- **Existing Controls**: N/A。
- **Proposed Remediation**: 无需修复。随 SEC-T1/legacy 处置自然消解。
- **Compatibility Risk**: 无。
- **Acceptance Criteria**: 分类复核记录在案（本文档）；不新增代码。
- **Verification Method**: 人工代码阅读（URL 来源全静态）+ 本登记册。

### SEC-03 response_url SSRF（main.py:110）
- **Evidence**: `main.py:100-116`：`response_url = message_body.get("response_url", "")`（平台回调体，**外部影响输入**）→ `requests.post(response_url, json=payload, timeout=10)`，无 scheme/host 校验，requests 默认**跟随重定向**。
- **Classification**: **TRUE POSITIVE**（外部影响的 URL 作为请求目标 = 真实 SSRF sink）
- **Reachability**: 仅 listen/both 模式。攻击前提：①on-path MITM（因 SEC-06 可行）或 ②平台侧被攻破/伪造回调。直接从公网不可达（WS 由客户端向平台建立，无入站端口）。
- **Impact**: 盲 SSRF——可自托管主机向任意 URL（含内网/云元数据地址）POST markdown 内容；配合重定向可绕过简单防护。不直接返回响应体给攻击者。
- **Existing Controls**: 仅 10s 超时；无 scheme/host/IP 校验；重定向默认开启。
- **Proposed Remediation**（→ SEC-T2，PROPOSED）: ①scheme 白名单（仅 https）；②host 精确白名单（平台域名，经 env `RESPONSE_URL_ALLOWED_HOSTS` 可配，默认保守值）；③解析后拒绝私有/环回/链路本地/保留地址（`ipaddress` 库）；④`allow_redirects=False`；⑤拒绝时 warning 日志。**allowlist 初值需一次真实 callback 样本确认（L3，待用户授权）**。
- **Compatibility Risk**: 若平台实际下发域名与白名单假设不符 → 回复功能中断；缓解：白名单可配置 + 拒绝日志可观测 + 分阶段上线（先告警后阻断）。
- **Acceptance Criteria**: L1 测试——https+白名单内通过；http 拒绝；解析为私有/环回地址拒绝；重定向不跟随；拒绝产生日志；既有正常回复路径不回归。
- **Verification Method**: L1（mock getaddrinfo + redirect 断言）；L3 真实消息回复（待用户授权，属后续任务）。

### SEC-04 weather_service.py:85 URL 拼接（Mimosa L3）
- **Evidence**: `weather_service.py:80-97`：`url = f"{self.base_url}{endpoint}"`，base_url 为硬编码常量，endpoint 为内部字面量；location/key 经 query 参数（非路径拼接）。
- **Classification**: **FALSE POSITIVE**
- **Reachability**: 无外部可控 URL 成分。
- **Impact**: N/A。
- **Existing Controls**: HTTPS 默认证书校验 ✅。
- **Proposed Remediation**: 无需修复。
- **Compatibility Risk**: 无。
- **Acceptance Criteria**: 分类记录在案。
- **Verification Method**: 代码阅读（base_url/endpoint 全静态）。

### SEC-05 weather_state.py os.replace 路径（Mimosa L3）
- **Evidence**: `weather_state.py:77-86`：`tmp = state_path + ".tmp"` → `os.replace(tmp, state_path)`；state_path 默认由 `__file__` 定位（固定），构造参数仅测试注入临时路径。
- **Classification**: **FALSE POSITIVE**
- **Reachability**: 无外部输入可达该路径。
- **Impact**: N/A。
- **Existing Controls**: 原子写本身是完整性控制（ADR-008）。
- **Proposed Remediation**: 无需修复。
- **Compatibility Risk**: 无。
- **Acceptance Criteria**: 分类记录在案。
- **Verification Method**: 代码阅读 + 调用方清单（仅 weather_monitor.py 与测试）。

### SEC-06 WebSocket 证书校验禁用
- **Evidence**: `services/push_service.py:128`（`sslopt={"cert_reqs": ssl.CERT_NONE}`）、`qywx_websocket.py:291`（同模式）；订阅载荷含 bot_id 与 secret（`push_service.py:142-152`）。
- **Classification**: **TRUE POSITIVE**
- **Reachability**: 全部 WS 模式（scheduled/listen/both + legacy）。攻击前提：on-path 位置（云网络内、本机局域网）。
- **Impact**: ①MITM 可截获**订阅载荷中的 bot_id/secret**（凭据泄露）；②注入伪造回调 → 打通 SEC-03 SSRF 链；③伪造消息代发。这是全项目最严重的单点。
- **Existing Controls**: 无（禁用是显式代码决策，无 ADR 记录理由；仅 BL-012 挂账）。
- **Proposed Remediation**（→ SEC-T3，PROPOSED）: 移除 CERT_NONE，恢复默认证书校验并实测平台端点；若 CA 链失败，正解是**证书固定（pinning）而非重新禁用**。
- **Compatibility Risk**: 容器 CA 存储缺平台中间证书会导致连接失败——需在 Railway + 本地各实测一次（L3，待授权）；失败时的 pinning 方案复杂度中等。
- **Acceptance Criteria**: 两文件 sslopt 不再含 CERT_NONE；真实环境订阅成功（L3）；`grep CERT_NONE` 计数为 0。
- **Verification Method**: L0 grep + L3 真实连接（待用户授权）。

### SEC-07 legacy 脚本 getenv 凭据默认值
- **Evidence**: `qywx_websocket.py:44/45/48/53`：BOT_ID / SECRET / HEFENG_API_KEY / SCHEDULE_CHAT_ID 以 `os.getenv(名称, "<真实值>")` 形式携带非占位符默认值；自 `77c705d` 在库。
- **Classification**: **TRUE POSITIVE + HISTORICAL RISK**
- **Reachability/Impact**: 同 SEC-01（静态暴露面）；且该脚本曾是 Render 启动入口，历史部署曾真实使用这些值。**Exposure = CONFIRMED PUBLIC（U1，2026-09-30）→ 互联网公开**；Compromise = UNKNOWN。
- **处置状态（TASK-007 Finalization，2026-09-30）**：静态清理 ✅（getenv 默认值已清空，HEAD 0 命中）；平台失效 ✅（P1/P2 完成，用户确认）。
- **最终状态**：**Historical Exposure = CONFIRMED；Credential Status = RETIRED/REVOKED；Compromise = UNKNOWN**。
- **Existing Controls**: 无。
- **Proposed Remediation**（→ SEC-T1）: 轮换后清理默认值（改为空串默认 + 缺配置即退出）。
- **Compatibility Risk**: 同 SEC-01（旧值使用方 UNKNOWN）。
- **Acceptance Criteria**: 四处 getenv 第二参数为空或占位符（布尔取证）。
- **Verification Method**: 离线 grep 布尔命令。

### SEC-08 README.md 凭据表（已提交）
- **Evidence**: `README.md:136/137/142/159` 凭据表"示例值"列含非占位符内容；自 `77c705d` 在库。
- **Classification**: **TRUE POSITIVE + HISTORICAL RISK**
- **Reachability**: **Exposure = CONFIRMED PUBLIC（U1，2026-09-30：仓库为 Public）→ 凭据对互联网公开**；Compromise = UNKNOWN。
- **处置状态（TASK-007 Finalization，2026-09-30）**：README 占位符化 ✅；平台失效 ✅（P3 完成，用户确认：旧 key 已处置，在用 key 未动）。
- **最终状态**：**Historical Exposure = CONFIRMED；Credential Status = RETIRED/REVOKED；Compromise = UNKNOWN**。
- **Impact**: 同 SEC-01/07。
- **Existing Controls**: 无（STATE §6-1 挂账，TASK-003 曾因 WIKI 同类问题将 WIKI 排除出提交）。
- **Proposed Remediation**（→ SEC-T1）: 轮换 → README 表格替换占位符 → 历史重写单独决策（PROPOSED）。
- **Compatibility Risk**: 文档可用性下降（示例值变占位符）——可接受；轮换使用方风险同 SEC-01。
- **Acceptance Criteria**: README 四行值列为占位符（布尔取证）。
- **Verification Method**: 离线 grep 布尔命令。

### SEC-09 WIKI.md 凭据表（未跟踪文件）
- **Evidence**: `WIKI.md:274/275/282/291` 凭据表值列含非占位符内容（布尔取证 = true）。文件当前未跟踪（TASK-003 checkpoint 已将其排除出提交，BL-014 记录脱敏前置）。
- **Classification**: **TRUE POSITIVE**（暴露面受限：仅本机磁盘）
- **Reachability**: 本机；一旦被 `git add`/共享即扩大（TASK-003 曾依赖人工门禁拦截——**该门禁不是持久控制**）。
- **Impact**: 同 SEC-01 家族。
- **Existing Controls**: 唯一防线是"记得别提交"（流程性，不可靠）；BL-014 已注记。
- **Proposed Remediation**（→ SEC-T1）: WIKI 脱敏（值列占位符化）后再入库；或保持不入库直至 SEC-T1 完成。
- **Compatibility Risk**: 无（文档脱敏不影响功能）。
- **Acceptance Criteria**: WIKI 凭据表值列布尔取证 = false（无非占位符内容）。
- **Verification Method**: 离线 grep 布尔命令。

### SEC-10 LLM_BASE_URL 无 scheme 校验
- **Evidence**: `llm_service.py:17/148`：base_url 取自 env，直接拼接调用；未校验 scheme。
- **Classification**: **FALSE POSITIVE**（URL 为运营者配置面输入，非攻击者输入）+ **LOW 加固建议**
- **Reachability**: 需要能改 `.env`/部署配置（等同已获主机控制）。
- **Impact**: 运营者误配 http:// 时 Bearer key 明文出网。
- **Existing Controls**: 依赖运营者正确配置。
- **Proposed Remediation**（LOW，PROPOSED）: 启动时校验 `LLM_BASE_URL` 以 https:// 开头，否则 warning（不阻断——保持降级路径）。
- **Compatibility Risk**: 无。
- **Acceptance Criteria**: 配 http:// 时日志出现 warning。
- **Verification Method**: L1 单测。

## 3. 分类汇总

| 分类 | Findings |
|---|---|
| TRUE POSITIVE | SEC-01（+历史）、SEC-03、SEC-06、SEC-07（+历史）、SEC-08（+历史）、SEC-09 |
| FALSE POSITIVE | SEC-02、SEC-04、SEC-05、SEC-10 |
| HISTORICAL RISK | SEC-01、SEC-07、SEC-08（均在库自初始提交） |
| UNKNOWN | ~~仓库可见性~~（→ 已确认 Public，2026-09-30）；凭据是否已被滥用（Compromise）；Hermes 安全姿态；response_url 真实样本域名 |

> **U1 决议（2026-09-30，用户提供）**：Repository Visibility = **Public**。据此 SEC-01/07/08 的 **Exposure = CONFIRMED**（互联网公开，自 77c705d 起持续至今），**Compromise = UNKNOWN**（是否已被第三方获取无法离线验证）。含义：这组凭据必须视为已泄露处理——**轮换（SEC-T1 第①步）从"建议"升级为"最高优先"，其余清理步骤均以轮换为前置**。本升级不改变任何修复设计的内容，只改变紧急度。
> **TASK-007 Finalization（2026-09-30）**：U5 决议后策略改为退役；静态清理 ✅ + 平台失效 ✅（P1-P3）→ **SEC-01/07/08 最终状态 = Historical Exposure CONFIRMED / Credential RETIRED/REVOKED / Compromise UNKNOWN**（不就第三方访问/攻击/泄露做任何断言）。SEC-R3 历史重写维持 PROPOSED/Skip。

## 4. 修复设计（全部 PROPOSED，待批准后各自立项）

### SEC-T1 凭据轮换与静态清理（依赖用户平台操作）
- **顺序**：①用户在微信企业微信后台 + 和风控制台轮换全部受影响凭据（SEC-01/07/08/09 同源值视为一组）→ ②清理仓库静态暴露（README/WIKI 占位符化；legacy 两文件默认值清空或按 legacy 决策删除）→ ③历史重写**单独立项**（破坏性 + force push，默认不建议，除非确认仓库 public）。
- **AC（汇总）**：SEC-01/07/08/09 的布尔取证全部转 false；轮换事件记录 DEVELOPMENT_LOG（无值）。
- **验证**：离线 grep 布尔命令 + 平台侧用户确认。

### SEC-T2 response_url SSRF 加固（main.py 修改，PROPOSED）
- **设计**：见 SEC-03 Proposed Remediation（scheme 白名单 + host 白名单可配 + 私有地址拒绝 + 禁重定向 + 拒绝日志）。
- **AC**：见 SEC-03（L1 五项断言 + 既有回复路径不回归）。
- **验证**：L1 mock 测试；L3 真实消息（待授权）。

### SEC-T3 WS 证书校验恢复（push_service + legacy，PROPOSED；BL-012 落地）
- **设计**：见 SEC-06。失败时走 pinning 而非禁用。
- **AC**：见 SEC-06。
- **验证**：L0 grep + L3 真实连接（待授权）。

### 不予行动项（FP 备案）
SEC-02 / SEC-04 / SEC-05：复核为误报，无行动；SEC-10：LOW 建议，可搭车任意后续任务。

## 5. Unknowns（解决所需证据）

| # | UNKNOWN | 所需证据 |
|---|---|---|
| U1 | ~~GitHub 仓库 public/private~~ | **已决议（2026-09-30）**：用户确认 **Public** → SEC-01/07/08 Exposure = CONFIRMED，Compromise = UNKNOWN |
| U2 | 暴露窗口内凭据是否被第三方收集/滥用 | **永久 UNKNOWN**——不可追溯；已按最保守假设处置（退役 + 清理）。本文不就结果做断言 |
| U3 | response_url 真实样本（域名/格式） | 一次真实 @ 消息的脱敏日志（L3，待授权） |
| U4 | 平台 WS 端点 CA 链是否被容器 CA 信任 | SEC-T3 实测（L3，待授权） |
| U5 | 旧凭据是否仍有未知使用方 | 用户盘点（轮换前完成，避免中断） |
| U6 | Hermes 安全姿态 | BL-016 |

# STATE — 项目当前状态（动态文件）

> **维护规则**：任何 Agent 完成重要工作后必须更新本文件对应小节（最近修改 / 已知 Bug / 下一步）。日期一律实际当天。

**最后更新**：2026-10-01（TASK-009 状态同步：TASK-004/005/008 → COMPLETED；baseline-v1.0 tag 核验）

---

## 1. 项目当前能否正常运行？

**能（watchdog 路径已验证）**：

- `weather_monitor.py`：✅ 日志显示 2026-09-30 12:57 成功执行（双城市取数 → 规则命中 → 去重 → 静默退出）。
- `test_semantic_engine.py`：✅ 本次任务中实际运行通过（8 场景全部产出预期标签）。
- `main.py` 各模式：⚠️ 语法/编译通过，但依赖企业微信凭证与网络，**本次未做真实推送验证**（会向真实群聊发消息，需用户授权后测试）。
- `test_weather_service.py`：❌ 无法运行（语法错误）。

## 2. 主要功能完成度

| 功能 | 状态 | 说明 |
|---|---|---|
| 天气取数（实况/7天/24h/指数） | ✅ 完成 | 多城市支持（CITY_SLUGS）已实现未提交 |
| 语义规则引擎（9 种条件类型） | ✅ 完成 | 核心 7 条 + 默认 9 条 + 用户自定义 |
| LLM 生成 + 降级模板 | ✅ 完成 | 已验证运行（watchdog 日志含 LLM/降级路径） |
| 企业微信 WS 推送 / @ 回复 | ✅ 完成（未在本次验证） | scheduled / listen / both / once 四模式 |
| APScheduler 定时 | ✅ 完成 | 时区修复已提交（dca395e） |
| watchdog 告警去重状态 | ✅ 完成（已入库） | state/weather_state.json 原子落盘；去重语义 23 例测试覆盖 |
| Railway / Render 部署 | ⚠️ 配置在库，是否仍在用 UNKNOWN | 二者启动命令互相不一致 |

## 3. 当前正在开发什么

**TASK-010「BL-016 Hermes Runtime Discovery」——只读取证完成，READY_FOR_REVIEW（Gate Review 整改已落）**：BL-016 观测类已取证（调度行为/重叠/失败/同 tag emit 幂等——**投递层 UNKNOWN**；docs/HERMES-RUNTIME-EVIDENCE.md），消费侧语义（G1/G2/G4）仍需 Hermes 侧证据；§1.2 倍增窗口 **Cause=UNKNOWN**（G3：用户已排除手动触发；剩余假设含 Agent/工具触发、多实例并发、重复 handler、多 writer 等）。此前：**TASK-004/005/008 全部 COMPLETED（TASK-009 状态同步，2026-10-01）**：安全基线（SECURITY-REVIEW）、凭据处置设计（SEC-R1..R4）、基线冻结（c556d59 + baseline-v1.0 tag + eb0886e）全部闭环；SEC-01/07/08 = Historical Exposure CONFIRMED / Credential RETIRED/REVOKED / Compromise UNKNOWN；REQ-006/015 冻结期转 ACCEPTED。此前闭环：TASK-007（静态清理 + P1-P3 平台失效）、TASK-006（Review + 两项修正）、TASK-003（watchdog 收敛：D1 修复 + 23 例测试）。

## 4. 已知 Bug

| # | 位置 | 描述 | 严重度 |
|---|---|---|---|
| B1 | `test_weather_service.py:10` | `print("=" * 60")` 语法错误，文件无法解析/运行 | 高（测试不可用） |
| B2 | `services/semantic_engine.py` `_load_rule_file` | JSON 规则的 `conditions` 只取第一个 key，多条件会被静默忽略 | 中（易踩坑） |
| B3 | ~~`SemanticEngine(config_dir="config")` 相对 CWD 路径~~ | **已修复（TASK-003，ADR-015）**：默认目录锚定项目根（相对模块定位），测试 `ConfigResolutionTests` 覆盖 | 已关闭 |
| B4 | `models/__init__.py` | 未导出新增的 `WeatherHourly`（目前各处直接从 `models.weather_types` import，未触发问题） | 低 |

## 5. 技术债务

**已于 TASK-000（2026-09-30）迁移至 [BACKLOG.md](../BACKLOG.md)**（BL-001..015）：为避免重复维护，此处不再逐条罗列（ADP-1.0 §41 每事一处）。

- 非阻塞技术债 / 已知缺陷 → `BACKLOG.md`（BL-001..015）；
- **阻塞类用户决策** → 本文件 §6（不进 BACKLOG）；
- 文档-代码冲突 → 本文件 §9 CONFLICT 清单。

## 6. 当前阻塞问题（需用户决定）

1. ~~未提交的 watchdog 功能：何时提交？是否为最终形态？~~ → **已处置完毕**（TASK-003 收敛 + checkpoint d37ed3a/f2358de/c556d59）：REQ-011..014 ACCEPTED、23 例测试在 verify.py 闭环内、文档已对齐——无遗留。
2. 三条部署路径（Railway / Render / Hermes-watchdog）保留哪些？Hermes 的调度配置在哪里？（另：Hermes 集成证据已立案 BL-016，M3 Runtime Integration 核心——TASK-008 Gate Review 修正）
3. **凭证暴露处置——已处置（TASK-007 + P1-P3，2026-09-30）**：静态清理 ✅ + 平台失效 ✅；最终状态 = Historical Exposure CONFIRMED / Credential RETIRED/REVOKED / Compromise UNKNOWN（暴露窗口 77c705d 起至失效日；不做任何第三方访问断言）。R3 历史重写维持 PROPOSED/Skip。
4. ~~`state/weather_state.json` 是否 gitignore~~ → **已完成（TASK-003）**：`state/*` 已 gitignore，`.gitkeep` 保留，现有运行数据未动。

## 7. 当前未提交工作区（Uncommitted Work）

**无。** TASK-003 checkpoint（`feat: finalize watchdog implementation`）已包含 watchdog 实现、23 例测试、ADP 治理文档与全部任务记录。工作区仅剩 `.mimosa/`（Mimosa 安全工具的本地产物，**OUT OF SCOPE** 未入库；是否 gitignore 待用户决定）。

## 8. 下一动作（Next Action）

1. ~~Review 待审文档~~ **已全部闭环**（TASK-004/005/008 COMPLETED @ TASK-009；BASELINE-c556d59 为一致性校验基准）。下一步候选（均待用户授权立项）：M2 终验（BL-014）、M3 Runtime Integration（BL-016 七项取证）。
2. **已完成归档**：P1-P3 平台失效 ✅（2026-09-30）；U5 运行面 ✅（Hermes 活跃用于 QQ 推送；Railway/Render/WeCom/legacy 退役）；TASK-007 checkpoint ✅（f2358de）；基线冻结 ✅（c556d59）。
3. **M2 终验尾巴**：BL-014（README/WIKI 内容对齐，凭据部分已清）。4. **M3 Runtime Integration（核心，Gate Review 修正）**：BL-016 七项 UNKNOWN——观测类已取证（TASK-010：频率/重叠/失败/同 tag emit 幂等），**剩余 G1-G4**（Hermes 消费语义/exit code/重试策略/倍增窗口机制/投递样本）+ 退役配置处置 + README runtime 对齐。

## 9. 文档-代码 CONFLICT 清单（2026-09-30 逐项核查结果）

处理原则：**以代码实际行为为准**，文档待用户确认后统一修订；下表"更可能真实"列即当前事实来源。

| # | 冲突点 | 文档说了什么 | 代码实际是什么 | 更可能真实 | 需用户确认 |
|---|---|---|---|---|---|
| C1 | README/WIKI 目录结构 | 只列 services/models/prompts/config，无 `weather_monitor.py`、`services/weather_state.py`、`state/`、`utils/` | 实际树包含以上全部（watchdog 为未提交工作区） | **代码** | watchdog 定稿后重写 README 结构图 |
| C2 | WIKI 默认规则数 | "`weather_rules_default.json` 7 条" | JSON 实际 **9 条**（含 snow_alert、precip_soon_alert） | **代码** | 无（更新 WIKI 即可） |
| C3 | README 运行方式 | 只写 `--mode once/scheduled` | `main.py` 支持 4 种模式（scheduled/once/listen/both） | **代码** | 无（更新 README） |
| C4 | 部署启动命令 | README：Railway 自动检测 railway.json；render.yaml：`python qywx_websocket.py` | railway.json=`main.py --mode both`；render.yaml=`qywx_websocket.py`；而 2026-09 日志显示**本地 watchdog 是活跃路径** | **日志/代码** | 三条路径保留哪些？Hermes 配置在哪？ |
| C5 | 凭证管理 | README"安全提示：.env 不提交" | README"示例值"与 qywx_websocket.py、wechat_weather.py 中存在**看似真实的** BOT_ID/SECRET/和风 KEY/群 ID（已入库） | **代码（泄露属实）** | 是否轮换凭证并清理？ |
| C6 | CHANGELOG | [Unreleased] 仅记时区修复，停在 2025-06 | git log 显示其后还有 ≥10 个功能/修复提交 | **git 历史** | 是否补记 CHANGELOG |
| C7 | WIKI 测试说明 | 两个测试脚本均可运行 | `test_weather_service.py` 语法损坏无法运行（Bug B1） | **代码** | 修复还是删除该文件 |
| C8 | .env.example 完整性 | （未声明缺项） | 代码还读取 `LLM_TIMEOUT`、`LLM_MAX_RETRIES`、`HEARTBEAT_INTERVAL` 等 7 个 example 未列出的变量 | **代码** | 无（可补 example） |

另有两处**文档间不一致**（非文档-代码冲突）：README 与 WIKI 对 Railway 休眠行为的描述不同（"15 分钟休眠，Webhook 自动唤醒" vs "15 分钟休眠自动唤醒"——实质相同）；`requirements.txt` 含 `openai`/`schedule` 但 WIKI 依赖清单如实列出（文件一致，代码未使用——见技术债 #2）。

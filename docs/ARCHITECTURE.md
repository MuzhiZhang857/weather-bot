# ARCHITECTURE — 项目地图（Single Source of Truth）

> 本文档描述代码的**实际行为**，以源码为准。若与 README.md / WIKI.md 冲突，以本文档 + 源码为准，并在 docs/STATE.md 记录冲突。
> 最后核对日期：2026-09-30（对应未提交的多城市/watchdog 功能工作区状态）。

---

## 1. 项目解决什么问题

weather-bot 是一个**中文天气提醒机器人**：

1. 从和风天气（QWeather）API 获取实时天气、7 天预报、24 小时逐时预报、生活指数；
2. 用**语义规则引擎**（代码内置规则 + JSON 可配置规则）把天气数值翻译成标签（如 "低温预警"、"近期降水"）；
3. 调用 **OpenAI 兼容 LLM** 生成有人情味的中文提醒文案（失败自动降级为固定模板）；
4. 把提醒送达用户，两条通道：
   - **企业微信机器人 WebSocket**（`aibot` 协议）主动推送 / 回复 @ 消息；
   - **stdout 文本**（watchdog 模式，由外部调度器 "Hermes" 读取后投递微信 — 见 Unknown Areas）。

## 2. 系统边界

**属于本项目**：天气取数、语义规则、LLM 文案生成、企业微信 WS 推送、定时调度、告警去重状态。

**不属于本项目**：
- 前端 / Web UI（spec 明确 Non-Goal，见 `.trae/specs/weather-alert-system/spec.md`）；
- 完整聊天机器人（只回复 @ 消息的天气问题，不做对话管理）；
- 数据库（无 SQL/ORM；唯一持久化是本地 JSON 状态文件）；
- 多 Agent 工作流 / Django 迁移（README 提到"预留能力"，**代码中不存在**，属于愿景不是事实）；
- 外部调度器 "Hermes" 本身（watchdog 模式假设它存在并负责投递）。

## 3. 核心模块

| 文件 | 职责 | 依赖 |
|---|---|---|
| `main.py` | 推荐主入口。4 种运行模式：`scheduled`（默认，APScheduler 定时）、`once`（单次）、`listen`（WS 监听 @ 消息并经 `response_url` 回复）、`both`（listen + 后台定时线程）。Railway 启动命令指向它 | services 全部 |
| `weather_monitor.py` | **未提交的新入口**。双/多城市 watchdog：遍历 `CITY_SLUGS` 城市 → 语义规则判定 → `WeatherState` 去重 → 命中新事件才把 LLM 文案打印到 stdout。日志只写文件，stdout 仅承载提醒文本 | weather_service, semantic_engine, llm_service, weather_state |
| `services/weather_service.py` | 封装和风天气 API：`/weather/now`、`/weather/7d`、`/weather/24h`、`/indices/1d`；多城市解析（`CITY_SLUGS`/`CITY_NAMES`，回退单城市 `CITY_ID`）；统一错误处理 | requests, models |
| `services/semantic_engine.py` | 规则引擎：7 条核心规则（代码内置）+ `config/weather_rules_default.json`（9 条）+ `config/weather_rules_user.json`（用户自定义）。支持 9 种条件类型（见 §7）。默认配置目录**锚定项目根**（相对模块定位，TASK-003 D1 修复），不再依赖 CWD | models, config JSON |
| `services/llm_service.py` | 渲染 `prompts/weather_alert.txt` 模板 → POST `{LLM_BASE_URL}/chat/completions`（requests 实现，带重试）；**任何失败都降级**到 `generate_simple_alert()` 固定模板，保证推送不中断 | requests |
| `services/push_service.py` | 企业微信开放平台 WebSocket 客户端：连接 → `aibot_subscribe` 订阅（30s 超时）→ 响应服务器 `ping`/`pong` → `aibot_send_msg` 发 markdown；指数退避重试；消息/事件回调 | websocket-client |
| `services/scheduler.py` | `WeatherScheduler`：APScheduler `BlockingScheduler`（`Asia/Shanghai`），按 `SCHEDULE_TIME` 触发完整工作流。**不使用**状态去重（每日定时推送无条件发送） | services 全部, apscheduler |
| `services/weather_state.py` | **未提交的新模块**。按城市×标签的告警"活动态"记忆，落盘 `state/weather_state.json`（原子写：tmp + os.replace）。首次命中→新事件；仍命中→去重静默；不再命中→解除活动态 | 无（纯标准库） |
| `models/weather_types.py` | 全部 dataclass：`WeatherNow`、`DailyWeather`、`WeatherHourly`、`Weather7D`、`IndicesItem`、`IndicesData`、`WeatherData`、`WeatherRule`、`AlertMessage` | 无 |
| `utils/time_utils.py` | 东八区时间工具（`now_cst` 等）+ `CSTFormatter` 日志格式化器。**注意：`main.py`/`weather_monitor.py`/`weather_state.py` 各自重复定义了 `CST = timezone(timedelta(hours=8))`，没有统一引用本模块** | 无 |
| `prompts/weather_alert.txt` | LLM Prompt 模板（`{占位符}` 替换式，非 Jinja）。占位符列表见 §8 | — |
| `config/weather_rules_default.json` | 预设规则 9 条（雨天/降雪/近期降水/高温/低温/大风/高湿度/强紫外线/感冒） | — |
| `config/weather_rules_user.json` | 用户自定义规则（当前 1 条禁用的示例） | — |
| `qywx_websocket.py` | 旧版单文件整合脚本（BackgroundScheduler + WS + 关键词"天气"触发回复）。**代码内含硬编码凭证默认值**。Render 配置仍指向它 | services |
| `wechat_weather.py` | 最简旧版脚本（webhook 推送）。**硬编码凭证**，无配置化 | requests |

## 4. 模块依赖关系

```
main.py ──► services/scheduler.py ──► weather_service ─► semantic_engine ─► llm_service ─► push_service
   │                                              │              │               │
   │                                              ▼              ▼               ▼
   ├──► push_service (listen/both)            models/*      config/*.json   prompts/weather_alert.txt
   │
weather_monitor.py ──► weather_service ─► semantic_engine ─► llm_service
        │                     │               │
        └──► weather_state ───┘               └──► state/weather_state.json（读写）
                              └──► config/*.json

qywx_websocket.py ──► weather_service / semantic_engine / llm_service / push（自带 WS 逻辑）
wechat_weather.py ──► 无内部依赖（全硬编码）
```

无循环依赖；`services/__init__.py` 统一导出（导入 `services` 包即拉起 apscheduler/websocket 依赖）。

## 5. 数据流

### 5.1 定时推送（main.py scheduled/once → scheduler.py）

```
APScheduler(CronTrigger, Asia/Shanghai, SCHEDULE_TIME)
  └► execute_workflow():
       1. WeatherService.get_complete_weather()  # now + 7d + 24h + indices（单城市 CITY_ID）
       2. SemanticEngine.analyze()               # → {"weather_tags": [...]}
       3. _build_weather_variables()             # 19 个模板变量（见 §8.2）
       4. LLMService.generate_alert()            # 失败 → 降级模板
       5. PushService.connect_websocket() → send_message(markdown) → disconnect()
```

### 5.2 @ 消息回复（main.py listen/both）

```
WS 收到 aibot_msg_callback
  └► handle_message(body):
       1. 提取 text.content + response_url
       2. 同 5.1 的 1-4 步
       3. HTTP POST response_url（markdown webhook），不走 WS 发送
```

### 5.3 watchdog（weather_monitor.py，当前实际活跃路径）

```
外部调度器(Hermes) 启动 weather_monitor.py
  └► for city in get_cities():            # CITY_SLUGS 解析，多城市
       1. get_complete_weather(city_id, city_name)
       2. analyze() → tags
       3. WeatherState.get_new_tags(city_id, tags)   # 新事件/去重/解除
       4. 新事件 → build variables → LLM → alerts[]
  └► print("\n\n".join(alerts))           # 仅命中新事件才打印；否则静默
```

## 6. API / 外部服务

| 服务 | 端点 | 用途 | 备注 |
|---|---|---|---|
| 和风天气 | `https://mg5u9xcaf3.re.qweatherapi.com/v7/weather/now`、`/weather/7d`、`/weather/24h`、`/indices/1d` | 天气数据 | **非官方默认域名**（自定义 host）。鉴权：`key` query 参数（`HEFENG_API_KEY`）。业务成功判定：响应 JSON `code == "200"`（字符串） |
| LLM | `{LLM_BASE_URL}/chat/completions` | 文案生成 | OpenAI 兼容，Bearer 鉴权。requests + urllib3 Retry（429/5xx），`trust_env=False` |
| 企业微信 | `wss://openws.work.weixin.qq.com` | 推送/收消息 | `aibot_subscribe`（bot_id+secret）→ `aibot_send_msg`。**TLS 校验被禁用**（`sslopt={"cert_reqs": ssl.CERT_NONE}`） |
| 企业微信 | 消息体内的 `response_url` | @ 回复 | HTTP POST markdown，listen 模式专用 |

## 7. 语义规则条件类型（SemanticEngine 支持全集）

`humidity_above`、`temp_diff_above`（今日 max-min）、`wind_scale_above`、`temp_below`、`temp_above`、`weather_includes`（关键词列表）、`precip_soon_in`（未来 N 小时降水，读 24h 逐时数据，值可为数字或 `{hours, text_keywords, pop_min, precip_min}` 字典）、`uv_index_includes`、`cold_index_includes`。

**限制**：`_load_rule_file` 只取 `conditions` 对象的**第一个 key** 作为条件类型——JSON 规则一条只能写一个条件；写多个条件时后面的会被静默忽略。

## 8. 配置系统

### 8.1 环境变量（代码中实际读取的全部变量）

| 变量 | 读取处 | 默认值 | 说明 |
|---|---|---|---|
| `BOT_ID` | push_service, qywx_websocket(硬编码默认值!) | `""` | 企业微信机器人 ID |
| `SECRET` | push_service, qywx_websocket(硬编码默认值!) | `""` | 企业微信机器人密钥 |
| `WS_URL` | push_service | `wss://openws.work.weixin.qq.com` | WS 地址 |
| `HEARTBEAT_INTERVAL` / `MAX_RETRY_ATTEMPTS` / `INITIAL_RETRY_DELAY` / `MAX_RETRY_DELAY` / `CONNECT_TIMEOUT` | push_service | 30 / 3 / 1.0 / 30.0 / 10 | WS 连接参数 |
| `HEFENG_API_KEY` | weather_service | 无 | 和风天气密钥 |
| `CITY_SLUGS` | weather_service.get_cities | 无 | 多城市：`slug=locationID,slug2=locationID2` |
| `CITY_NAMES` | weather_service.get_cities | 无 | 可选：`slug=中文名,...` |
| `CITY_ID` / `CITY_NAME` | weather_service（回退）、qywx_websocket(硬编码默认值!) | 无 | 旧单城市模式 |
| `ALERT_LEAD_HOURS` | weather_monitor | 3 | 覆盖 `precip_soon_in` 提前量（小时） |
| `SCHEDULE_TIME` | scheduler | `08:00` | `HH:MM`，Asia/Shanghai |
| `SCHEDULE_CHAT_ID` | scheduler, main.py | `""` | 推送目标会话 ID |
| `SCHEDULE_CHAT_TYPE` | scheduler, main.py | `2` | 1=单聊 2=群聊 |
| `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL` | llm_service | 无 | LLM 配置；任一缺失 → 直接走降级模板 |
| `LLM_TEMPERATURE` / `LLM_MAX_TOKENS` / `LLM_TIMEOUT` / `LLM_MAX_RETRIES` | llm_service | 0.7 / 1000 / 120 / 3 | |

**注意**：`LLM_TIMEOUT`、`LLM_MAX_RETRIES` 及 5 个 WS 参数在代码中存在但 `.env.example` 未列出。

### 8.2 LLM 模板变量（19 个，scheduler.py 与 main.py/weather_monitor.py 三处重复构建）

`city_name, date, time_of_day, current_time, weather, temp, feels_like, humidity, wind_dir, wind_scale, tomorrow_weather, tomorrow_temp_max, tomorrow_temp_min, dressing_index, uv_index, comfort_index, sport_index, cold_index, alert_tags`

注意：`current_time` 在代码中构建但 **prompt 模板并未引用**（冗余变量，历史 commit `b854bff` 引入）；模板实际使用其余 18 个占位符。

`time_of_day` 时段划分（三处重复实现）：6-9 早晨 / 9-12 上午 / 12-14 中午 / 14-18 下午 / 18-22 傍晚 / 其余 晚上。

### 8.3 持久化状态（无数据库）

`state/weather_state.json`（仅 watchdog 使用）：
```json
{ "<city_id>": { "<tag>": { "time": "<ISO+08:00>", "type": "event"|"state" } } }
```
- 写入时机：登记新事件或解除旧事件时（原子写 tmp→replace）；
- 标签分类：`weather_state.py` 顶部 `EVENT_TAG_PREFIXES` / `STATE_TAG_PREFIXES` 前缀匹配，未匹配默认按 event 处理。

## 9. 启动流程

`main.py`：**先清除 4 个代理环境变量** → `load_dotenv()` → 配置日志（RotatingFileHandler，`logs/weather_bot.log`，东八区）→ argparse `--mode` → 按模式分支（见 §5）。
`weather_monitor.py`：stdout 强制 UTF-8（防 Windows gbk emoji 崩溃）→ 清代理 → 日志仅写文件（stdout 保持纯净）→ 遍历城市（见 §5.3）。

## 10. 构建流程

无本地构建步骤（纯 Python 解释执行）。Railway 用 NIXPACKS，Python 3.11（`railway.json`）。Render 用 `pip install -r requirements.txt`。无 pyproject.toml / lockfile / lint / typecheck 配置。

## 11. 测试流程

两个**手写脚本**（非 pytest 框架）：

| 文件 | 状态 | 说明 |
|---|---|---|
| `test_semantic_engine.py` | ✅ 可离线运行 | 8 个场景直接喂 `WeatherData`，打印匹配标签，无断言（verify.py 代为断言输出） |
| `test_watchdog.py` | ✅ 可离线运行（TASK-003 新增） | unittest 22 例：去重状态机、precip_soon_in 三信号、城市解析、CWD 无关加载、monitor 流程（stdout 契约/失败冻结，外部服务 mock）。运行：`$PY -m unittest test_watchdog -v` |
| `test_weather_service.py` | ❌ **语法错误**（第 10 行 `print("=" * 60")`） | 修复后也需要真实网络 + API key |

`scripts/verify.py` = 最小验证闭环（编译 + 语义场景断言 + watchdog 单测），全离线。

## 12. 部署流程

| 平台 | 配置 | 启动命令 | 状态 |
|---|---|---|---|
| Railway | `railway.json`（NIXPACKS, Python 3.11） | `python main.py --mode both` | README 推荐方案；**当前是否仍在运行 UNKNOWN — requires verification** |
| Render | `render.yaml` | `python qywx_websocket.py` | 指向旧脚本，与 Railway 漂移 |
| 本地 watchdog | 外部调度器 "Hermes" | `python weather_monitor.py` | **日志证明 2026-09-30 当天仍在运行，是当前实际活跃路径**；Hermes 本身是什么 UNKNOWN — requires verification |

## 13. Critical Components

被大量依赖、修改需谨慎：

1. **`services/weather_service.py`** — 所有入口的唯一天气数据来源；`get_complete_weather()` 返回结构被 semantic_engine / 所有变量构建代码消费。
2. **`models/weather_types.py`** — 全部跨模块数据结构。改字段名会波及 semantic_engine、scheduler、main、monitor 三处变量构建。
3. **`prompts/weather_alert.txt` 的占位符契约** — 模板 `{xxx}` 与代码变量 dict 必须一一对应；代码用字符串 replace，模板里出现未提供的占位符会原样泄漏给 LLM。
4. **`services/semantic_engine.py` 的条件类型名** — 与 `config/*.json` 的 key 是字符串契约（如 `precip_soon_in`），改名会让规则静默失效。
5. **`services/push_service.py` 的 `ping`/`pong` 响应**（`_on_message`）— git 历史明确记录这是"关键修复"，删掉会导致订阅失败/断连。

## 14. High Risk Areas

修改后容易造成系统级回归的区域：

1. ~~`SemanticEngine(config_dir="config")` 是相对 CWD 的路径~~ → **已修复（TASK-003，ADR-015）**：默认配置目录锚定项目根（相对模块定位），任意 CWD 启动规则集一致（测试 `ConfigResolutionTests` 覆盖）。显式传入 `config_dir` 的语义保持不变。
2. **`weather_state.py` 的去重逻辑** — `_prune` 在某 tag 一次未命中就立即解除活动态；若规则阈值恰好在边界抖动，会造成重复提醒风暴。调整规则阈值前先想清楚与状态文件的交互。
3. **三处重复的"变量构建 + time_of_day"逻辑**（scheduler.py / main.py / weather_monitor.py）— 改模板变量时必须同步三处，否则某条路径输出 `N/A` 或残留 `{占位符}`。
4. **时区实现有两套**：scheduler 用 `ZoneInfo("Asia/Shanghai")`（CHANGELOG 记录的修复），main/monitor/state 用固定 `UTC+8`。两者当前等价（中国无夏令时），但不要只改一处。
5. **`qywx_websocket.py` / `wechat_weather.py` / README 中的真实凭证** — Bot ID、Secret、和风 Key 以硬编码/文档示例形式存在于仓库中（详见 STATE.md 技术债务）。任何"清理"动作都涉及凭证轮换，需用户决策。
6. **LLM 降级路径** — `generate_alert()` 捕获一切异常并降级。测试 LLM 集成时不要被降级模板"假成功"迷惑（日志会写"使用降级方案"）。
7. **`requirements.txt` 含未使用依赖**（`openai`、`schedule`，全代码无 import）— 升级/删除前确认 qywx_websocket 等旧脚本没有间接需要（已核实当前无 import，但保留原因是 UNKNOWN）。

## 15. External Dependencies

| 依赖 | 失败时的行为 |
|---|---|
| 和风天气 API | `get_complete_weather()` 返回 None/空 → 该城市跳过（watchdog）或工作流终止（scheduled）；**不会用旧数据** |
| LLM API | 超时/异常 → 自动降级为 `generate_simple_alert()` 固定模板，推送继续 |
| 企业微信 WS | 连接重试 3 次（指数退避）→ 失败则本次推送丢失（无持久化重试队列） |
| response_url（listen 模式） | POST 失败仅记日志，消息丢失 |
| 外部调度器（Hermes，仅 watchdog） | UNKNOWN — requires verification |

## 16. Unknown Areas

- **UNKNOWN — requires verification**: "Hermes" 是什么（Windows 计划任务？网关服务？），由谁维护，如何配置调度频率。`weather_monitor.py` 注释称其"读取 stdout 作为消息体投递微信"。→ 已立案 **BACKLOG BL-016（Integration Evidence）**，M2 终验前解决。
- **UNKNOWN — requires verification**: Railway / Render 部署当前是否仍在运行。日志证据（logs/weather_bot.log）表明本地 watchdog 是 2026-09 活跃路径。
- **UNKNOWN — requires verification**: 和风天气自定义域名 `mg5u9xcaf3.re.qweatherapi.com` 的来源（企业版专属 host？）。历史 commit 中无解释。
- **UNKNOWN — requires verification**: `.venv`（损坏，指向已卸载的 `D:\Program Files\Tencent\Marvis\...\python311`）与 `.venv2`（Python 3.11.15，无 pip）为什么并存；`.venv2` 如何创建（无 pip，疑似 uv 管理）。
- **UNKNOWN — requires verification**: `requirements.txt` 中 `openai==1.54.3`、`schedule==1.2.2` 保留原因（当前代码无 import）。
- ~~**UNKNOWN**: `state/weather_state.json` 是否应纳入 `.gitignore`~~ → **已决定（TASK-003，ADR-015）**：运行时状态不入库，`state/*` 已 gitignore（保留 `.gitkeep`）；现有运行数据原样保留在本机。

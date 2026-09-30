# DEVELOPMENT — 开发规范（记录现状，不是愿景）

> 原则：本文只记录项目**已经存在并实际使用**的工具与命令。没有的东西明确写"无"，不要凭经验补充。

---

## 1. 语言与运行时

| 项 | 现状 |
|---|---|
| 语言 | Python（唯一语言） |
| 版本依据 | `railway.json` NIXPACKS 指定 **3.11**；仓库无 `.python-version` / `pyproject.toml` 版本声明 |
| 本地可用解释器 | `.venv2/Scripts/python.exe` = **Python 3.11.15**（依赖已装好：requests / websocket-client / apscheduler / python-dotenv；**无 pip 模块**） |
| `.venv` | **已损坏** — venv 指向已不存在的 `D:\Program Files\Tencent\Marvis\...\python311\python.exe`。不要使用 |
| 系统 Python | 本机另装 Python 3.13.14（`python` 命令），未验证依赖完整性 |

**约定**：本地运行/测试统一用 `.venv2/Scripts/python.exe`（相对项目根的绝对路径调用，避免 PATH 混淆）。

## 2. 框架与核心依赖（requirements.txt，pip 钉版本）

```
websocket-client==1.9.0    # 企业微信 WS（实际使用）
requests==2.32.3           # 天气 API + LLM 调用（实际使用）
schedule==1.2.2            # 未使用（全仓库无 import）— 删除前需确认，见 docs/ARCHITECTURE.md §14
python-dotenv==1.0.1       # .env 加载（实际使用）
APScheduler==3.10.4        # 定时调度（实际使用）
openai==1.54.3             # 未使用（LLM 用裸 requests）— 删除前需确认
```

包管理器：**pip + requirements.txt**。无 lockfile、无 pyproject.toml、无 setup.py。

## 3. 代码风格

| 项 | 现状 |
|---|---|
| Formatter | **无**（未配置 black/ruff fmt 等） |
| Linter | **无** |
| Type checker | **无**（代码有类型注解习惯，但无 mypy/pyright 配置） |
| 命名/习惯 | 模块级中文注释与日志；服务类以 `XxxService`/`XxxEngine` 命名；dataclass 字段与和风 API 原始字段名保持一致（如 `feelsLike`、`textDay` — 有意为之，勿改成 snake_case） |

## 4. 命令速查（在项目根 `D:\weather-bot` 下执行）

```bash
# 解释器变量（Git Bash 写法）
PY=".venv2/Scripts/python.exe"

# ---- 安装依赖（仅当重建 venv 时）----
pip install -r requirements.txt

# ---- 运行 ----
$PY main.py --mode once         # 单次推送（走企业微信 WS，需 BOT_ID/SECRET/群配置，会真实发消息）
$PY main.py --mode scheduled    # 定时模式（默认模式，阻塞运行）
$PY main.py --mode listen       # 监听 @ 消息并回复
$PY main.py --mode both         # 监听 + 后台定时线程（Railway 启动命令）
$PY weather_monitor.py          # watchdog：多城市检查，命中新事件才打印到 stdout（当前活跃模式）
$PY qywx_websocket.py           # 旧版整合脚本（Render 启动命令指向它）

# ---- 测试 ----
$PY scripts/verify.py           # 最小验证闭环：全模块 py_compile + 离线语义引擎测试（推荐每次改码后运行）
$PY test_semantic_engine.py     # 语义引擎 8 场景（离线，无断言，人工目检输出）
$PY test_weather_service.py     # 【已知损坏】第 10 行语法错误，见 docs/STATE.md

# ---- 构建 ----
# 无本地构建。云平台：Railway=NIXPACKS 自动构建；Render=pip install -r requirements.txt
```

**Dev / Production 命令的差异**：没有独立的 dev 配置。区别只在环境变量（`.env` 本地 / Railway·Render 控制台）与入口选择；生产（Railway）跑 `main.py --mode both`，本地验证跑 `weather_monitor.py`。

## 5. 环境变量

完整清单（含默认值与读取位置）见 **docs/ARCHITECTURE.md §8.1**，此处不重复。

- 本地：复制 `.env.example` → `.env` 填写。`.env` 已在 `.gitignore`，**严禁提交**。
- 云端：Railway/Render 控制台逐个配置。
- `.env.example` 与代码的一致性以 ARCHITECTURE.md §8.1 为准（example 缺 `LLM_TIMEOUT`、`LLM_MAX_RETRIES` 及 5 个 WS 参数）。

## 6. "数据库"与迁移方式

**无数据库。** 唯一持久化是 `state/weather_state.json`（watchdog 告警去重活动态，结构见 ARCHITECTURE.md §8.3）。

- 无迁移机制；结构变更由 `weather_state.py` 的加载容错兜底（坏文件 → 从空状态开始）。
- 该文件是运行时产物：**不要手工编辑后提交**；是否加入 `.gitignore` 待用户确认（STATE.md 阻塞项）。

## 7. Git 工作流（从 git 历史归纳的实际做法）

- 分支：单 `main` 分支开发；外部贡献经 GitHub PR（历史上有 5 个 merge PR，来自 fork `MuzhiZhang857/master`）。
- 提交信息：中文为主、带类型前缀的约定式风格（`feat:` / `fix:` / `docs:`），如 `fix: 修复定时推送时区偏移问题 - 从16:00修正为08:00`。
- 远端：`origin`（GitHub）。当前工作区有**未提交的多城市/watchdog 功能**（见 docs/STATE.md）。
- 无 CI/CD（无 GitHub Actions / pre-commit / branch protection 证据）。
- CHANGELOG.md 存在但仅维护到 2025-06（0.1.0）与一条 Unreleased 时区修复，严重滞后于实际提交，不能作为事实来源。

## 8. 修改检查单（每次代码修改，ADP-1.0 七阶段的落地版）

1. **GATE 1**：确认需求依据（REQUIREMENTS.md 的 ACCEPTED 条目或用户指令）与任务文件（tasks/，六态状态机）；
2. 改码（遵守 AGENTS.md 的保护目录与确认事项；非阻塞发现 → `BACKLOG.md`，不扩 Scope）；
3. `$PY scripts/verify.py` 通过（L0 编译 + L1 离线语义测试），并声明本次验证级别；
4. 涉及外部交互的改动，本地手动跑对应入口一次（真实调用 API/发消息，先获用户逐次授权）；
5. **RECORD**：更新 `docs/STATE.md`（当前状态）、任务文件 Completion Evidence；有架构影响的决策 → `docs/DECISIONS.md`（新 ADR 必含 Alternatives）；
6. 提交（遵循 §7 提交信息风格；一个有意义任务一个 commit）。

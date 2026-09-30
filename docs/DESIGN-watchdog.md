# DESIGN: Watchdog（weather_monitor 体系）— ACCEPTED

> **文档地位**：REQ-011..014 的正式设计文档。TASK-002（2026-09-30）对未提交工作区代码逆向规格化产出（当时 PROPOSED）；**TASK-003（2026-09-30）经用户批准随 REQ-011..014 一并 ACCEPTED（ADR-015），本文自此冻结为设计基准**。此后代码与本文偏差须走 Task/ADR；§7 的 Q1-Q4 已全部决议（决议内嵌于各条）。
> **证据分级**：正文区分 【FACT】（代码/日志可证）、【设计】（决策记录）、【风险】【未决】。

---

## 1. Watchdog 实现了什么（事实清单）

**一句话**：一个无常驻进程的多城市命令行检查器——每次运行遍历全部配置城市，取完整天气 → 规则引擎判定 → 按城市×标签去重 → 只把**新**告警的 LLM 文案打印到 stdout；未命中或重复则零输出退出。

### 1.1 涉及文件（7 个，全部未提交）

| 文件 | watchdog 角色 |
|---|---|
| `weather_monitor.py` | 入口/编排（210 行） |
| `services/weather_state.py` | 告警去重状态（159 行） |
| `services/weather_service.py`（未提交增量） | 多城市解析 + 24h 逐时预报 |
| `services/semantic_engine.py`（未提交增量） | `precip_soon_in` 提前降水条件 |
| `models/weather_types.py`（未提交增量） | `WeatherHourly` 数据类 |
| `config/weather_rules_default.json`（未提交增量） | `precip_soon_alert` 规则 |
| `.env.example`（未提交增量） | `CITY_SLUGS`/`CITY_NAMES`/`ALERT_LEAD_HOURS` |

### 1.2 运行时行为【FACT】

| # | 行为 | 证据 |
|---|---|---|
| F1 | 启动时强制 stdout 为 UTF-8（防 Windows gbk 下 emoji 崩溃） | weather_monitor.py:20-28 |
| F2 | 清除 4 个代理环境变量后才导入网络模块 | weather_monitor.py:31-34 |
| F3 | 日志**只写文件**（logs/weather_bot.log，RotatingFileHandler，东八区），`logger.propagate=False` 保证 stdout 纯净 | weather_monitor.py:46-78 |
| F4 | 从 `CITY_SLUGS`（`slug=locationID` 逗号分隔）解析城市列表，`CITY_NAMES` 可选中文名映射；未配置则回退单城市 `CITY_ID`；解析为空则退出码 1 | weather_service.py:33-75；weather_monitor.py:159-162 |
| F5 | 每城市独立取完整天气（实况+7天+24h逐时+生活指数）；**任一城市取数失败仅跳过该城市**，不影响其他城市，也不触碰其历史状态 | weather_service.py:275-301；weather_monitor.py:170-173 |
| F6 | 语义引擎逐规则判定；其中 `precip_soon_in`：未来 N 小时内（默认 3）逐时数据命中"文本含雨/雪" 或 `pop ≥ 30%` 或 `precip ≥ 1.0mm` 即命中 | semantic_engine.py:222-256 |
| F7 | `ALERT_LEAD_HOURS` 环境变量在运行时覆盖 `precip_soon_in` 规则的提前量 | weather_monitor.py:123-128,152 |
| F8 | **去重核心**：以"规则标签"为指纹，按城市×标签维护活动态；首次命中→登记并作为新告警输出；仍命中→静默去重；一次未命中→解除活动态（未来可再告警） | weather_state.py:107-150 |
| F9 | 状态持久化 `state/weather_state.json`（结构 `{city_id: {tag: {time, type}}}`），写入用 tmp 文件 + `os.replace` 原子替换；文件损坏则从空状态开始 | weather_state.py:39-49,59-86 |
| F10 | 标签分两型：事件型（注意带伞/注意防滑/近期降水/大风/风寒明显）与状态型（高湿度/高温/低温/酷热/严寒/昼夜温差/强紫外线/感冒/潮湿），按前缀匹配，未识别默认事件型 | weather_state.py:29-33,94-102 |
| F11 | 命中新告警才生成文案（LLM，失败自动降级模板——复用 REQ-003），多城市文案以空行拼接后 `print` 到 stdout；无新告警则**零输出**退出 | weather_monitor.py:189-200 |
| F12 | 不导入 push_service，不读 BOT_ID/SECRET——watchdog 自身不推送，投递外包给外部调度器 | weather_monitor.py:146-149 |
| F13 | `--once` 参数存在但为无操作（默认行为即单次） | weather_monitor.py:132-138 |
| F14 | 顶层异常捕获：记日志后退出码 1 | weather_monitor.py:204-206 |

### 1.3 运行证据【FACT】

- `state/weather_state.json`：两城市（包头 101080201 / 呼和浩特 101080101）各有 3 个状态型标签自 **2026-09-19 21:30** 处于活动态。
- `logs/weather_bot.log` 2026-09-30 12:57：双城市完整执行，相同标签命中被判"重复事件，保持静默去重"，最终零输出退出——**去重跨天生效的实证**。
- 推断（INFERENCE）：watchdog 已被某外部机制按日/多小时调度运行 ≥11 天（调度器本体即"Hermes"，见 §5.5）。

---

## 2. 行为分类：哪些是需求，哪些是 Agent 的设计

### 2.1 明确需求（可追溯）——只有两类

1. **复用的 ACCEPTED 能力**：天气取数（REQ-001）、规则引擎（REQ-002）、LLM+降级（REQ-003）、文件日志（REQ-007）。watchdog 对它们是**消费方**，这部分行为有需求依据。
2. **"保持 PROPOSED"本身**：用户在 TASK-000 任务书中明确指示"不得因已实现而视为产品需求"——这是 watchdog 相关的唯一一条显式用户指令（FACT：任务书原文）。

**除此之外，watchdog 的全部差异化行为（F4-F13）没有任何一条能追溯到用户需求、历史 PRD 或正式设计评审。** `.env` 中 CITY_SLUGS 已填真实城市且系统已运行 11+ 天，属"事实存在、需求未记录"（无法确认配置者是用户还是 Agent）。

### 2.2 Claude（前序 Agent）自行做出的设计【设计】

| # | 设计 | 内容 | 决策记录 |
|---|---|---|---|
| S1 | 多城市配置面 | CITY_SLUGS/CITY_NAMES 环境变量格式 + 单城市回退 | 无 ADR；散见代码注释 |
| S2 | 提前降水判定 | 接入 /weather/24h；`precip_soon_in` 条件；启发式阈值 pop≥30%、precip≥1.0mm、文本关键词 | 无 ADR；JSON 规则内含 |
| S3 | 去重模型 | tag 作指纹、城市×标签隔离、活动/解除语义、无全局冷却 | ADR-008（Agent 撰写的论证，非用户批准记录） |
| S4 | 标签两型分类 | event/state 前缀表（F10） | 无 ADR；仅代码注释 |
| S5 | stdout 契约 | 命中新事件才输出；日志只进文件；投递外包 | ADR-007 |
| S6 | Hermes 假设 | 外部调度器读取 stdout 投递微信 | ADR-007；**实现本体不在仓库** |
| S7 | 运行时配置覆盖 | ALERT_LEAD_HOURS 改写规则条件 | 无 ADR |
| S8 | 工程细节 | stdout UTF-8、代理清理、失败跳过单城市、`--once` 空参数 | ADR-011 + 代码注释 |

### 2.3 合理但尚未批准（S1-S8 的合理性论证）

- **S3 去重模型——最关键的设计**。合理性：外部调度器高频运行下，无去重 = 每次命中都轰炸；以 tag 为指纹使天气数值微抖不影响去重（相对"时间戳/数值指纹"方案）；"一次未命中即解除"保证雨停再雨能再提醒；原子落盘保证重启不重复推送。**代价**：边界抖动会"解除→再提醒"（§4 D4），且活动态跨天长存（state 文件实证 11 天）。
- **S5+S6 stdout 契约**。合理性：把"检测"与"投递"解耦，watchdog 不持有企业微信凭证（F12），攻击面与配置面最小；代价：投递质量依赖仓库外的 Hermes（不可验证）。
- **S1+S2+S7 配置面**。合理性：零数据库约束下的最小实现；阈值可经 JSON 字典形式或 env 调整；代价：env 格式无校验、解析失败即退出（fail-fast，可接受）。
- **S8** 防御性工程，无争议。
- 批准 S1-S8 意味着：接受上述语义为**产品行为**（而非临时脚本），后续修改须走 Task/ADR，删除它们也须用户同意。

### 2.4 缺陷（见 §4）

---

## 3. 与已批准需求的交叉影响

| 交叉点 | 状态 |
|---|---|
| watchdog 命中后仍走 REQ-003 LLM+降级 | ✅ 复用，无冲突 |
| **双通道重复提醒**：`main.py --mode scheduled`（REQ-005，每日推送）**不接入**去重状态（scheduler.py 无 weather_state import），同一标签可能在 watchdog 与定时推送中重复出现 | 【未决】Q3，需产品决策 |
| watchdog 的 stdout 文案格式沿用 REQ-003 的 19 变量模板 | ✅ 复用（变量构建代码三处重复 → BL-003） |

---

## 4. 缺陷与处置（按严重度）

| # | 缺陷 | 证据 | 影响 | 处置 |
|---|---|---|---|---|
| D1 | **CWD 相对路径读规则**：`SemanticEngine(config_dir="config")` 相对当前目录；从非项目根启动（Hermes 完全可能）时 JSON 规则静默丢失，只剩 7 条核心规则，行为变化无告警 | semantic_engine.py:20 | **High**——告警集静默缩水 | ✅ **已修复（TASK-003，用户批准 Q2=修复方案）**：默认目录锚定项目根（相对模块定位），显式 config_dir 语义不变；测试 `ConfigResolutionTests.test_rules_load_regardless_of_cwd` |
| D2 | **去重核心零测试**：F8/F9 的正确性（首现/重复/解除/原子写）无任何 L1 测试 | BACKLOG BL-015 | High（对验收而言）——正确性主张不可证 | ✅ **已补齐（TASK-003）**：test_watchdog.py 22 例（状态机/规则/解析/流程），已入 verify.py 闭环（BL-015 关闭） |
| D3 | **状态文件无并发保护**：无文件锁；Hermes 重叠调度两个实例时可能丢失解除记录或双发 | weather_state.py:77-86 | Medium | **按 TASK-003 决定接受为已知风险**：单实例假设写入 §5.1；锁机制不做（后续 Integration Evidence 若证实重叠调度再立项） |
| D4 | **告警抖动**：阈值边界附近"命中→未命中→命中"会连续三次提醒（一次未命中即解除，无迟滞/冷却） | weather_state.py:136-150 | Medium | **按 TASK-003 决定接受为已知风险**：不引入迟滞；保持当前设计 |
| D5 | JSON 规则单条件限制（STATE.md B2） | semantic_engine.py:101 | Medium | 既定 BL-007，不阻塞验收 |
| D6 | 变量构建/time_of_day 三处重复（STATE.md B3 家族） | weather_monitor.py:96-120 | Low | 既定 BL-003 |
| D7 | `--once` 无操作参数；ALERT_LEAD_HOURS 非法值 fail-fast 崩溃 | weather_monitor.py:132-138,152 | Info | 保留现状（fail-fast 合理）；随 TASK-003 文档说明 |
| D8 | **Hermes 不可验证**：投递链路上游在仓库外，stdout 契约的端到端正确性无法在本仓库内证明 | 仅注释提及 | Info（对 REQ-013 为 UNKNOWN） | **→ BL-016（Hermes Integration Evidence）**：M2 终验前解决；在此之前不得声称"Production / Hermes integration verified" |

---

## 5. 正式设计（as-implemented 规格）

### 5.1 组件与数据流

```
外部调度器(Hermes, 仓库外)
  └► python weather_monitor.py            # 单实例假设（D3）
       ├─ WeatherService.get_cities()      # CITY_SLUGS/CITY_NAMES/回退 CITY_ID
       ├─ for city: get_complete_weather(id, name)   # 失败→跳过该城市
       ├─ SemanticEngine.analyze(data)     # 核心7条 + 默认9条 + 用户规则
       ├─ WeatherState.get_new_tags(id, tags)        # 去重/登记/解除
       ├─ 新事件 → LLMService.generate_alert(vars)   # 失败→降级模板(REQ-003)
       └─ print("\n\n".join(alerts))       # 仅命中新事件；否则零输出
```

### 5.2 去重状态机（单城市 × 单标签）

```
[无记录] --命中--> [活动态] 且判为新告警（输出）
[活动态] --仍命中--> 保持，静默
[活动态] --一次未命中--> [解除：删记录]（未来再命中按新告警）
取数失败/城市跳过 --> 状态不动（不误解除）
```

- 指纹 = 标签文本本身；时间戳仅记录用，不参与判定。
- event/state 两型当前**不影响判定语义**（只影响 state 文件元数据 type 字段），是预留分类。

### 5.3 失败边界

| 失败 | 行为 |
|---|---|
| 单城市取数失败 | 跳过该城市；其余城市正常；该城市状态冻结 |
| LLM 失败/未配置 | 降级模板（REQ-003），提醒仍产出 |
| 状态文件损坏 | 从空状态开始（全部按新告警重发一轮） |
| 规则 JSON 不可读 | 警告 + 退化为核心规则（⚠️ D1 场景，待修） |
| 任何顶层异常 | 日志 + 退出码 1（stdout 可能已有部分输出——Hermes 侧语义未知，【未决】Q4） |

### 5.4 配置面（watchdog 专用增量）

| 配置 | 语义 | 默认 |
|---|---|---|
| `CITY_SLUGS` | `slug=locationID,...` 多城市清单 | 无（回退 CITY_ID） |
| `CITY_NAMES` | `slug=中文名,...` 可选 | slug 本名 |
| `ALERT_LEAD_HOURS` | precip_soon_in 提前量（小时） | 3 |
| `precip_soon_in` JSON 值 | 数字，或 `{hours, text_keywords, pop_min, precip_min}` 字典 | 3 / [雨,雪] / 30 / 1.0 |

### 5.5 外部依赖与信任边界

和风天气 API、LLM API（同 REQ-001/003）；**Hermes（仓库外）**：负责调度与把 stdout 投递到微信——其存在性由日志间接证明，实现、配置、失败语义全部 UNKNOWN（ARCHITECTURE.md §16）。

---

## 6. 验收标准（Acceptance Criteria）

> 批准 REQ-011..014 为 ACCEPTED 后，以下 AC 是 M2 关闭的客观门槛。AC-1/4/2/3 离线可测（入 verify.py）。

- **AC-1 规则判定**：给定含 24h 数据的 WeatherData，`precip_soon_in` 在"文本含雨/雪"、"pop≥阈值"、"precip≥阈值"三种情形下均返回"近期降水提醒"，且 N 小时窗口外不命中。Verification: 单元测试（新增，进 verify.py）。
- **AC-2 去重语义**：对同一 city 依次输入 tags 序列 [A] → [A] → [] → [A]，get_new_tags 分别返回 [A] / [] / []（并解除）/ [A]。Verification: 单元测试（BL-015 落地）。
- **AC-3 状态持久化**：状态写入后文件可再加载且语义不变；save 使用 tmp+os.replace（可测写入函数行为）；**损坏容错覆盖两种故障模式**——内容非法 JSON（tests/fixtures/corrupted_weather_state.json）与路径不可读，均从空状态开始且自愈。Verification: 单元测试（test_corrupted_json_starts_empty / test_unreadable_state_file_starts_empty）。
- **AC-4 城市解析**：CITY_SLUGS 仅 slug、slug=ID、含 CITY_NAMES 映射、回退 CITY_ID 四种配置解析结果正确。Verification: 单元测试。
- **AC-5 stdout 契约**：无新事件时 stdout 零字节；有新事件时 stdout 恰为 LLM 文案拼接；日志不出现在 stdout。Verification: 本地手动（离线 mock 天气数据）+ 日志文件核查。
- **AC-6 规则加载健壮性**：从任意 CWD 启动时规则集完整加载。Verification: 单元测试 + 子进程不同 CWD 启动。**前置**：D1 修复（建议纳入 TASK-003），或用户书面确认 Hermes 固定项目根启动（则降级为文档约束）。
- **AC-7 文档一致**：README/ARCHITECTURE 与最终代码一致（消除 STATE.md §9 C1-C3）。Verification: 人工核查 + BL-014 关闭。
- **AC-8 回归**：verify.py 全绿（含新增测试）。

---

## 7. 原未决问题 → 决议记录（TASK-003，2026-09-30，ADR-015）

- **Q1 是否批准 REQ-011..014**：✅ **全部批准为 ACCEPTED**（用户 TASK-003 任务书：Authorization 节）。
- **Q2 D1 处置**：✅ **修复代码**（不采用"约束 Hermes 固定 CWD"方案）——已实施并测试（ConfigResolutionTests）。
- **Q3 双通道去重**：✅ **两个独立语义通道**——事件告警走 WeatherState 去重；定时日报（REQ-005）不接入去重（用户任务书 Explicit Design Decisions）。
- **Q4 Hermes**：⏳ 信息仍未获得 → **BL-016（Integration Evidence）**，M2 终验前解决；在此之前禁止声称"Production / Hermes integration verified"（用户任务书 Hermes Information 节）。

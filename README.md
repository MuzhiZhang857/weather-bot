# 智能天气提醒系统 - 企业微信 LLM 机器人

## 项目概述

本项目是一个模块化、可扩展的智能天气提醒系统，支持：
- ✅ 模块化 Service 层架构
- ✅ 语义规则引擎解析天气标签
- ✅ 国内 LLM 集成（通义千问/DeepSeek/智谱AI）
- ✅ 自然语言天气提醒生成
- ✅ 企业微信机器人 WebSocket 推送
- ✅ APScheduler 定时任务
- ✅ 支持后续迁移到 Django
- ✅ 预留 AI Agent 工作流扩展能力

## 技术架构

采用 Service 层架构，各模块低耦合：

```
autoweather/
├── services/
│   ├── weather_service.py      # 天气数据获取和清洗
│   ├── semantic_engine.py      # 规则引擎：语义标签分析
│   ├── llm_service.py         # LLM 调用：自然语言生成
│   ├── push_service.py        # 推送服务：企业微信 WebSocket
│   └── scheduler.py           # 调度器：APScheduler 定时任务
├── models/
│   └── weather_types.py       # 类型定义
├── prompts/
│   └── weather_alert.txt      # Prompt 模板
├── config/
│   ├── weather_rules_default.json  # 预设语义规则
│   └── weather_rules_user.json     # 用户自定义语义规则
├── main.py                     # 主入口
├── requirements.txt
├── railway.json
├── render.yaml
└── .env.example
```

## 核心功能流程

```
┌───────────────┐    ┌──────────────────┐    ┌───────────────┐    ┌───────────────┐
│ WeatherService│───>│ SemanticEngine   │───>│   LLMService  │───>│  PushService  │
│  获取天气数据  │    │  解析语义标签    │    │ 生成自然语言   │    │ 推送企业微信   │
└───────────────┘    └──────────────────┘    └───────────────┘    └───────────────┘
     ↑
┌─────────────────────────────────────────────────────────────────────┐
│                      APScheduler (定时调度)                        │
└─────────────────────────────────────────────────────────────────────┘
```

## 语义规则说明

支持预设规则和用户自定义规则：
- `湿度 > 85%` → "潮湿"
- `温差 > 10℃` → "昼夜温差大"
- `风力 > 5级` → "风寒明显"
- `温度 < 0℃` → "严寒"
- `温度 > 35℃` → "酷热"
- `天气含"雨"` → "注意带伞"
- `天气含"雪"` → "注意防滑"

用户可在 `config/weather_rules_user.json` 自定义规则

## LLM 支持

支持多种国内 LLM 服务（OpenAI 兼容接口）：
- 通义千问 (DashScope)
- DeepSeek
- 智谱 AI (GLM)

## 部署平台

### 推荐：Railway（免费额度充足）

**优点**：
- 每月 500 小时免费运行时间
- 自动部署 GitHub 仓库
- 易于配置环境变量
- 支持自动重启

**缺点**：
- 免费版实例会在空闲15分钟后休眠（但会通过Webhook自动唤醒）

### 备选：Render

**优点**：
- 免费容器持续运行
- 与 GitHub 集成良好

**缺点**：
- 免费版有休眠限制（90天后需要手动唤醒）
- 性能相对较低

---

## Railway 部署步骤

### 1. 准备 GitHub 仓库

```bash
# 创建新仓库并推送代码
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/你的用户名/weather-bot.git
git push -u origin main
```

### 2. Railway 部署

#### 方法一：GitHub 集成部署（推荐）

1. 访问 [Railway.app](https://railway.app)
2. 使用 GitHub 登录
3. 点击 "New Project" → "Deploy from GitHub repo"
4. 选择你的仓库
5. Railway 会自动检测 `railway.json` 配置

#### 方法二：手动部署

1. 访问 [Railway.app](https://railway.app)
2. 点击 "New Project" → "Empty Project"
3. 点击 "Add a Service" → "Empty Service"
4. 上传代码或连接 GitHub 仓库

### 3. 配置环境变量

在 Railway 项目设置中添加以下环境变量：

#### 企业微信配置
| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `BOT_ID` | 企业微信机器人ID | `aibq4IJma9oTpus6NeE6--WVJtJaK_0O3wN` |
| `SECRET` | 企业微信机器人密钥 | `ST6Ytrm7M1BAlVOCVxuGwMKrNg7hoWR3rStapaIak9D` |

#### 天气 API 配置
| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `HEFENG_API_KEY` | 和风天气API密钥 | `bb4de13c914d421a9aa4f255df9de5c9` |
| `CITY_ID` | 城市ID | `101080101` |
| `CITY_NAME` | 城市名称 | `呼和浩特` |

#### LLM 配置
| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `LLM_API_KEY` | LLM API Key | `sk-xxxx` |
| `LLM_BASE_URL` | API 地址 | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `LLM_MODEL` | 模型名称 | `qwen-plus` |
| `LLM_TEMPERATURE` | 温度参数 | `0.7` |
| `LLM_MAX_TOKENS` | 最大输出 Token | `1000` |

#### 定时任务配置
| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `SCHEDULE_TIME` | 定时推送时间 | `08:00` |
| `SCHEDULE_CHAT_ID` | 推送目标群聊ID | `wrpv4ybQAA1abzhZBJZ8SaOVZIb5u9NA` |
| `SCHEDULE_CHAT_TYPE` | 会话类型 | `2` (2=群聊, 1=单聊) |

### 4. 配置自定义域名（可选）

1. 在 Railway 项目设置中点击 "Settings"
2. 点击 "Networking" → "Custom Domains"
3. 添加你的域名并配置 DNS

### 5. 监控日志

1. 在 Railway 控制台选择你的服务
2. 点击 "Deployments" 查看部署历史
3. 点击 "Logs" 查看实时日志

---

## Render 部署步骤

### 1. 准备 GitHub 仓库

同上步骤 1

### 2. Render 部署

1. 访问 [Render](https://render.com)
2. 使用 GitHub 登录
3. 点击 "New" → "Web Service"
4. 连接你的 GitHub 仓库
5. 配置以下设置：

**基础设置**：
- **Name**: `weather-bot`
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python qywx_websocket.py`

**实例类型**：
- 选择 **Free**（免费实例）

**环境变量**：
添加上述表格中的所有环境变量

### 3. 自动部署

Render 默认会在你推送代码到 GitHub 时自动部署。

---

## 配置说明

### 企业微信配置

1. 登录企业微信管理后台
2. 进入"应用管理"
3. 创建或选择 AI Bot 应用
4. 复制 Bot ID 和 Secret

### 和风天气 API

1. 访问 [和风天气开发者平台](https://dev.qweather.com/)
2. 注册并登录
3. 创建应用获取 API Key
4. 查找城市ID：https://geoapi.qweather.com/v2/city/lookup?location=城市名&key=你的KEY

### 群聊 ID 获取

运行一次脚本，当用户在群聊中发送消息时，终端会输出群聊ID：
```
会话ID: wrpv4ybQAA1abzhZBJZ8SaOVZIb5u9NA
```

---

## 常见问题

### Q1: Railway 实例休眠怎么办？

Railway 免费实例会在空闲15分钟后休眠。当用户发送消息时，企业微信会通过 WebSocket 推送消息，实例会自动被唤醒。

### Q2: 如何修改定时推送时间？

在 Railway/Render 的环境变量中修改 `SCHEDULE_TIME`，例如：
- `08:00` - 每天早上8点
- `07:30` - 每天早上7点半
- `20:00` - 每天晚上8点

### Q3: 如何推送给多个群聊？

目前脚本只支持推送给一个群聊。如需推送给多个群聊，可以：
1. 部署多个实例
2. 修改代码支持多个群聊ID

### Q4: 如何查看运行日志？

- **Railway**: 在项目控制台点击 "Logs"
- **Render**: 在服务控制台点击 "Logs"

### Q5: 推送失败怎么办？

1. 检查日志中的错误信息
2. 确认群聊ID是否正确
3. 确认机器人是否被添加到目标群聊
4. 确认 Bot ID 和 Secret 是否正确

---

## 项目结构

```
weather-bot/
├── services/
│   ├── __init__.py
│   ├── weather_service.py      # 天气数据服务
│   ├── semantic_engine.py      # 语义规则引擎
│   ├── llm_service.py         # LLM 集成服务
│   ├── push_service.py        # 企业微信推送服务
│   └── scheduler.py           # 定时调度服务
├── models/
│   ├── __init__.py
│   └── weather_types.py       # 类型定义
├── prompts/
│   └── weather_alert.txt      # Prompt 模板
├── config/
│   ├── weather_rules_default.json  # 预设语义规则
│   └── weather_rules_user.json     # 用户自定义规则
├── main.py                     # 主入口
├── qywx_websocket.py          # 旧版本 WebSocket（保留）
├── requirements.txt
├── railway.json
├── render.yaml
├── .env.example
└── README.md
```

---

## 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 方法 1: 使用 .env 文件
# 复制 .env.example 为 .env 并填写配置
cp .env.example .env
# 编辑 .env 填写配置

# 方法 2: 直接设置环境变量（Windows）
set BOT_ID=你的机器人ID
set SECRET=你的机器人密钥
set HEFENG_API_KEY=你的API密钥
set LLM_API_KEY=你的LLM API密钥
set LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
set LLM_MODEL=qwen-plus
set CITY_ID=101080101
set CITY_NAME=呼和浩特
set SCHEDULE_TIME=08:00
set SCHEDULE_CHAT_ID=你的群聊ID
set SCHEDULE_CHAT_TYPE=2

# 运行（单次执行，测试用）
python main.py --mode once

# 运行（定时模式，正式使用）
python main.py --mode scheduled
# 或直接运行（默认 scheduled 模式
python main.py
```

---

## 技术支持

如有问题，请检查：
1. 日志输出中的错误信息
2. 环境变量配置是否正确
3. 企业微信 Bot 是否有效
4. 网络连接是否正常

---

## 注意事项

1. **安全提示**：不要将 `.env` 文件提交到 GitHub，已添加到 `.gitignore`
2. **费用提示**：Railway 和 Render 都有免费额度，超出后会产生费用
3. **重启机制**：脚本内置了自动重连机制，无需手动重启
4. **时区**：定时任务使用服务器时区（UTC），注意换算

---

**祝你部署成功！** 🚀

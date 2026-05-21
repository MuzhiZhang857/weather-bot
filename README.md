# 企业微信天气机器人 - 云端部署指南

## 项目概述

本项目是一个基于企业微信 WebSocket 的天气推送机器人，支持：
- 定时自动推送天气信息
- 实时响应用户消息
- 自动重连机制

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

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `BOT_ID` | 企业微信机器人ID | `aibq4IJma9oTpus6NeE6--WVJtJaK_0O3wN` |
| `SECRET` | 企业微信机器人密钥 | `ST6Ytrm7M1BAlVOCVxuGwMKrNg7hoWR3rStapaIak9D` |
| `HEFENG_API_KEY` | 和风天气API密钥 | `bb4de13c914d421a9aa4f255df9de5c9` |
| `CITY_ID` | 城市ID | `101080101` |
| `CITY_NAME` | 城市名称 | `呼和浩特` |
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
├── qywx_websocket.py      # 主程序
├── requirements.txt       # Python 依赖
├── railway.json          # Railway 配置文件
├── render.yaml           # Render 配置文件
├── .env.example          # 环境变量示例
└── README.md             # 本文档
```

---

## 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量（Windows）
set BOT_ID=你的机器人ID
set SECRET=你的机器人密钥
set HEFENG_API_KEY=你的API密钥
set CITY_ID=101080101
set CITY_NAME=呼和浩特
set SCHEDULE_TIME=08:00
set SCHEDULE_CHAT_ID=你的群聊ID
set SCHEDULE_CHAT_TYPE=2

# 运行
python qywx_websocket.py
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

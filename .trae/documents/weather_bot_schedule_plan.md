# 天气机器人定时推送实现计划

## 目标
在企业微信WebSocket客户端中集成天气推送功能，实现定时自动发送天气信息到指定群聊。

## 现有代码分析

### 已有功能
1. **qywx_websocket.py** - WebSocket客户端
   - ✅ WebSocket连接和订阅认证
   - ✅ 心跳保活机制
   - ✅ 消息接收和解析
   - ❌ 主动发送消息功能（需要添加）
   - ❌ 定时任务（需要添加）

2. **wechat_weather.py** - 天气获取
   - ✅ 和风天气API调用
   - ✅ 天气数据格式化
   - ❌ WebSocket消息发送（需要改造）

## 实现步骤

### 步骤1：整合天气获取功能到WebSocket客户端
- 将 `wechat_weather.py` 中的天气API函数迁移到 `qywx_websocket.py`
- 添加配置项：城市ID、城市名称、和风天气API密钥

### 步骤2：实现主动发送消息功能
根据企业微信AI Bot协议，使用 `aibot_send_msg` 命令发送消息：
```python
def send_message(ws, chatid, chat_type, content):
    """
    通过WebSocket主动发送消息
    - chatid: 会话ID（群聊ID或用户ID）
    - chat_type: 1=单聊, 2=群聊
    - content: 消息内容（支持Markdown格式）
    """
```

### 步骤3：添加定时任务功能
使用Python的 `schedule` 库或 `threading.Timer` 实现定时推送：
- 配置推送时间（如每天早上8:00）
- 在独立线程中运行定时任务
- 定时触发天气获取和消息发送

### 步骤4：配置管理
添加可配置项：
- 定时推送时间
- 推送目标群聊ID
- 城市配置

### 步骤5：消息格式优化
使用Markdown格式美化天气推送消息：
- 标题加粗
- 分段清晰
- 添加emoji图标（可选）

## 技术方案

### 主动发送消息协议
```json
{
    "cmd": "aibot_send_msg",
    "headers": {
        "req_id": "唯一请求ID"
    },
    "body": {
        "chatid": "目标群聊ID或用户ID",
        "chat_type": 2,
        "msgtype": "markdown",
        "markdown": {
            "content": "天气消息内容"
        }
    }
}
```

### 定时任务实现
```python
import schedule
import threading

def schedule_weather_push(ws, chatid, push_time="08:00"):
    def job():
        weather_data = get_weather_info()
        send_weather_message(ws, chatid, weather_data)
    
    schedule.every().day.at(push_time).do(job)
    
    while True:
        schedule.run_pending()
        time.sleep(60)
```

## 文件修改清单

| 文件 | 修改内容 |
|------|----------|
| `qywx_websocket.py` | 添加天气API、主动发送消息、定时任务功能 |
| `wechat_weather.py` | 保留作为独立脚本，或删除（功能已整合） |

## 预期效果
1. WebSocket客户端启动后自动连接并订阅
2. 到达设定时间后自动获取天气信息
3. 自动发送格式化的天气消息到指定群聊
4. 同时保留接收用户消息的能力

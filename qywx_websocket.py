import websocket
import json
import time
import threading
import uuid
import ssl
import requests
import os
import logging
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

# 导入新版功能
from services.weather_service import WeatherService
from services.semantic_engine import SemanticEngine
from services.llm_service import LLMService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

# 东八区时区
BEIJING_TZ = timezone(timedelta(hours=8))

def get_beijing_time():
    """获取东八区时间"""
    return datetime.now(tz=BEIJING_TZ)

def format_beijing_time(format_str="%Y-%m-%d %H:%M:%S"):
    """格式化东八区时间"""
    return get_beijing_time().strftime(format_str)

def get_beijing_date_str():
    """获取东八区日期字符串 (YYYY-MM-DD)"""
    return get_beijing_time().strftime("%Y-%m-%d")

# 配置项
BOT_ID = os.getenv("BOT_ID", "aibq4IJma9oTpus6NeE6--WVJtJaK_0O3wN")
SECRET = os.getenv("SECRET", "ST6Ytrm7M1BAlVOCVxuGwMKrNg7hoWR3rStapaIak9D")
WS_URL = "wss://openws.work.weixin.qq.com"

HEFENG_API_KEY = os.getenv("HEFENG_API_KEY", "bb4de13c914d421a9aa4f255df9de5c9")
CITY_ID = os.getenv("CITY_ID", "101080101")
CITY_NAME = os.getenv("CITY_NAME", "呼和浩特")

SCHEDULE_TIME = os.getenv("SCHEDULE_TIME", "08:00")
SCHEDULE_CHAT_ID = os.getenv("SCHEDULE_CHAT_ID", "wrpv4ybQAA1abzhZBJZ8SaOVZIb5u9NA")
SCHEDULE_CHAT_TYPE = int(os.getenv("SCHEDULE_CHAT_TYPE", "2"))

MAX_RECONNECT_ATTEMPTS = 10
RECONNECT_DELAY_BASE = 1
RECONNECT_DELAY_CAP = 30

ws_instance = None
subscribe_timeout = None

# 初始化新版服务
weather_service = WeatherService()
semantic_engine = SemanticEngine()
llm_service = LLMService()
scheduler = BackgroundScheduler(timezone='Asia/Shanghai')

def generate_req_id():
    return str(uuid.uuid4()).replace("-", "")

def send_weather_to_chat(ws, chat_id, chat_type, auto_reply=True):
    """发送天气消息到聊天（使用新版 LLM）"""
    try:
        logger.info(f"{'='*50}")
        logger.info(f"{'[自动回复]' if auto_reply else '[定时任务]'} 开始获取天气信息...")
        logger.info(f"{'='*50}")
        
        # 获取完整天气数据
        weather_data = weather_service.get_complete_weather()
        if not weather_data:
            logger.error("获取天气数据失败")
            return
        
        # 语义分析
        semantic_result = semantic_engine.analyze(weather_data)
        semantic_tags = semantic_result.get("weather_tags", [])
        
        # 构建 LLM 提示变量
        weather_variables = {
            "city_name": weather_data.city_name,
            "now_temp": weather_data.now.temp if weather_data.now else "N/A",
            "now_weather": weather_data.now.weather if weather_data.now else "N/A",
            "now_humidity": weather_data.now.humidity if weather_data.now else "N/A",
            "now_wind": f"{weather_data.now.windDir} {weather_data.now.windScale}级" if weather_data.now else "N/A",
            "tomorrow_weather": weather_data.daily.tomorrow_text_day if weather_data.daily else "N/A",
            "tomorrow_temp_max": weather_data.daily.tomorrow_temp_max if weather_data.daily else "N/A",
            "tomorrow_temp_min": weather_data.daily.tomorrow_temp_min if weather_data.daily else "N/A",
            "dressing_index": weather_data.indices.dressing if weather_data.indices else "N/A",
            "uv_index": weather_data.indices.uv if weather_data.indices else "N/A",
            "sport_index": weather_data.indices.sport if weather_data.indices else "N/A",
            "cold_index": weather_data.indices.cold if weather_data.indices else "N/A",
            "semantic_tags": "、".join(semantic_tags) if semantic_tags else "无特殊提醒",
            "date": get_beijing_date_str()
        }
        
        # 生成天气提醒
        alert_content = llm_service.generate_alert(weather_variables)
        if not alert_content:
            logger.error("LLM 生成提醒失败")
            return
        
        # 发送消息
        send_message(ws, chat_id, chat_type, alert_content)
        logger.info(f"{'[自动回复]' if auto_reply else '[定时任务]'} 天气推送完成")
        
    except Exception as e:
        logger.error(f"获取天气失败: {e}", exc_info=True)

def send_message(ws, chat_id, chat_type, content):
    """发送消息到企业微信"""
    if not ws or not ws.sock or not ws.sock.connected:
        logger.error("WebSocket 未连接，无法发送消息")
        return False
    
    req_id = generate_req_id()
    message = {
        "cmd": "aibot_send_msg",
        "headers": {
            "req_id": req_id
        },
        "body": {
            "chatid": chat_id,
            "chat_type": chat_type,
            "msgtype": "markdown",
            "markdown": {
                "content": content
            }
        }
    }
    
    try:
        ws.send(json.dumps(message))
        logger.info(f"发送消息成功: req_id={req_id}")
        return True
    except Exception as e:
        logger.error(f"发送消息失败: {e}")
        return False

def on_open(ws):
    global ws_instance, subscribe_timeout
    ws_instance = ws
    logger.info(f"[{format_beijing_time()}] WebSocket 连接已建立")
    
    def on_subscribe_timeout():
        global ws_instance
        logger.warning(f"[{format_beijing_time()}] 订阅超时，强制断开连接重连")
        if ws_instance and ws_instance.sock and ws_instance.sock.connected:
            ws_instance.close()
    
    subscribe_timeout = threading.Timer(30, on_subscribe_timeout)
    subscribe_timeout.start()
    
    send_subscribe(ws)

def send_subscribe(ws):
    req_id = generate_req_id()
    subscribe_msg = {
        "cmd": "aibot_subscribe",
        "headers": {
            "req_id": req_id,
            "timestamp": int(time.time())
        },
        "body": {
            "bot_id": BOT_ID,
            "secret": SECRET
        }
    }
    try:
        ws.send(json.dumps(subscribe_msg))
        logger.info(f"[{format_beijing_time()}] 发送订阅请求: req_id={req_id}")
    except Exception as e:
        logger.error(f"发送订阅请求失败: {e}")

def handle_user_message(ws, body):
    msgtype = body.get('msgtype', '')
    chat_type = body.get('chattype', '')
    chat_id = body.get('chatid', '')
    from_user = body.get('from', {}).get('userid', '')
    
    logger.info(f"\n{'='*50}")
    logger.info(f"[新消息] 收到用户消息")
    logger.info(f"{'='*50}")
    logger.info(f"发送者: {from_user}")
    logger.info(f"会话类型: {'群聊' if chat_type == 'group' else '单聊'}")
    logger.info(f"会话ID: {chat_id}")
    logger.info(f"消息类型: {msgtype}")
    
    if msgtype == 'text':
        content = body.get('text', {}).get('content', '')
        logger.info(f"内容: {content}")
        
        if '天气' in content or '天气预报' in content:
            logger.info(f"[自动回复] 检测到天气关键词，发送天气信息...")
            send_weather_to_chat(ws, chat_id, 2 if chat_type == 'group' else 1, auto_reply=True)
        
        return content
    elif msgtype == 'mixed':
        msg_items = body.get('mixed', {}).get('msg_item', [])
        for item in msg_items:
            if item.get('msgtype') == 'text':
                text_content = item.get('text', {}).get('content', '')
                logger.info(f"内容: {text_content}")
                if '天气' in text_content:
                    logger.info(f"[自动回复] 检测到天气关键词，发送天气信息...")
                    send_weather_to_chat(ws, chat_id, 2 if chat_type == 'group' else 1, auto_reply=True)
        return "[混合消息]"
    else:
        logger.info(f"其他消息类型: {msgtype}")
        return f"[{msgtype}消息]"

def on_message(ws, message):
    global subscribe_timeout
    try:
        data = json.loads(message)
        cmd = data.get('cmd', '')
        req_id = data.get('headers', {}).get('req_id', 'N/A')
        
        if cmd == 'ping':
            # 响应心跳
            pong_msg = {
                "cmd": "pong",
                "headers": {
                    "req_id": req_id
                }
            }
            ws.send(json.dumps(pong_msg))
        elif cmd == 'aibot_msg_callback':
            # 处理用户消息
            handle_user_message(ws, data.get('body', {}))
        elif data.get('errcode') == 0:
            logger.info(f"[{format_beijing_time()}] 收到消息: req_id={req_id}, 状态: 成功")
            # 订阅成功，取消超时定时器
            if subscribe_timeout:
                subscribe_timeout.cancel()
                subscribe_timeout = None
                logger.info("订阅成功，取消超时定时器")
        else:
            logger.error(f"[{format_beijing_time()}] 收到消息: req_id={req_id}, 错误码: {data.get('errcode')}, 错误信息: {data.get('errmsg')}")
    except json.JSONDecodeError:
        logger.error(f"收到非 JSON 消息: {message[:100]}...")
    except Exception as e:
        logger.error(f"处理消息失败: {e}", exc_info=True)

def on_error(ws, error):
    logger.error(f"WebSocket 错误: {error}")

def on_close(ws, close_status_code, close_msg):
    global ws_instance
    logger.info(f"[{format_beijing_time()}] WebSocket 连接已关闭: status_code={close_status_code}, message={close_msg}")
    ws_instance = None
    
    # 尝试重连
    def reconnect():
        attempt = 0
        while attempt < MAX_RECONNECT_ATTEMPTS:
            attempt += 1
            delay = min(RECONNECT_DELAY_BASE * (2 ** (attempt - 1)), RECONNECT_DELAY_CAP)
            logger.info(f"[{format_beijing_time()}] 尝试重连 (第 {attempt}/{MAX_RECONNECT_ATTEMPTS} 次)，等待 {delay} 秒...")
            time.sleep(delay)
            
            try:
                start_ws()
                return
            except Exception as e:
                logger.error(f"重连失败: {e}")
    
    threading.Thread(target=reconnect, daemon=True).start()

def start_ws():
    """启动 WebSocket 连接"""
    ws = websocket.WebSocketApp(
        WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    ws.run_forever(
        sslopt={"cert_reqs": ssl.CERT_NONE},
        ping_interval=0,
        ping_timeout=99999,
        suppress_origin=True
    )

def scheduled_weather_push():
    """定时推送天气"""
    logger.info(f"{'='*50}")
    logger.info(f"[定时任务] 开始执行天气推送")
    logger.info(f"{'='*50}")
    
    if ws_instance and ws_instance.sock and ws_instance.sock.connected:
        send_weather_to_chat(ws_instance, SCHEDULE_CHAT_ID, SCHEDULE_CHAT_TYPE, auto_reply=False)
    else:
        logger.warning("WebSocket 未连接，无法执行定时推送")

def main():
    print(f"\n{'='*60}")
    print("企业微信天气机器人 (整合版)")
    print(f"Bot ID: {BOT_ID[:20]}...")
    print(f"定时推送: 每天 {SCHEDULE_TIME} (北京时间)")
    print(f"推送目标: {SCHEDULE_CHAT_ID[:20]}...")
    print(f"{'='*60}\n")
    
    # 配置定时任务
    try:
        hour, minute = map(int, SCHEDULE_TIME.split(':'))
        scheduler.add_job(
            scheduled_weather_push,
            'cron',
            hour=hour,
            minute=minute,
            timezone='Asia/Shanghai'
        )
        scheduler.start()
        logger.info(f"定时任务已设置: 每天 {SCHEDULE_TIME} 推送天气")
    except Exception as e:
        logger.error(f"设置定时任务失败: {e}", exc_info=True)
    
    # 启动 WebSocket
    try:
        start_ws()
    except KeyboardInterrupt:
        logger.info("收到停止信号")
    except Exception as e:
        logger.error(f"WebSocket 启动失败: {e}", exc_info=True)
    finally:
        if scheduler.running:
            scheduler.shutdown()

if __name__ == "__main__":
    main()

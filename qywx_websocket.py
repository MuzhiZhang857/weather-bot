import websocket
import json
import time
import threading
import uuid
import ssl
import requests
import schedule
import os
from datetime import datetime

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

def generate_req_id():
    return str(uuid.uuid4()).replace("-", "")

def get_weather_now(location):
    url = "https://mg5u9xcaf3.re.qweatherapi.com/v7/weather/now"
    params = {"location": location, "key": HEFENG_API_KEY}
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    if data.get("code") != "200":
        raise Exception(f"和风天气API错误: {data.get('msg', '未知错误')}")
    weather_info = data.get("now", {})
    return {
        "temp": weather_info.get("temp", "N/A"),
        "feelsLike": weather_info.get("feelsLike", "N/A"),
        "weather": weather_info.get("text", "N/A"),
        "windDir": weather_info.get("windDir", "N/A"),
        "windScale": weather_info.get("windScale", "N/A"),
        "humidity": weather_info.get("humidity", "N/A"),
    }

def get_weather_7d(location):
    url = "https://mg5u9xcaf3.re.qweatherapi.com/v7/weather/7d"
    params = {"location": location, "key": HEFENG_API_KEY}
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    if data.get("code") != "200":
        raise Exception(f"和风天气API错误: {data.get('msg', '未知错误')}")
    daily_list = data.get("daily", [])
    if len(daily_list) >= 2:
        tomorrow = daily_list[1]
        return {
            "tomorrow_text_day": tomorrow.get("textDay", "N/A"),
            "tomorrow_temp_max": tomorrow.get("tempMax", "N/A"),
            "tomorrow_temp_min": tomorrow.get("tempMin", "N/A"),
        }
    return {}

def get_indices(location):
    url = "https://mg5u9xcaf3.re.qweatherapi.com/v7/indices/1d"
    params = {"location": location, "key": HEFENG_API_KEY, "type": "1,2,3,5,6,8,9"}
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    if data.get("code") != "200":
        raise Exception(f"和风天气API错误: {data.get('msg', '未知错误')}")
    indices_list = data.get("daily", [])
    indices_data = {}
    for item in indices_list:
        category = item.get("category", "")
        if category == "穿衣指数":
            indices_data["dressing"] = item.get("text", "N/A")
        elif category == "紫外线指数":
            indices_data["uv"] = item.get("text", "N/A")
        elif category == "舒适度指数":
            indices_data["comfort"] = item.get("text", "N/A")
        elif category == "感冒指数":
            indices_data["cold"] = item.get("text", "N/A")
    return indices_data

def get_clothing_advice(temp, weather, dressing_index):
    try:
        temp = int(temp)
    except (ValueError, TypeError):
        return "【穿衣】建议根据天气情况适当穿衣"

    if dressing_index and dressing_index != "N/A":
        return f"【穿衣】{dressing_index}"

    if temp < 0:
        return "【穿衣】极冷，需羽绒服、围巾、手套保暖"
    elif temp < 10:
        return "【穿衣】较冷，建议穿毛衣、外套"
    elif temp < 20:
        return "【穿衣】凉爽，适合夹克、薄毛衣"
    elif temp < 26:
        return "【穿衣】舒适，适合单衣或薄外套"
    else:
        return "【穿衣】炎热，建议穿短袖，注意防暑"

def format_weather_message(weather_now, weather_7d, indices, advice):
    date_str = datetime.now().strftime("%Y-%m-%d")
    content = f"""**{date_str} {CITY_NAME}天气推送**

**当前天气**: {weather_now['weather']}
**温度**: {weather_now['temp']}°C (体感 {weather_now['feelsLike']}°C)
**风力**: {weather_now['windDir']} {weather_now['windScale']}级
**湿度**: {weather_now['humidity']}%

**明日预报**: {weather_7d.get('tomorrow_text_day', 'N/A')}
**温度**: {weather_7d.get('tomorrow_temp_min', 'N/A')}~{weather_7d.get('tomorrow_temp_max', 'N/A')}°C

{advice}

**紫外线指数**: {indices.get('uv', 'N/A')}
**舒适度指数**: {indices.get('comfort', 'N/A')}
**感冒指数**: {indices.get('cold', 'N/A')}"""
    return content

def send_message(ws, chatid, chat_type, content):
    if not ws or not ws.sock or not ws.sock.connected:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] WebSocket未连接，无法发送消息")
        return False
    
    req_id = generate_req_id()
    message = {
        "cmd": "aibot_send_msg",
        "headers": {
            "req_id": req_id
        },
        "body": {
            "chatid": chatid,
            "chat_type": chat_type,
            "msgtype": "markdown",
            "markdown": {
                "content": content
            }
        }
    }
    
    try:
        ws.send(json.dumps(message))
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 发送消息: req_id={req_id}")
        return True
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 发送消息失败: {e}")
        return False

def send_weather_to_chat(ws, chatid, chat_type):
    print(f"\n{'='*50}")
    print(f"[定时任务] 开始获取天气信息...")
    print(f"{'='*50}")
    
    try:
        weather_now = get_weather_now(CITY_ID)
        print(f"  当前天气: {weather_now['weather']}, 温度: {weather_now['temp']}°C")
        
        weather_7d = get_weather_7d(CITY_ID)
        print(f"  明日天气: {weather_7d.get('tomorrow_text_day', 'N/A')}")
        
        indices = get_indices(CITY_ID)
        advice = get_clothing_advice(weather_now["temp"], weather_now["weather"], indices.get("dressing"))
        
        content = format_weather_message(weather_now, weather_7d, indices, advice)
        
        send_message(ws, chatid, chat_type, content)
        print(f"[定时任务] 天气推送完成")
        
    except Exception as e:
        print(f"[定时任务] 获取天气失败: {e}")

def on_open(ws):
    global ws_instance
    ws_instance = ws
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] WebSocket 连接已建立")
    send_subscribe(ws)
    
def send_subscribe(ws):
    req_id = generate_req_id()
    subscribe_msg = {
        "cmd": "aibot_subscribe",
        "headers": {
            "req_id": req_id
        },
        "body": {
            "bot_id": BOT_ID,
            "secret": SECRET
        }
    }
    try:
        ws.send(json.dumps(subscribe_msg))
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 发送订阅请求: req_id={req_id}")
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 发送订阅请求失败: {e}")

def handle_user_message(ws, body):
    msgtype = body.get('msgtype', '')
    chattype = body.get('chattype', '')
    chatid = body.get('chatid', '')
    from_user = body.get('from', {}).get('userid', '')
    
    print(f"\n{'='*50}")
    print(f"[新消息] 收到用户消息")
    print(f"{'='*50}")
    print(f"发送者: {from_user}")
    print(f"会话类型: {'群聊' if chattype == 'group' else '单聊'}")
    print(f"会话ID: {chatid}")
    print(f"消息类型: {msgtype}")
    
    if msgtype == 'text':
        content = body.get('text', {}).get('content', '')
        print(f"内容: {content}")
        
        if '天气' in content or '天气预报' in content:
            print(f"[自动回复] 检测到天气关键词，发送天气信息...")
            send_weather_to_chat(ws, chatid, 2 if chattype == 'group' else 1)
        
        return content
    elif msgtype == 'mixed':
        msg_items = body.get('mixed', {}).get('msg_item', [])
        for item in msg_items:
            if item.get('msgtype') == 'text':
                text_content = item.get('text', {}).get('content', '')
                print(f"内容: {text_content}")
                if '天气' in text_content:
                    print(f"[自动回复] 检测到天气关键词，发送天气信息...")
                    send_weather_to_chat(ws, chatid, 2 if chattype == 'group' else 1)
        return "[混合消息]"
    else:
        print(f"其他消息类型: {msgtype}")
        return f"[{msgtype}消息]"

def on_message(ws, message):
    try:
        data = json.loads(message)
        
        if data.get('errcode') == 0:
            pass
        elif data.get('errcode') != 0:
            print(f"    错误码: {data.get('errcode')}")
            print(f"    错误信息: {data.get('errmsg', '未知错误')}")
            
        cmd = data.get('cmd', '')
        if cmd == 'aibot_msg_callback':
            body = data.get('body', {})
            handle_user_message(ws, body)
            
        elif cmd == 'aibot_event_callback':
            event_type = data.get('body', {}).get('event', {}).get('type', '')
            print(f"    收到事件: {event_type}")
            
        elif cmd == 'pong':
            pass
            
    except json.JSONDecodeError:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 收到非JSON消息: {message}")

def on_error(ws, error):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 错误: {error}")

def on_close(ws, close_status_code, close_msg):
    global ws_instance
    ws_instance = None
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] WebSocket 连接已关闭")
    print(f"    状态码: {close_status_code}")
    print(f"    原因: {close_msg}")

def send_heartbeat(ws):
    while True:
        try:
            if ws.sock and ws.sock.connected:
                req_id = generate_req_id()
                heartbeat = {
                    "cmd": "ping",
                    "headers": {
                        "req_id": req_id
                    }
                }
                ws.send(json.dumps(heartbeat))
            time.sleep(30)
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 心跳发送失败: {e}")
            break

def schedule_task(ws):
    def job():
        if ws and ws.sock and ws.sock.connected:
            send_weather_to_chat(ws, SCHEDULE_CHAT_ID, SCHEDULE_CHAT_TYPE)
    
    schedule.every().day.at(SCHEDULE_TIME).do(job)
    print(f"[定时任务] 已设置每天 {SCHEDULE_TIME} 推送天气到群聊")
    
    while True:
        schedule.run_pending()
        time.sleep(60)

def connect_with_reconnect():
    reconnect_count = 0
    
    while reconnect_count < MAX_RECONNECT_ATTEMPTS:
        try:
            print(f"\n{'='*60}")
            print(f"企业微信天气机器人启动")
            print(f"Bot ID: {BOT_ID}")
            print(f"定时推送: 每天 {SCHEDULE_TIME}")
            print(f"推送目标: {SCHEDULE_CHAT_ID}")
            print(f"{'='*60}")
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 正在连接 WebSocket (第 {reconnect_count + 1} 次尝试)...")
            
            ws = websocket.WebSocketApp(
                WS_URL,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )
            
            heartbeat_thread = threading.Thread(target=send_heartbeat, args=(ws,), daemon=True)
            heartbeat_thread.start()
            
            schedule_thread = threading.Thread(target=schedule_task, args=(ws,), daemon=True)
            schedule_thread.start()
            
            ws.run_forever(
                sslopt={"cert_reqs": ssl.CERT_NONE},
                ping_interval=0,
                ping_timeout=99999,
                suppress_origin=True
            )
            
            reconnect_count += 1
            if reconnect_count < MAX_RECONNECT_ATTEMPTS:
                delay = min(RECONNECT_DELAY_BASE * (2 ** (reconnect_count - 1)), RECONNECT_DELAY_CAP)
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 连接断开，{delay}秒后尝试重新连接...")
                time.sleep(delay)
            
        except KeyboardInterrupt:
            print("\n用户中断，退出程序")
            return
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 连接失败: {e}")
            reconnect_count += 1
            if reconnect_count < MAX_RECONNECT_ATTEMPTS:
                delay = min(RECONNECT_DELAY_BASE * (2 ** (reconnect_count - 1)), RECONNECT_DELAY_CAP)
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {delay}秒后尝试重新连接...")
                time.sleep(delay)
    
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 已达到最大重连次数 ({MAX_RECONNECT_ATTEMPTS})，退出程序")

if __name__ == "__main__":
    try:
        connect_with_reconnect()
    except KeyboardInterrupt:
        print("\n用户中断，退出程序")

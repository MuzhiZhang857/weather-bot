import os
import sys
import time
import threading

# 在导入任何其他模块前，先清除所有代理环境变量！
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)

import logging
import argparse
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

load_dotenv()

CST = timezone(timedelta(hours=8))


def setup_logging():
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    if logger.handlers:
        logger.handlers.clear()
    
    class CSTFormatter(logging.Formatter):
        def formatTime(self, record, datefmt=None):
            dt = datetime.fromtimestamp(record.created, tz=CST)
            if datefmt:
                s = dt.strftime(datefmt)
            else:
                s = dt.isoformat(timespec='milliseconds')
            return s
    
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "weather_bot.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = CSTFormatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = CSTFormatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    parser = argparse.ArgumentParser(description="天气机器人")
    parser.add_argument(
        "--mode",
        type=str,
        default="scheduled",
        choices=["scheduled", "once", "listen", "both"],
        help="运行模式: scheduled (定时运行), once (单次运行), listen (消息监听), both (定时+监听)"
    )
    
    args = parser.parse_args()
    
    try:
        if args.mode in ["listen", "both"]:
            from services.push_service import PushService, PushMessage, ChatType
            from services.weather_service import WeatherService
            from services.semantic_engine import SemanticEngine
            from services.llm_service import LLMService
            
            logger.info(f"启动消息监听模式: {args.mode}")
            
            push_service = PushService()
            weather_service = WeatherService()
            semantic_engine = SemanticEngine()
            llm_service = LLMService()
            
            chat_id = os.getenv("SCHEDULE_CHAT_ID", "")
            chat_type = ChatType(int(os.getenv("SCHEDULE_CHAT_TYPE", "2")))
            
            def send_via_response_url(response_url: str, content: str):
                """通过 response_url 发送回复（企业微信 webhook 模式）"""
                try:
                    import requests
                    payload = {
                        "msgtype": "markdown",
                        "markdown": {
                            "content": content
                        }
                    }
                    response = requests.post(response_url, json=payload, timeout=10)
                    if response.status_code == 200:
                        logger.info("通过 response_url 发送回复成功")
                    else:
                        logger.error(f"通过 response_url 发送回复失败: {response.status_code} - {response.text}")
                except Exception as e:
                    logger.error(f"通过 response_url 发送回复出错: {str(e)}")
            
            def handle_message(message_body):
                """处理收到的 @ 消息"""
                try:
                    logger.info(f"收到消息: {message_body}")
                    
                    content = message_body.get("text", {}).get("content", "").strip()
                    response_url = message_body.get("response_url", "")
                    
                    if not content and not response_url:
                        logger.warning("消息内容为空且无 response_url")
                        return
                    
                    if not response_url:
                        logger.warning("缺少 response_url，无法发送回复")
                        return
                    
                    weather_data = weather_service.get_complete_weather()
                    if not weather_data:
                        reply = "抱歉，获取天气信息失败，请稍后重试。"
                        send_via_response_url(response_url, reply)
                        return
                    
                    semantic_result = semantic_engine.analyze(weather_data)
                    semantic_tags = semantic_result.get("weather_tags", [])
                    
                    def get_time_of_day():
                        """根据当前时间（北京时间）返回时段问候"""
                        hour = datetime.now(CST).hour
                        if 6 <= hour < 9:
                            return "早晨"
                        elif 9 <= hour < 12:
                            return "上午"
                        elif 12 <= hour < 14:
                            return "中午"
                        elif 14 <= hour < 18:
                            return "下午"
                        elif 18 <= hour < 22:
                            return "傍晚"
                        else:
                            return "晚上"

                    now_cst = datetime.now(CST)
                    variables = {
                        "city_name": weather_data.city_name,
                        "date": now_cst.strftime("%Y年%m月%d日"),
                        "time_of_day": get_time_of_day(),
                        "current_time": now_cst.strftime("%H:%M"),
                        "weather": weather_data.now.weather if weather_data.now else "N/A",
                        "temp": weather_data.now.temp if weather_data.now else "N/A",
                        "feels_like": weather_data.now.feelsLike if weather_data.now else "N/A",
                        "humidity": weather_data.now.humidity if weather_data.now else "N/A",
                        "wind_dir": weather_data.now.windDir if weather_data.now else "N/A",
                        "wind_scale": weather_data.now.windScale if weather_data.now else "N/A",
                        "tomorrow_weather": weather_data.daily.tomorrow_text_day if weather_data.daily else "N/A",
                        "tomorrow_temp_max": weather_data.daily.tomorrow_temp_max if weather_data.daily else "N/A",
                        "tomorrow_temp_min": weather_data.daily.tomorrow_temp_min if weather_data.daily else "N/A",
                        "dressing_index": weather_data.indices.dressing if weather_data.indices else "N/A",
                        "uv_index": weather_data.indices.uv if weather_data.indices else "N/A",
                        "comfort_index": weather_data.indices.comfort if weather_data.indices else "N/A",
                        "sport_index": weather_data.indices.sport if weather_data.indices else "N/A",
                        "cold_index": weather_data.indices.cold if weather_data.indices else "N/A",
                        "alert_tags": "、".join(semantic_tags) if semantic_tags else "无特殊提醒",
                    }
                    
                    alert_content = llm_service.generate_alert(variables)
                    if alert_content:
                        send_via_response_url(response_url, alert_content)
                        logger.info("消息回复已发送")
                    else:
                        reply = "抱歉，生成天气提醒失败，请稍后重试。"
                        send_via_response_url(response_url, reply)
                        
                except Exception as e:
                    logger.error(f"处理消息时出错: {str(e)}", exc_info=True)
                    try:
                        if response_url:
                            send_via_response_url(response_url, f"处理消息时出错: {str(e)}")
                    except:
                        pass
            
            push_service.set_message_callback(handle_message)
            
            if push_service.connect_websocket():
                logger.info("WebSocket 连接成功，进入消息监听模式")
                
                if args.mode == "both":
                    from services.scheduler import WeatherScheduler
                    scheduler = WeatherScheduler()
                    scheduler_thread = threading.Thread(
                        target=scheduler.start_scheduled,
                        daemon=True
                    )
                    scheduler_thread.start()
                    logger.info("定时推送任务已在后台启动")
                
                while True:
                    time.sleep(1)
            else:
                logger.error("WebSocket 连接失败，无法进入消息监听模式")
                sys.exit(1)
        
        else:
            from services.scheduler import WeatherScheduler
            
            scheduler = WeatherScheduler()
            
            if args.mode == "once":
                logger.info("运行模式: 单次执行")
                scheduler.run_once()
            else:
                logger.info("运行模式: 定时执行")
                scheduler.start_scheduled()
                
    except ImportError as e:
        logger.error(f"导入模块失败: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"程序运行异常: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

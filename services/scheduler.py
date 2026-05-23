import os
import logging
from typing import Optional, List, Dict, Any
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

from services.weather_service import WeatherService
from services.semantic_engine import SemanticEngine
from services.llm_service import LLMService
from services.push_service import PushService, PushMessage, ChatType

load_dotenv()

CST = timezone(timedelta(hours=8))

logger = logging.getLogger(__name__)


class WeatherScheduler:
    def __init__(self):
        self.weather_service = WeatherService()
        self.semantic_engine = SemanticEngine()
        self.llm_service = LLMService()
        self.push_service = PushService()
        
        self.chat_id = os.getenv("SCHEDULE_CHAT_ID", "")
        self.chat_type = ChatType(int(os.getenv("SCHEDULE_CHAT_TYPE", "2")))
        self.schedule_time = os.getenv("SCHEDULE_TIME", "08:00")
        
        self.scheduler = BlockingScheduler()
        logger.info("WeatherScheduler 初始化完成")
    
    def _build_weather_variables(self, weather_data, semantic_tags: List[str]) -> Dict[str, str]:
        variables = {
            "city_name": weather_data.city_name,
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
        return variables
    
    def execute_workflow(self) -> None:
        logger.info("=" * 50)
        logger.info("开始执行完整天气推送工作流")
        logger.info("=" * 50)
        
        try:
            weather_data = self.weather_service.get_complete_weather()
            if not weather_data:
                logger.error("获取天气数据失败，工作流终止")
                return
            
            semantic_result = self.semantic_engine.analyze(weather_data)
            semantic_tags = semantic_result.get("weather_tags", [])
            
            weather_variables = self._build_weather_variables(weather_data, semantic_tags)
            alert_content = self.llm_service.generate_alert(weather_variables)
            
            if not alert_content:
                logger.error("LLM 生成提醒失败，工作流终止")
                return
            
            if self.push_service.connect_websocket():
                message = PushMessage(
                    chat_id=self.chat_id,
                    chat_type=self.chat_type,
                    content=alert_content
                )
                success = self.push_service.send_message(message)
                if success:
                    logger.info("天气提醒推送成功")
                else:
                    logger.error("天气提醒推送失败")
                
                self.push_service.disconnect()
            else:
                logger.error("WebSocket 连接失败，无法推送消息")
            
            logger.info("完整工作流执行完成")
            
        except Exception as e:
            logger.error(f"工作流执行异常: {str(e)}", exc_info=True)
    
    def _parse_schedule_time(self) -> Dict[str, str]:
        time_parts = self.schedule_time.split(":")
        hour = time_parts[0] if len(time_parts) > 0 else "8"
        minute = time_parts[1] if len(time_parts) > 1 else "0"
        return {"hour": hour, "minute": minute}
    
    def start_scheduled(self) -> None:
        schedule_config = self._parse_schedule_time()
        logger.info(f"配置定时任务: 每天 {self.schedule_time} 执行")
        
        self.scheduler.add_job(
            self.execute_workflow,
            trigger=CronTrigger(
                hour=schedule_config["hour"],
                minute=schedule_config["minute"]
            ),
            id="weather_push_job",
            name="每日天气推送",
            replace_existing=True
        )
        
        try:
            logger.info("定时调度器启动，按 Ctrl+C 停止")
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("收到停止信号，关闭调度器")
            self.scheduler.shutdown()
    
    def run_once(self) -> None:
        logger.info("执行单次工作流")
        self.execute_workflow()

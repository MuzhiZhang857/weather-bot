"""
双城市天气监控 watchdog 脚本（供 Hermes 定时任务调用）。

契约：
  * 遍历配置的全部城市（呼和浩特、包头），各取完整天气（实况 + 7天 + 24h逐时 + 生活指数）
  * 用语义规则引擎判定命中（雨/雪/近期降水/大风/高温/低温/高湿/强紫外线/感冒…）
  * 命中任一规则 → 生成人话提醒（优先 LLM，失败自动降级到简单模板）
    并打印到 stdout —— stdout 只用于承载提醒，供上层网关投递微信
  * 全部未命中 → 不做任何打印（静默），正常退出

日志只写文件，避免污染 stdout（Hermes 会读取 stdout 作为消息体）。
"""
import os
import io
import sys
import argparse
import logging
from logging.handlers import RotatingFileHandler

# Windows 默认 stdout 用 gbk 编码，无法输出 emoji。这里强制 UTF-8，
# 否则命中提醒里的 emoji（☀️🌡️❄️…）会导致 UnicodeEncodeError 而整个脚本退出失败。
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# 在导入任何可能发起网络请求的模块前，先清除代理环境变量（国内网络必需）
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)

from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

load_dotenv()

CST = timezone(timedelta(hours=8))
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
LOG_FILE = os.path.join(LOG_DIR, "weather_bot.log")


def setup_logging():
    """仅文件日志：让 stdout 保持干净，只承载命中提醒的文本。"""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # 保持根 logger 干净，避免重复 handler 与泄漏到 stdout
    if logger.handlers:
        logger.handlers.clear()

    class CSTFormatter(logging.Formatter):
        def formatTime(self, record, datefmt=None):
            dt = datetime.fromtimestamp(record.created, tz=CST)
            if datefmt:
                return dt.strftime(datefmt)
            return dt.isoformat(timespec="milliseconds")

    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(CSTFormatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    logger.addHandler(file_handler)
    # 禁用可能把日志打印到 stdout 的默认 handler（如 `pythonw`/IDE 注入的 StreamHandler）
    logger.propagate = False


def get_time_of_day() -> str:
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
    return "晚上"


def build_weather_variables(weather_data, semantic_tags):
    now_cst = datetime.now(CST)
    def g(obj, attr, default="N/A"):
        return getattr(obj, attr, default) if obj else default
    return {
        "city_name": weather_data.city_name,
        "date": now_cst.strftime("%Y年%m月%d日"),
        "time_of_day": get_time_of_day(),
        "current_time": now_cst.strftime("%H:%M"),
        "weather": g(weather_data.now, "weather"),
        "temp": g(weather_data.now, "temp"),
        "feels_like": g(weather_data.now, "feelsLike"),
        "humidity": g(weather_data.now, "humidity"),
        "wind_dir": g(weather_data.now, "windDir"),
        "wind_scale": g(weather_data.now, "windScale"),
        "tomorrow_weather": g(weather_data.daily, "tomorrow_text_day"),
        "tomorrow_temp_max": g(weather_data.daily, "tomorrow_temp_max"),
        "tomorrow_temp_min": g(weather_data.daily, "tomorrow_temp_min"),
        "dressing_index": g(weather_data.indices, "dressing"),
        "uv_index": g(weather_data.indices, "uv"),
        "comfort_index": g(weather_data.indices, "comfort"),
        "sport_index": g(weather_data.indices, "sport"),
        "cold_index": g(weather_data.indices, "cold"),
        "alert_tags": "、".join(semantic_tags) if semantic_tags else "无特殊提醒",
    }


def apply_lead_hours(engine, lead_hours: int):
    """用 ALERT_LEAD_HOURS 覆盖 'precip_soon_in' 规则的提前量，让雨/雪提前判定可配置。"""
    for rule in engine.rules:
        cond = rule.condition
        if cond and isinstance(cond, dict) and cond.get("type") == "precip_soon_in":
            cond["value"] = lead_hours


def main():
    parser = argparse.ArgumentParser(description="双城市天气监控 watchdog")
    parser.add_argument(
        "--once",
        action="store_true",
        help="单次执行后退出（默认即如此，此参数仅用于显式手动测试）",
    )
    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("=" * 50)
    logger.info("weather_monitor 开始运行 (once=%s)", args.once)
    logger.info("=" * 50)

    from services.weather_service import WeatherService
    from services.semantic_engine import SemanticEngine
    from services.llm_service import LLMService
    from services.weather_state import WeatherState

    try:
        lead_hours = int(os.getenv("ALERT_LEAD_HOURS", "3"))
        service = WeatherService()
        engine = SemanticEngine()
        llm_service = LLMService()
        state_store = WeatherState()
        apply_lead_hours(engine, lead_hours)

        cities = service.get_cities()
        if not cities:
            logger.error("未解析到任何城市配置，退出")
            sys.exit(1)

        alerts = []
        for city in cities:
            city_id = city["id"]
            city_name = city["name"]
            logger.info(f"--- 处理城市: {city_name} ({city_id}) ---")

            weather_data = service.get_complete_weather(city_id, city_name)
            if not weather_data:
                logger.error(f"[{city_name}] 获取完整天气失败，跳过")
                continue

            result = engine.analyze(weather_data)
            tags = result.get("weather_tags", [])

            # 事件去重 + 状态记忆：登记新告警、同时解除本次不再命中的旧活动态
            new_tags = state_store.get_new_tags(city_id, tags)

            if not tags:
                logger.info(f"[{city_name}] 未命中任何预警规则，静默")
                continue

            if not new_tags:
                logger.info(f"[{city_name}] 命中但均为重复事件，保持静默去重: {tags}")
                continue

            logger.info(f"[{city_name}] 新告警事件: {new_tags}（本次完整命中: {tags}）")
            variables = build_weather_variables(weather_data, tags)
            content = llm_service.generate_alert(variables)
            if content:
                alerts.append(content)

        # 命中才打印到 stdout（供 Hermes 投递微信）；未命中则什么都不到，保持静默
        if alerts:
            print("\n\n".join(alerts))
            logger.info(f"共命中 {len(alerts)} 个城市提醒，已打印到 stdout")
        else:
            logger.info("所有城市均未命中预警规则，未输出任何内容（静默退出）")

        logger.info("weather_monitor 执行完成")

    except Exception as e:
        logger.error(f"weather_monitor 运行异常: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
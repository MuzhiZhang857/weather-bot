import os
import sys

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
        choices=["scheduled", "once"],
        help="运行模式: scheduled (定时运行) 或 once (单次运行)"
    )
    
    args = parser.parse_args()
    
    try:
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

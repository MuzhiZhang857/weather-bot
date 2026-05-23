import logging
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))


def now_cst() -> datetime:
    """获取当前东八区时间"""
    return datetime.now(CST)


def format_date_cst(date_format: str = "%Y年%m月%d日") -> str:
    """格式化东八区当前日期"""
    return now_cst().strftime(date_format)


def format_datetime_cst(date_format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """格式化东八区当前时间"""
    return now_cst().strftime(date_format)


class CSTFormatter(logging.Formatter):
    """自定义日志格式化器，使用东八区时间"""
    
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=CST)
        if datefmt:
            s = dt.strftime(datefmt)
        else:
            s = dt.isoformat(timespec='milliseconds')
        return s

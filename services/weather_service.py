import os
import logging
import requests
from typing import Optional
from dataclasses import asdict
from models.weather_types import (
    WeatherNow,
    DailyWeather,
    Weather7D,
    IndicesItem,
    IndicesData,
    WeatherData
)
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class WeatherService:
    def __init__(self):
        self.api_key = os.getenv("HEFENG_API_KEY")
        self.city_id = os.getenv("CITY_ID")
        self.city_name = os.getenv("CITY_NAME", "")
        self.base_url = "https://mg5u9xcaf3.re.qweatherapi.com/v7"
        self.timeout = 10

        if not self.api_key:
            logger.warning("HEFENG_API_KEY 未配置")
        if not self.city_id:
            logger.warning("CITY_ID 未配置")

    def _make_request(self, endpoint: str, params: dict) -> dict:
        url = f"{self.base_url}{endpoint}"
        params["key"] = self.api_key
        try:
            logger.debug(f"请求 API: {url}, params: {params}")
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            if data.get("code") != "200":
                logger.error(f"和风天气API错误: {data.get('msg', '未知错误')}")
                raise Exception(f"和风天气API错误: {data.get('msg', '未知错误')}")
            return data
        except requests.RequestException as e:
            logger.error(f"HTTP请求失败: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"请求处理失败: {str(e)}")
            raise

    def get_current_weather(self) -> Optional[WeatherNow]:
        if not self.api_key or not self.city_id:
            logger.error("缺少API密钥或城市ID未配置")
            return None

        try:
            data = self._make_request("/weather/now", {"location": self.city_id})
            weather_info = data.get("now", {})
            weather_now = WeatherNow(
                temp=weather_info.get("temp", "N/A"),
                feelsLike=weather_info.get("feelsLike", "N/A"),
                weather=weather_info.get("text", "N/A"),
                windDir=weather_info.get("windDir", "N/A"),
                windScale=weather_info.get("windScale", "N/A"),
                humidity=weather_info.get("humidity", "N/A"),
                pressure=weather_info.get("pressure"),
                vis=weather_info.get("vis"),
                cloud=weather_info.get("cloud"),
                dew=weather_info.get("dew"),
            )
            logger.info(f"获取当前天气成功: {weather_now.weather} {weather_now.temp}°C")
            return weather_now
        except Exception as e:
            logger.error(f"获取当前天气失败: {str(e)}")
            return None

    def get_weather_forecast(self) -> Optional[Weather7D]:
        if not self.api_key or not self.city_id:
            logger.error("缺少API密钥或城市ID未配置")
            return None

        try:
            data = self._make_request("/weather/7d", {"location": self.city_id})
            daily_list = data.get("daily", [])

            daily_weathers = []
            for item in daily_list:
                daily_weathers.append(
                    DailyWeather(
                        textDay=item.get("textDay", "N/A"),
                        textNight=item.get("textNight"),
                        tempMax=item.get("tempMax", "N/A"),
                        tempMin=item.get("tempMin", "N/A"),
                        windDirDay=item.get("windDirDay"),
                        windScaleDay=item.get("windScaleDay"),
                        windDirNight=item.get("windDirNight"),
                        windScaleNight=item.get("windScaleNight"),
                        fxDate=item.get("fxDate"),
                    )
                )

            tomorrow_text_day = "N/A"
            tomorrow_temp_max = "N/A"
            tomorrow_temp_min = "N/A"
            tomorrow_wind_dir = None
            tomorrow_wind_scale = None

            if len(daily_list) >= 2:
                tomorrow = daily_list[1]
                tomorrow_text_day = tomorrow.get("textDay", "N/A")
                tomorrow_temp_max = tomorrow.get("tempMax", "N/A")
                tomorrow_temp_min = tomorrow.get("tempMin", "N/A")
                tomorrow_wind_dir = tomorrow.get("windDirDay")
                tomorrow_wind_scale = tomorrow.get("windScaleDay")

            weather_7d = Weather7D(
                tomorrow_text_day=tomorrow_text_day,
                tomorrow_temp_max=tomorrow_temp_max,
                tomorrow_temp_min=tomorrow_temp_min,
                tomorrow_wind_dir=tomorrow_wind_dir,
                tomorrow_wind_scale=tomorrow_wind_scale,
                daily_list=daily_weathers,
            )
            logger.info(f"获取7天预报成功，共{len(daily_weathers)}天数据")
            return weather_7d
        except Exception as e:
            logger.error(f"获取7天预报失败: {str(e)}")
            return None

    def get_life_indices(self) -> Optional[IndicesData]:
        if not self.api_key or not self.city_id:
            logger.error("缺少API密钥或城市ID未配置")
            return None

        try:
            data = self._make_request("/indices/1d", {"location": self.city_id, "type": "1,2,3,5,6,8,9"})
            indices_list = data.get("daily", [])

            indices_items = []
            indices_data = IndicesData()

            for item in indices_list:
                category = item.get("category", "")
                text = item.get("text", "N/A")
                idx_item = IndicesItem(
                    category=category,
                    text=text,
                    type=item.get("type"),
                    level=item.get("level"),
                )
                indices_items.append(idx_item)

                if category == "穿衣指数":
                    indices_data.dressing = text
                elif category == "紫外线指数":
                    indices_data.uv = text
                elif category == "舒适度指数":
                    indices_data.comfort = text
                elif category == "运动指数":
                    indices_data.sport = text
                elif category == "感冒指数":
                    indices_data.cold = text
                elif category == "空气污染扩散条件指数":
                    indices_data.air_pollution = text
                elif category == "洗车指数":
                    indices_data.car_wash = text

            indices_data.all_items = indices_items
            logger.info(f"获取生活指数成功，共{len(indices_items)}项")
            return indices_data
        except Exception as e:
            logger.error(f"获取生活指数失败: {str(e)}")
            return None

    def get_complete_weather(self) -> Optional[WeatherData]:
        logger.info(f"开始获取{self.city_name}完整天气数据")

        weather_data = WeatherData(
            city_name=self.city_name,
            city_id=self.city_id,
        )

        try:
            weather_data.now = self.get_current_weather()
            weather_data.daily = self.get_weather_forecast()
            weather_data.indices = self.get_life_indices()

            logger.info(f"完整天气数据获取完成")
            return weather_data
        except Exception as e:
            logger.error(f"获取完整天气数据失败: {str(e)}")
            return None

import os
import logging
import requests
from typing import Optional, List, Dict
from models.weather_types import (
    WeatherNow,
    DailyWeather,
    Weather7D,
    WeatherHourly,
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
        self.base_url = "https://mg5u9xcaf3.re.qweatherapi.com/v7"
        self.timeout = 10

        if not self.api_key:
            logger.warning("HEFENG_API_KEY 未配置")

    # ---------------------------------------------------------------
    # 多城市配置解析
    # ---------------------------------------------------------------
    def get_cities(self) -> List[Dict[str, str]]:
        """从环境变量解析城市列表。

        CITY_SLUGS, 如: baotou=101080201,huhehaote=101080101
        CITY_NAMES（可选）, 如: baotou=包头,huhehaote=呼和浩特
        """
        slugs_raw = os.getenv("CITY_SLUGS", "").strip()
        if not slugs_raw:
            logger.warning("CITY_SLUGS 未配置，回退到单个 CITY_ID")
            city_id = os.getenv("CITY_ID", "").strip()
            if not city_id:
                logger.error("既无 CITY_SLUGS 也无 CITY_ID，城市配置为空")
                return []
            return [{"id": city_id, "name": os.getenv("CITY_NAME", city_id)}]

        names_map = {}
        names_raw = os.getenv("CITY_NAMES", "").strip()
        if names_raw:
            for part in names_raw.split(","):
                part = part.strip()
                if "=" in part:
                    slug, name = part.split("=", 1)
                    names_map[slug.strip()] = name.strip()

        cities = []
        for part in slugs_raw.split(","):
            part = part.strip()
            if not part:
                continue
            if "=" in part:
                slug, city_id = part.split("=", 1)
                slug = slug.strip()
                city_id = city_id.strip()
                name = names_map.get(slug, slug)
            else:
                city_id = part
                slug = city_id
                name = names_map.get(city_id, city_id)
            if city_id:
                cities.append({"id": city_id, "name": name or slug})

        logger.info(f"解析城市列表: {cities}")
        return cities

    # ---------------------------------------------------------------
    # HTTP 基础请求
    # ---------------------------------------------------------------
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

    def _guard(self, city_id: str) -> bool:
        if not self.api_key or not city_id:
            logger.error("缺少API密钥或城市ID未配置")
            return False
        return True

    def _get_city_id(self, city_id: str) -> str:
        if city_id:
            return city_id
        return os.getenv("CITY_ID", "")

    # ---------------------------------------------------------------
    # 各类型取数
    # ---------------------------------------------------------------
    def get_current_weather(self, city_id: Optional[str] = None) -> Optional[WeatherNow]:
        city_id = self._get_city_id(city_id)
        if not self._guard(city_id):
            return None

        try:
            data = self._make_request("/weather/now", {"location": city_id})
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
            logger.info(f"获取{city_id}当前天气成功: {weather_now.weather} {weather_now.temp}°C")
            return weather_now
        except Exception as e:
            logger.error(f"获取当前天气失败[{city_id}]: {str(e)}")
            return None

    def get_weather_forecast(self, city_id: Optional[str] = None) -> Optional[Weather7D]:
        city_id = self._get_city_id(city_id)
        if not self._guard(city_id):
            return None

        try:
            data = self._make_request("/weather/7d", {"location": city_id})
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
            logger.info(f"获取{city_id}7天预报成功，共{len(daily_weathers)}天数据")
            return weather_7d
        except Exception as e:
            logger.error(f"获取7天预报失败[{city_id}]: {str(e)}")
            return None

    def get_hourly_forecast(self, city_id: Optional[str] = None) -> List[WeatherHourly]:
        """获取24小时逐时预报（和风 /weather/24h）。

        返回按时间升序的逐时列表，用于雨/雪"未来几小时"提前判定。
        """
        city_id = self._get_city_id(city_id)
        if not self._guard(city_id):
            return []

        try:
            data = self._make_request("/weather/24h", {"location": city_id})
            hourly_list = data.get("hourly", [])

            result = []
            for item in hourly_list:
                result.append(
                    WeatherHourly(
                        fxTime=item.get("fxTime", ""),
                        text=item.get("text", "N/A"),
                        temp=item.get("temp", "N/A"),
                        pop=item.get("pop", "N/A"),
                        precip=item.get("precip", "N/A"),
                        windDir=item.get("windDir"),
                        windScale=item.get("windScale"),
                        humidity=item.get("humidity"),
                    )
                )
            logger.info(f"获取{city_id}24h逐时预报成功，共{len(result)}条")
            return result
        except Exception as e:
            logger.error(f"获取24h逐时预报失败[{city_id}]: {str(e)}")
            return []

    def get_life_indices(self, city_id: Optional[str] = None) -> Optional[IndicesData]:
        city_id = self._get_city_id(city_id)
        if not self._guard(city_id):
            return None

        try:
            data = self._make_request("/indices/1d", {"location": city_id, "type": "1,2,3,5,6,8,9"})
            indices_list = data.get("daily", [])

            indices_items = []
            indices_data = IndicesData()

            for item in indices_list:
                # 注意：和风 indices 接口里 name 才是指数种类（如“穿衣指数”），
                # category 是等级/评语（如“较适宜”）。旧代码误用 category 匹配导致取不到值。
                name = item.get("name") or item.get("category", "")
                text = item.get("text", "N/A")
                idx_item = IndicesItem(
                    category=name,
                    text=text,
                    type=item.get("type"),
                    level=item.get("level"),
                )
                indices_items.append(idx_item)

                if name == "穿衣指数":
                    indices_data.dressing = text
                elif name == "紫外线指数":
                    indices_data.uv = text
                elif name == "舒适度指数":
                    indices_data.comfort = text
                elif name == "运动指数":
                    indices_data.sport = text
                elif name == "感冒指数":
                    indices_data.cold = text
                elif name in ("空气污染扩散条件指数", "空气污染指数"):
                    indices_data.air_pollution = text
                elif name == "洗车指数":
                    indices_data.car_wash = text

            indices_data.all_items = indices_items
            logger.info(f"获取{city_id}生活指数成功，共{len(indices_items)}项")
            return indices_data
        except Exception as e:
            logger.error(f"获取生活指数失败[{city_id}]: {str(e)}")
            return None

    # ---------------------------------------------------------------
    # 完整取数（单城市）
    # ---------------------------------------------------------------
    def get_complete_weather(self, city_id: Optional[str] = None,
                             city_name: Optional[str] = None) -> Optional[WeatherData]:
        city_id = self._get_city_id(city_id)
        if not city_id:
            logger.error("缺少城市ID")
            return None
        if not city_name:
            city_name = city_id

        logger.info(f"开始获取[{city_name}]完整天气数据")

        weather_data = WeatherData(
            city_name=city_name,
            city_id=city_id,
        )

        try:
            weather_data.now = self.get_current_weather(city_id)
            weather_data.daily = self.get_weather_forecast(city_id)
            weather_data.hourly = self.get_hourly_forecast(city_id)
            weather_data.indices = self.get_life_indices(city_id)

            logger.info(f"[{city_name}]完整天气数据获取完成")
            return weather_data
        except Exception as e:
            logger.error(f"获取完整天气数据失败[{city_name}]: {str(e)}")
            return None
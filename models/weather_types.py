from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class WeatherNow:
    temp: str = "N/A"
    feelsLike: str = "N/A"
    weather: str = "N/A"
    windDir: str = "N/A"
    windScale: str = "N/A"
    humidity: str = "N/A"
    pressure: Optional[str] = None
    vis: Optional[str] = None
    cloud: Optional[str] = None
    dew: Optional[str] = None


@dataclass
class DailyWeather:
    textDay: str = "N/A"
    textNight: Optional[str] = None
    tempMax: str = "N/A"
    tempMin: str = "N/A"
    windDirDay: Optional[str] = None
    windScaleDay: Optional[str] = None
    windDirNight: Optional[str] = None
    windScaleNight: Optional[str] = None
    fxDate: Optional[str] = None


@dataclass
class Weather7D:
    tomorrow_text_day: str = "N/A"
    tomorrow_temp_max: str = "N/A"
    tomorrow_temp_min: str = "N/A"
    tomorrow_wind_dir: Optional[str] = None
    tomorrow_wind_scale: Optional[str] = None
    daily_list: List[DailyWeather] = field(default_factory=list)


@dataclass
class IndicesItem:
    category: str = ""
    text: str = "N/A"
    type: Optional[str] = None
    level: Optional[str] = None


@dataclass
class IndicesData:
    dressing: Optional[str] = None
    uv: Optional[str] = None
    comfort: Optional[str] = None
    sport: Optional[str] = None
    cold: Optional[str] = None
    air_pollution: Optional[str] = None
    car_wash: Optional[str] = None
    all_items: List[IndicesItem] = field(default_factory=list)


@dataclass
class WeatherData:
    city_name: str = ""
    city_id: str = ""
    now: Optional[WeatherNow] = None
    daily: Optional[Weather7D] = None
    indices: Optional[IndicesData] = None


@dataclass
class WeatherRule:
    rule_id: str
    name: str
    description: str
    conditions: Dict[str, Any]
    message_template: str
    enabled: bool = True
    priority: int = 0


@dataclass
class AlertMessage:
    title: str
    content: str
    level: str = "info"
    suggestions: List[str] = field(default_factory=list)

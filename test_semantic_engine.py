import logging
from services.semantic_engine import SemanticEngine
from models.weather_types import WeatherData, WeatherNow, Weather7D, DailyWeather

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def test_semantic_engine():
    print("=" * 60)
    print("测试语义引擎")
    print("=" * 60)
    
    engine = SemanticEngine()
    
    test_cases = [
        {
            "name": "潮湿测试",
            "weather_data": WeatherData(
                now=WeatherNow(
                    temp="25",
                    humidity="90",
                    weather="多云",
                    windScale="3"
                ),
                daily=Weather7D(
                    daily_list=[
                        DailyWeather(
                            textDay="多云",
                            tempMax="28",
                            tempMin="22"
                        )
                    ]
                )
            )
        },
        {
            "name": "昼夜温差大测试",
            "weather_data": WeatherData(
                now=WeatherNow(
                    temp="20",
                    humidity="60",
                    weather="晴",
                    windScale="2"
                ),
                daily=Weather7D(
                    daily_list=[
                        DailyWeather(
                            textDay="晴",
                            tempMax="30",
                            tempMin="15"
                        )
                    ]
                )
            )
        },
        {
            "name": "风寒明显测试",
            "weather_data": WeatherData(
                now=WeatherNow(
                    temp="10",
                    humidity="50",
                    weather="晴",
                    windScale="6"
                ),
                daily=Weather7D(
                    daily_list=[
                        DailyWeather(
                            textDay="晴",
                            tempMax="15",
                            tempMin="5"
                        )
                    ]
                )
            )
        },
        {
            "name": "严寒测试",
            "weather_data": WeatherData(
                now=WeatherNow(
                    temp="-5",
                    humidity="40",
                    weather="晴",
                    windScale="2"
                ),
                daily=Weather7D(
                    daily_list=[
                        DailyWeather(
                            textDay="晴",
                            tempMax="0",
                            tempMin="-10"
                        )
                    ]
                )
            )
        },
        {
            "name": "酷热测试",
            "weather_data": WeatherData(
                now=WeatherNow(
                    temp="38",
                    humidity="70",
                    weather="晴",
                    windScale="2"
                ),
                daily=Weather7D(
                    daily_list=[
                        DailyWeather(
                            textDay="晴",
                            tempMax="40",
                            tempMin="35"
                        )
                    ]
                )
            )
        },
        {
            "name": "注意带伞测试",
            "weather_data": WeatherData(
                now=WeatherNow(
                    temp="25",
                    humidity="70",
                    weather="小雨",
                    windScale="2"
                ),
                daily=Weather7D(
                    daily_list=[
                        DailyWeather(
                            textDay="小雨",
                            tempMax="28",
                            tempMin="22"
                        )
                    ]
                )
            )
        },
        {
            "name": "注意防滑测试",
            "weather_data": WeatherData(
                now=WeatherNow(
                    temp="-2",
                    humidity="80",
                    weather="小雪",
                    windScale="3"
                ),
                daily=Weather7D(
                    daily_list=[
                        DailyWeather(
                            textDay="小雪",
                            tempMax="0",
                            tempMin="-5"
                        )
                    ]
                )
            )
        },
        {
            "name": "多重条件测试",
            "weather_data": WeatherData(
                now=WeatherNow(
                    temp="-3",
                    humidity="95",
                    weather="中雪",
                    windScale="6"
                ),
                daily=Weather7D(
                    daily_list=[
                        DailyWeather(
                            textDay="中雪",
                            tempMax="2",
                            tempMin="-8"
                        )
                    ]
                )
            )
        }
    ]
    
    for test_case in test_cases:
        print(f"\n{'=' * 60}")
        print(f"测试场景: {test_case['name']}")
        print(f"{'=' * 60}")
        result = engine.analyze(test_case['weather_data'])
        print(f"分析结果: {result}")


if __name__ == "__main__":
    test_semantic_engine()

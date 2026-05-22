import logging
from services import WeatherService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def main():
    print("=" * 60)
    print("测试 WeatherService")
    print("=" * 60")

    try:
        weather_service = WeatherService()

        print("\n1. 测试获取当前天气...")
        current_weather = weather_service.get_current_weather()
        if current_weather:
            print(f"   天气: {current_weather.weather}")
            print(f"   温度: {current_weather.temp}°C")
            print(f"   体感温度: {current_weather.feelsLike}°C")

        print("\n2. 测试获取7天预报...")
        forecast = weather_service.get_weather_forecast()
        if forecast:
            print(f"   明天天气: {forecast.tomorrow_text_day}")
            print(f"   明天温度: {forecast.tomorrow_temp_min}~{forecast.tomorrow_temp_max}°C")

        print("\n3. 测试获取生活指数...")
        indices = weather_service.get_life_indices()
        if indices:
            print(f"   穿衣指数: {indices.dressing}")
            print(f"   紫外线指数: {indices.uv}")

        print("\n4. 测试获取完整天气数据...")
        complete = weather_service.get_complete_weather()
        if complete:
            print(f"   城市: {complete.city_name}")
            print(f"   城市ID: {complete.city_id}")
            print(f"   当前天气: {complete.now.weather if complete.now else 'N/A'}")

        print("\n" + "=" * 60)
        print("测试完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

import requests
from datetime import datetime

HEFENG_API_KEY = "bb4de13c914d421a9aa4f255df9de5c9"
CITY_ID = "101080101"
CITY_NAME = "呼和浩特"

QYWX_WEBHOOK_KEY = "ST6Ytrm7M1BAlVOCVxuGwMKrNg7hoWR3rStapaIak9D"

def get_weather_now(location):
    url = "https://mg5u9xcaf3.re.qweatherapi.com/v7/weather/now"
    params = {"location": location, "key": HEFENG_API_KEY}
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    if data.get("code") != "200":
        raise Exception(f"和风天气API错误: {data.get('msg', '未知错误')}")
    weather_info = data.get("now", {})
    return {
        "temp": weather_info.get("temp", "N/A"),
        "feelsLike": weather_info.get("feelsLike", "N/A"),
        "weather": weather_info.get("text", "N/A"),
        "windDir": weather_info.get("windDir", "N/A"),
        "windScale": weather_info.get("windScale", "N/A"),
        "humidity": weather_info.get("humidity", "N/A"),
        "pressure": weather_info.get("pressure", "N/A"),
        "vis": weather_info.get("vis", "N/A"),
        "cloud": weather_info.get("cloud", "N/A"),
        "dew": weather_info.get("dew", "N/A"),
    }

def get_weather_7d(location):
    url = "https://mg5u9xcaf3.re.qweatherapi.com/v7/weather/7d"
    params = {"location": location, "key": HEFENG_API_KEY}
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    if data.get("code") != "200":
        raise Exception(f"和风天气API错误: {data.get('msg', '未知错误')}")
    daily_list = data.get("daily", [])
    if len(daily_list) >= 2:
        tomorrow = daily_list[1]
        return {
            "tomorrow_text_day": tomorrow.get("textDay", "N/A"),
            "tomorrow_temp_max": tomorrow.get("tempMax", "N/A"),
            "tomorrow_temp_min": tomorrow.get("tempMin", "N/A"),
            "tomorrow_wind_dir": tomorrow.get("windDirDay", "N/A"),
            "tomorrow_wind_scale": tomorrow.get("windScaleDay", "N/A"),
        }
    return {}

def get_indices(location):
    url = "https://mg5u9xcaf3.re.qweatherapi.com/v7/indices/1d"
    params = {"location": location, "key": HEFENG_API_KEY, "type": "1,2,3,5,6,8,9"}
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    if data.get("code") != "200":
        raise Exception(f"和风天气API错误: {data.get('msg', '未知错误')}")
    indices_list = data.get("daily", [])
    indices_data = {}
    for item in indices_list:
        category = item.get("category", "")
        if category == "穿衣指数":
            indices_data["dressing"] = item.get("text", "N/A")
        elif category == "紫外线指数":
            indices_data["uv"] = item.get("text", "N/A")
        elif category == "舒适度指数":
            indices_data["comfort"] = item.get("text", "N/A")
        elif category == "运动指数":
            indices_data["sport"] = item.get("text", "N/A")
        elif category == "感冒指数":
            indices_data["cold"] = item.get("text", "N/A")
        elif category == "空气污染扩散条件指数":
            indices_data["air_pollution"] = item.get("text", "N/A")
        elif category == "洗车指数":
            indices_data["car_wash"] = item.get("text", "N/A")
    return indices_data

def get_clothing_advice(temp, weather, dressing_index):
    advice_parts = []
    try:
        temp = int(temp)
    except (ValueError, TypeError):
        pass

    if dressing_index and dressing_index != "N/A":
        advice_parts.append(f"【穿衣】{dressing_index}")

    if advice_parts:
        return "\n".join(advice_parts)

    if temp < 0:
        return "【穿衣】极冷，需羽绒服、围巾、手套保暖"
    elif temp < 10:
        return "【穿衣】较冷，建议穿毛衣、外套"
    elif temp < 20:
        return "【穿衣】凉爽，适合夹克、薄毛衣"
    elif temp < 26:
        return "【穿衣】舒适，适合单衣或薄外套"
    else:
        return "【穿衣】炎热，建议穿短袖，注意防暑"

def send_qywx_webhook(weather_now, weather_7d, indices, advice):
    url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={QYWX_WEBHOOK_KEY}"
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    content = f"""{date_str}
【{CITY_NAME}】天气推送

当前天气: {weather_now['weather']}
温度: {weather_now['temp']}度 (体感 {weather_now['feelsLike']}度)
风力: {weather_now['windDir']} {weather_now['windScale']}级
湿度: {weather_now['humidity']}%

明日预报: {weather_7d.get('tomorrow_text_day', 'N/A')}
温度: {weather_7d.get('tomorrow_temp_min', 'N/A')}~{weather_7d.get('tomorrow_temp_max', 'N/A')}度

{advice}

紫外线指数: {indices.get('uv', 'N/A')}
舒适度指数: {indices.get('comfort', 'N/A')}
感冒指数: {indices.get('cold', 'N/A')}"""

    payload = {
        "msgtype": "text",
        "text": {
            "content": content
        }
    }

    print("      发送的数据: " + str(payload).encode('utf-8', errors='replace').decode('utf-8'))

    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    data = response.json()
    if data.get("errcode") != 0:
        raise Exception(f"发送企业微信消息失败: {data.get('errmsg', '未知错误')}")
    return data

def main():
    print("=" * 50)
    print("企业微信天气推送开始执行")
    print("=" * 50)

    try:
        print(f"\n[1/4] 获取 {CITY_NAME} 实时天气...")
        weather_now = get_weather_now(CITY_ID)
        print(f"      天气: {weather_now['weather']}")
        print(f"      温度: {weather_now['temp']}°C")
        print(f"      体感温度: {weather_now['feelsLike']}°C")
        print(f"      风力: {weather_now['windDir']} {weather_now['windScale']}级")
        print(f"      湿度: {weather_now['humidity']}%")

        print(f"\n[2/4] 获取 {CITY_NAME} 7天预报...")
        weather_7d = get_weather_7d(CITY_ID)
        print(f"      明天天气: {weather_7d.get('tomorrow_text_day', 'N/A')}")
        print(f"      明天温度: {weather_7d.get('tomorrow_temp_min', 'N/A')}~{weather_7d.get('tomorrow_temp_max', 'N/A')}°C")

        print(f"\n[3/4] 生成穿衣建议...")
        indices = get_indices(CITY_ID)
        advice = get_clothing_advice(weather_now["temp"], weather_now["weather"], indices.get("dressing"))
        print(f"      {advice}")

        print(f"\n[4/4] 发送企业微信群消息...")
        result = send_qywx_webhook(weather_now, weather_7d, indices, advice)
        print(f"      发送成功")

        print("\n" + "=" * 50)
        print("执行完成！天气推送已发送")
        print("=" * 50)

    except Exception as e:
        print(f"\n执行失败: {str(e)}")
        raise

if __name__ == "__main__":
    main()
"""和风天气 QWeather 获取真实天气。

只负责按城市名查询并返回可读文本：
1. 城市查名 -> Location ID（geoapi）
2. 按 Location ID 查实时天气（devapi）

需要 .env 中配置 QWEATHER_API_KEY（免费版即可）。
"""

import os

import requests

_GEO_API = "https://geoapi.qweather.com/v2/city/lookup"
_WEATHER_API = "https://devapi.qweather.com/v7/weather/now"


def _lookup_location_id(city: str) -> str:
    resp = requests.get(
        _GEO_API,
        params={"location": city, "key": os.getenv("QWEATHER_API_KEY")},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != "200" or not data.get("location"):
        raise RuntimeError(f"城市 [{city}] 未找到或查询失败: {data.get('code')}")
    return data["location"][0]["id"]


def get_current_weather(city: str) -> str:
    """查询指定城市当前天气，返回可读文本。失败时抛出异常并附原因。"""
    location_id = _lookup_location_id(city)
    resp = requests.get(
        _WEATHER_API,
        params={"location": location_id, "key": os.getenv("QWEATHER_API_KEY")},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != "200":
        raise RuntimeError(f"天气查询失败: {data.get('code')}")
    now = data["now"]
    return (
        f"{city} 当前 {now['text']}，"
        f"气温 {now['temp']}°C，体感 {now['feelsLike']}°C，"
        f"湿度 {now['humidity']}%，风向 {now['windDir']}，风速 {now['windScale']} 级"
    )
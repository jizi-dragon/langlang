"""和风天气实时天气工具。

通过账号专属 API Host 调用实时天气接口（/v7/weather/now），
返回指定城市当前的温度与天气现象。
"""

import os
import gzip
import urllib.request
import urllib.parse
import json

# 学习用：常见城市 → 和风天气 LocationID（固定映射，便于入门，无需 geo 定位接口）
CITY_IDS = {
    "杭州": "101210101",
    "北京": "101010100",
    "上海": "101020100",
    "广州": "101280101",
    "深圳": "101280601",
    "成都": "101270101",
    "武汉": "101200101",
    "西安": "101110101",
}


def _fetch_now(location_id: str) -> dict:
    """请求和风天气实时天气，返回原始 JSON 的 now 字段。"""
    host = os.environ["QWEATHER_API_HOST"]
    key = os.environ["QWEATHER_API_KEY"]
    url = (
        f"https://{host}/v7/weather/now?"
        + urllib.parse.urlencode({"location": location_id, "key": key})
    )
    # 和风天气可能以 gzip 压缩返回，urllib 不自动解压，需声明接受并处理
    request = urllib.request.Request(url, headers={"Accept-Encoding": "gzip"})
    with urllib.request.urlopen(request, timeout=10) as resp:
        raw = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        data = json.loads(raw.decode("utf-8"))
    if data.get("code") != "200":
        raise RuntimeError(f"和风天气接口返回错误 code={data.get('code')}")
    return data["now"]


def get_city_weather(city: str) -> str:
    """查询指定城市的实时天气汇总。

    参数：
        city: 城市中文名，如"杭州"、"北京"
    返回：
        形如 "杭州：阴，28°C" 的天气描述
    """
    location_id = CITY_IDS.get(city)
    if location_id is None:
        return f"暂不支持查询 {city}，支持的城市：{', '.join(CITY_IDS)}"
    now = _fetch_now(location_id)
    temp = now.get("temp", "--")
    text = now.get("text", "未知")
    return f"{city}：{text}，{temp}°C"
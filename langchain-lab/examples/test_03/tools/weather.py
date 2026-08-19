"""和风天气真实数据客户端（test_03 共用）。

封装对和风天气 /v7/weather/3d 的调用，返回未来 3 天逐日预报。
与 test_01 的实时天气客户端不同，这里输出结构化 dict，便于 Agent 与上层工具在真实场景中做温度对比、行程建议。
所有敏感配置（专属 Host、Key）均从环境变量读取，不从代码传入。
"""

import gzip
import json
import os
import urllib.parse
import urllib.request

# 学习用：常见城市 → 和风天气 LocationID
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


class WeatherClientError(Exception):
    """天气客户端自身异常（网络失败、接口返回非 200 等）。"""


def _get_daily(location_id: str) -> list[dict]:
    """请求和风天气 3d 预报，返回按日期排序的逐日 dict 列表。"""
    host = os.environ["QWEATHER_API_HOST"]
    key = os.environ["QWEATHER_API_KEY"]
    url = (
        f"https://{host}/v7/weather/3d?"
        + urllib.parse.urlencode({"location": location_id, "key": key})
    )
    request = urllib.request.Request(url, headers={"Accept-Encoding": "gzip"})
    with urllib.request.urlopen(request, timeout=10) as resp:
        raw = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        data = json.loads(raw.decode("utf-8"))
    if data.get("code") != "200":
        raise WeatherClientError(f"和风天气接口返回错误 code={data.get('code')}")
    return data["daily"]
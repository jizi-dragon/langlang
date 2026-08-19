"""test_03 · args_schema：用 Pydantic 校验工具入参。

真实场景：Agent 拿到用户的话术"帮我看看杭州下雨没"，模型自动生成工具入参，
但模型可能把"杭州"打成城市名变体、漏字段、传错类型。args_schema 让这些
脏参数在进入真实 API 之前就被拦截，而不是打到和风天气上浪费一次调用、甚至 4xx。

本例用 `Literal` 把 city 限定为公司支持的城市名单，"北京"能过、"beijing/北境"被拒。
"""

from dotenv import load_dotenv

from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langchain.agents import create_agent
from langchain.messages import HumanMessage
from pydantic import BaseModel, Field
from typing import Literal

from tools.weather import CITY_IDS, _get_daily

load_dotenv()


class WeatherInput(BaseModel):
    """查询未来 3 天天气预报的入参，逐字段约束。

    这里把 city 限定为 NOT 任意 str，而是受支持的枚举——模型只能选对，
    选不对就进不了工具函数体。
    """

    city: Literal["杭州", "北京", "上海", "广州", "深圳", "成都", "武汉", "西安"] = Field(
        description="城市中文名，仅支持项目中已配置的城市"
    )
    date_index: int = Field(
        default=0,
        ge=0,
        le=2,
        description="取预报第几天：0=今天，1=明天，2=后天",
    )


@tool(args_schema=WeatherInput)
def get_weather(city: str, date_index: int = 0) -> str:
    """查询指定城市未来 3 天中某一天的天气预报。"""
    daily = _get_daily(CITY_IDS[city])
    day = daily[date_index]
    return (
        f"{city} {day['fxDate']}：{day['textDay']}，"
        f"{day['tempMin']}~{day['tempMax']}°C"
    )


def main():
    # 入参解析是确定性任务：固定模型、关闭思考模式保证 tool_call 格式稳定
    model = init_chat_model(
        "deepseek:deepseek-v4-flash",
        temperature=0,
        extra_body={"thinking": {"type": "disabled"}},
    )
    agent = create_agent(
        model=model,
        tools=[get_weather],
        system_prompt="你是出行天气顾问，用工具查询真实天气后如实回答。",
    )

    # 合法入参：Agent 生成 {city:'杭州', date_index:0}
    result = agent.invoke({"messages": [HumanMessage(content="杭州今天天气怎么样？")]})
    print(result["messages"][-1].content)

    # 非法入参演示：直接构造一个不在 Literal 里的城市，验证 args_schema 会抛校验错误
    print("\n=== 直接构造非法入参（'北境' 不在支持名单）===")
    try:
        get_weather.invoke({"city": "北境", "date_index": 0})
    except Exception as exc:
        print(f"args_schema 拦截: {type(exc).__name__}")


if __name__ == "__main__":
    main()
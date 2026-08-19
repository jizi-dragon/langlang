"""test_03 · return_direct：工具结果直接作为最终答案。

真实场景：天气/地图/汇率这类"查询型"工具，返回已是完整、格式化好的最终数据，
用户要的就是这句话本身。设 return_direct=True 后 Agent 不再拿它二次加工，
直接作为最终回复——省 Token、降低时延。

对比同一个错误输入（一个不支持的城市），return_direct 与普通工具的行为差异见 main() 注释。
"""

from dotenv import load_dotenv

from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langchain.agents import create_agent
from langchain.messages import HumanMessage

from tools.weather import CITY_IDS, _get_daily

load_dotenv()


@tool(return_direct=True)
def get_weather(city: str, date_index: int = 0) -> str:
    """查询指定城市未来 3 天中某一天的天气预报。

    Args:
        city: 城市中文名（必须是完整中文城市名）
        date_index: 取第几天，0=今天，1=明天，2=后天
    """
    if city not in CITY_IDS:
        return f"暂不支持 {city}"
    daily = _get_daily(CITY_IDS[city])
    day = daily[date_index]
    return f"{city}今天{day['textDay']}，{day['tempMin']}~{day['tempMax']}°C"


@tool
def get_travel_advice(city: str) -> str:
    """根据城市天气给出出行建议（普通工具，结果需模型再加工成完整建议）。

    Args:
        city: 城市中文名
    """
    if city not in CITY_IDS:
        return f"暂不支持 {city}"
    daily = _get_daily(CITY_IDS[city])[0]
    advice = (
        "适合外出" if daily["textDay"] in ("晴", "多云") else "建议携带雨具、注意出行安全"
    )
    return f"{city}明日{daily['textDay']}，{advice}"


def main():
    model = init_chat_model(
        "deepseek:deepseek-v4-flash",
        temperature=0,
        extra_body={"thinking": {"type": "disabled"}},
    )

    # return_direct 工具：结果直接是终答
    agent_direct = create_agent(
        model=model,
        tools=[get_weather],
        system_prompt="你是出行天气顾问，用工具查询真实天气后如实回答。",
    )
    print("=== get_weather 设 return_direct=True ===\n直接返回工具结果，模型不加工：")
    result = agent_direct.invoke({"messages": [HumanMessage(content="北京天气怎么样？")]})
    print(result["messages"][-1].content)

    # 普通工具：结果需模型加工成一句话
    agent_normal = create_agent(
        model=model,
        tools=[get_travel_advice],
        system_prompt="你是出行天气顾问，用工具查询真实天气后，把建议转述成完整的话。",
    )
    print("\n=== get_travel_advice 为普通工具 ===\n模型会基于工具结果再组织语言：")
    result = agent_normal.invoke({"messages": [HumanMessage(content="明天去杭州合适吗？")]})
    print(result["messages"][-1].content)

    # 多工具混合时的注意点说明（代码里体现不出，见文件底部注释）
    print("\n注意：若一轮里同时触发 return_direct 工具与其他普通工具，")
    print("普通工具的结果不会被模型再总结——设计多工具 Agent 时要留意。")


if __name__ == "__main__":
    main()
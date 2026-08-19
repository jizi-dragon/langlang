"""test_03 · ToolException + handle_tool_error：工具出错时的两种姿势。

真实场景：参数类型对（都是字符串），但业务上无效——比如"北境"不在支持名单。
这不该让程序崩溃，也不该用 args_schema 拦截（因为纯字符串类型合法），而应由
工具自身通过 ToolException 明确上报"业务级错误"。

对比两种姿势：
  1. handle_tool_error=False（默认）：异常向上抛出，可被调用方 try/except。
  2. handle_tool_error=True：异常被工具"吞掉"并转成正常返回值，交给 Agent，
     由模型阅读错误后向用户解释、或自我修正重试。
"""

from dotenv import load_dotenv

from langchain.chat_models import init_chat_model
from langchain.tools import tool, ToolException
from langchain.agents import create_agent
from langchain.messages import HumanMessage

from tools.weather import CITY_IDS, _get_daily

load_dotenv()


@tool
def get_weather(city: str, date_index: int = 0) -> str:
    """查询指定城市未来 3 天中某一天的天气预报。

    Args:
        city: 城市中文名（必须是完整中文城市名）
        date_index: 取第几天，0=今天，1=明天，2=后天
    """
    if city not in CITY_IDS:
        # 业务级错误：用 ToolException 明确表达，而不是 return 一段拼接的假消息
        raise ToolException(
            f"暂不支持城市 {city}，支持的城市：{'、'.join(CITY_IDS)}。请改用支持的城市名。"
        )
    daily = _get_daily(CITY_IDS[city])
    day = daily[date_index]
    return f"{city} {day['fxDate']}：{day['textDay']}，{day['tempMin']}~{day['tempMax']}°C"


# runoob 笔记写 @tool(handle_tool_error=True)，但 langchain 1.3.15 的 tool() 装饰器
# 不支持该参数；正确方式是在创建工具后给实例属性赋值（单数，ToolNode 层才是复数）。
get_weather.handle_tool_error = True


def main():
    # 演示 1：handle_tool_error=True，出错时错误信息成为正常返回值（体现在 Agent 端）
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
    result = agent.invoke({"messages": [HumanMessage(content="北境天气怎么样？")]})

    print("=== handle_tool_error=True：Agent 收到转换后的错误信息并解释 ===")
    for msg in result["messages"]:
        if msg.type == "tool":
            print(f"  [tool {msg.name}] {msg.content}")
        elif msg.type == "ai" and msg.content:
            print(f"  [agent] {msg.content}")


if __name__ == "__main__":
    main()
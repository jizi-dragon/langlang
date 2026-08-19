"""test_03 · InjectedToolCallId：在工具内拿到"本次调用"的唯一 ID。

真实场景：业务需要把一次 Agent 交互的每一项工具操作关联起来做审计——
"用户问杭州天气 → 工具调用 #xxx123 查询了天气"。
InjectedToolCallId 由 LangChain 运行时自动注入当次 ToolCall 的 id，
工具内部可以用它写日志、上报埋点、或把结果绑定回后续的 ToolMessage。

注意：InjectedToolCallId 不在工具 schema 里，模型看不到也填不了它，
由运行时在执行时注入——这正是"注入参数"的含义。
"""

from dotenv import load_dotenv

from langchain.chat_models import init_chat_model
from langchain.tools import tool, InjectedToolCallId
from langchain.agents import create_agent
from langchain.messages import HumanMessage
from typing import Annotated

from tools.weather import CITY_IDS, _get_daily

load_dotenv()


@tool
def get_weather(
    city: str,
    date_index: int = 0,
    tool_call_id: Annotated[str, InjectedToolCallId] = "",
) -> str:
    """查询指定城市未来 3 天中某一天的天气，并把本次调用记录到审计日志。

    Args:
        city: 城市中文名（必须是完整中文城市名）
        date_index: 取第几天，0=今天，1=明天，2=后天
    """
    if city not in CITY_IDS:
        return f"暂不支持 {city}"
    daily = _get_daily(CITY_IDS[city])
    day = daily[date_index]
    weather = f"{city} {day['fxDate']}：{day['textDay']}，{day['tempMin']}~{day['tempMax']}°C"

    # 真实项目：写入审计日志（此处仅打印模拟落点），tool_call_id 由运行时注入
    print(f"[audit] tool_call_id={tool_call_id} | action=query_weather | {city} → {weather}")
    return weather


def main():
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
    result = agent.invoke({"messages": [HumanMessage(content="广州今天天气怎么样？")]})
    print(f"\n最终回答: {result['messages'][-1].content}")


if __name__ == "__main__":
    main()
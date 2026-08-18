"""test_02：手动复刻 Agent 的工具调用闭环（tool_call 二次注入）。

bind_tools.py 只演示了模型"请求"调用工具；本脚本把 Agent 层实际做的
完整循环手动写出来：模型发出 tool_calls → 应用侧执行真实工具 → 把工具
结果以 ToolMessage 注入回对话历史 → 再次发送给模型，得到最终回答。

这就是 create_agent 在背后自动执行的流程。理解它，就掌握了"拿到
tool_call / 结构化参数后如何二次注入模型"。

运行（在 langchain-lab 目录下）：
    .\\dev.ps1 examples/test_02/tool_call_loop.py
"""

import sys
from pathlib import Path

# test_02 没有独立工具包，复用 test_01 的真实工具（和风天气 / 安全计算器）；
# 脚本目录在 examples/test_02，需先把 test_01 加入 sys.path 才能 `from tools...` 导入
_TEST_01_DIR = Path(__file__).resolve().parents[1] / "test_01"
sys.path.append(str(_TEST_01_DIR))

from dotenv import load_dotenv

from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, ToolMessage
from pydantic import BaseModel, Field

from tools.calculator import calculate  # noqa: E402
from tools.weather import get_city_weather  # noqa: E402

load_dotenv()


class WeatherInput(BaseModel):
    """查询指定城市的天气情况"""
    city: str = Field(description="城市名称，如 杭州、北京")
    unit: str = Field(
        default="celsius",
        description="温度单位，celsius（摄氏度）或 fahrenheit（华氏度）"
    )


class CalculatorInput(BaseModel):
    """执行数学计算"""
    expression: str = Field(
        description="要计算的数学表达式，如 '(3 + 5) * 2'"
    )


# 工具名取自已绑定 Pydantic 类的类名，与模型返回的 tool_call["name"] 一一对应
TOOL_REGISTRY = {
    "WeatherInput": get_city_weather,
    "CalculatorInput": calculate,
}


def main():
    # 工具入参解析是确定性任务，temperature=0 保证格式稳定；
    # 思考模式下 temperature 不生效，故显式关闭思考
    model = init_chat_model(
        "deepseek:deepseek-v4-flash",
        temperature=0,
        extra_body={"thinking": {"type": "disabled"}},
    )
    model_with_tools = model.bind_tools([WeatherInput, CalculatorInput])

    question = "北京今天多少度？顺便帮我算一下 123 * 456 等于多少？"
    messages = [HumanMessage(content=question)]

    # 第一轮：模型只"请求"调用工具，返回 tool_calls，不产出最终回答
    response = model_with_tools.invoke(messages)
    messages.append(response)  # AIMessage 携 tool_calls 进入历史

    print(f"模型请求了 {len(response.tool_calls)} 个工具调用：")
    for tc in response.tool_calls:
        print(f"  {tc['name']}({tc['args']})")

    # 应用侧逐个执行工具，每个结果以 ToolMessage 回填（用 tool_call_id 关联）
    for tc in response.tool_calls:
        tool_result = TOOL_REGISTRY[tc["name"]](**tc["args"])
        print(f"工具返回: {tool_result}")
        messages.append(ToolMessage(content=tool_result, tool_call_id=tc["id"]))

    # 第二轮：把含工具结果的完整历史二次注入模型，得到最终自然语言回答
    final = model_with_tools.invoke(messages)
    print(f"\n最终回答: {final.content}")


if __name__ == "__main__":
    main()

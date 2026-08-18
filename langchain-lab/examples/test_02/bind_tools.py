"""test_02：Chat Model 的 bind_tools 工具绑定。

用 Pydantic 描述工具入参，LangChain 自动转换为模型可感知的工具描述。
bind_tools 只让模型"可以"发出工具调用请求，不保证调用、也不执行工具——
真正"收到请求 → 执行 → 回填结果"的循环发生在 Agent 层。

运行（在 langchain-lab 目录下）：
    .\\dev.ps1 examples/test_02/bind_tools.py
"""

from dotenv import load_dotenv

from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field

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


def main():
    # 工具入参解析是确定性任务，temperature=0 保证入参格式稳定；
    # 思考模式下 temperature 不生效，故显式关闭思考
    model = init_chat_model(
        "deepseek:deepseek-v4-flash",
        temperature=0,
        extra_body={"thinking": {"type": "disabled"}},
    )
    model_with_tools = model.bind_tools([WeatherInput, CalculatorInput])

    response = model_with_tools.invoke(
        "北京今天多少度？顺便帮我算一下 123 * 456"
    )

    print(f"模型请求了 {len(response.tool_calls)} 个工具调用：")
    for tc in response.tool_calls:
        print(f"  {tc['name']}({tc['args']})")


if __name__ == "__main__":
    main()

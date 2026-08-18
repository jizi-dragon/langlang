"""test_01：打造你的第一个 Agent。

目标：用 langchain 的 create_agent 把"模型 + 工具"组合成一个能自主决策、
调用工具回答问题的 Agent。模型固定为 DeepSeek，工具接入真实的和风天气 API。

运行（在 langchain-lab 目录下）：
    .\run.ps1 examples/test_01/agent.py
"""

import os

from dotenv import load_dotenv

from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langchain.agents import create_agent
from langchain.messages import HumanMessage

from tools.calculator import calculate as _calculate
from tools.weather import get_city_weather as _get_city_weather

# 从项目根 .env 读取各类密钥（由 run.ps1 透传或按需加载）
load_dotenv()


# ---------------------------------------------------------------------------
# 定义工具：@tool 把普通函数包装成"Agent 可感知、可调用"的工具
# ---------------------------------------------------------------------------
@tool
def get_city_weather(city: str) -> str:
    """查询指定城市的实时天气情况。

    Args:
        city: 城市名称，如"杭州"、"北京"
    """
    return _get_city_weather(city)


@tool
def calculate(expression: str) -> str:
    """执行数学计算，支持四则运算。

    Args:
        expression: 数学表达式，如 "3 * 7 + 2"
    """
    return _calculate(expression)


# ---------------------------------------------------------------------------
# 构建 Agent
# ---------------------------------------------------------------------------
# init_chat_model 通过 provider 前缀选择服务商，deepseek 走 OpenAI 兼容协议
model = init_chat_model("deepseek:deepseek-v4-flash")

agent = create_agent(
    model=model,
    tools=[get_city_weather, calculate],
    system_prompt="你是一个乐于助人的助手，会使用工具来回答问题。"
    "查询天气类问题请调用天气工具；涉及温差推算请基于工具返回的真实温度计算。",
)


def ask(question: str):
    """发送一个问题到 Agent，并打印对话结果。"""
    inputs = {"messages": [HumanMessage(content=question)]}
    result = agent.invoke(inputs)
    print(f"问题: {question}")
    print(f"回答: {result['messages'][-1].content}")
    print("-" * 50)
    return result


if __name__ == "__main__":
    ask("杭州今天天气怎么样？")
    ask("杭州和北京今天温差多少度？")
    ask("菜鸟教程 RUNOOB 是一个非常棒的学习平台，如果我有 3 个朋友都推荐了，再加上 2 个，一共多少人推荐？")
"""04. 入门练习：构建你的第一个 Tool-calling Agent。

学习目标：
  1. @tool 定义可调用工具
  2. create_agent 把模型与工具组合成 Agent
  3. 让模型自主决定何时、用哪个工具
  4. 真实调用和风天气 QWeather 获取天气

运行（在 langchain-lab 目录下）：
  .\run.ps1 examples/test_01/04_first_agent.py

前置：.env 中配置了 OPENAI_API_* 与 QWEATHER_API_KEY。
"""

import ast
import operator
import os
from importlib.metadata import version as pkg_version

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage
from langchain.tools import tool

from qweather import get_current_weather

load_dotenv()


@tool
def calculate(expression: str) -> str:
    """安全地执行四则运算表达式，如 \"3 * 7 + 2\"。"""
    result = _safe_eval(expression)
    return f"{expression} = {result}"


_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}


def _safe_eval(expression: str):
    """只允许数字、基本四则运算符与括号的表达式求值，杜绝任意代码注入。"""
    tree = ast.parse(expression, mode="eval")

    def evaluate(node):
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPERATORS:
            return _ALLOWED_OPERATORS[type(node.op)](evaluate(node.left), evaluate(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) is ast.USub:
            return -evaluate(node.operand)
        raise TypeError(f"不支持的表达式节点: {type(node).__name__}")

    return evaluate(tree)


# 创建 Agent：模型 + 工具 + 系统提示
model = init_chat_model(
    os.getenv("OPENAI_MODEL", "deepseek-chat"),
    model_provider="openai",
    base_url=os.getenv("OPENAI_API_BASE"),
    api_key=os.getenv("OPENAI_API_KEY"),
)
agent = create_agent(
    model=model,
    tools=[get_current_weather, calculate],
    system_prompt="你是一个乐于助人的助手，会使用工具来回答问题。",
)


def ask(question: str):
    """发送问题到 Agent 并打印结果"""
    print(f"问题: {question}")
    result = agent.invoke({"messages": [HumanMessage(content=question)]})
    print(f"回答: {result['messages'][-1].content}")
    print("-" * 50)
    return result


if __name__ == "__main__":
    print(f"langchain={pkg_version('langchain')}")
    ask("杭州今天天气怎么样？")
    ask("计算 3 * 7 + 2 等于多少？")
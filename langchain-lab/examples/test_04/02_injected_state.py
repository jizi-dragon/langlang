"""test_04 · InjectedState：在工具中读取"当前这轮会话"的运行状态。

回应用户困惑：Agent 处理用户消息时，会持续把"消息列表和中间结果"累积成一份
正在变化的状态（state）。InjectedState 让工具能直接读到这份状态——但它的作用域
只在本次 invoke 内，对话结束即消失，不是持久化。

真实场景：客服工具需要知道"当前这个用户已经在这个对话里问了几轮"，从而给出
不同的应对；比如前 3 轮耐心引导，之后提醒可以转人工。这份"对话进行到第几轮"
的信息就来自 state 里的 messages。
"""

from typing import Annotated, Any

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage
from langchain.tools import InjectedState, tool


@tool
def conversation_stats(state: Annotated[dict[str, Any], InjectedState]) -> str:
    """统计这次对话已经进行到什么程度：消息总数、用户问了几次、AI 答了几次。

    不需要模型传参，数据来自框架注入的当前会话状态。
    """
    messages = state.get("messages", [])
    human = sum(1 for m in messages if m.type == "human")
    ai = sum(1 for m in messages if m.type == "ai")
    return f"本会话已累计 {len(messages)} 条消息 | 用户问了 {human} 次 | 助手回了 {ai} 次（含本次）"


def main():
    model = init_chat_model(
        "deepseek:deepseek-v4-flash",
        temperature=0,
        extra_body={"thinking": {"type": "disabled"}},
    )
    agent = create_agent(
        model=model,
        tools=[conversation_stats],
        system_prompt="你是客服助手，需要时调用 conversation_stats 了解对话进展。",
    )

    # 短会话：只有 1 条用户消息
    result = agent.invoke({"messages": [HumanMessage(content="统计一下我们这次对话的进展？")]})
    print(f"[agent] {result['messages'][-1].content}\n")

    # 更完整的会话：先铺垫几条历史消息再问，state 里累积了更多消息
    messages = [
        HumanMessage(content="你好，我想问下我的订单。" if i != 1 else "订单在哪儿查？") for i in range(2)
    ]
    messages.append(HumanMessage(content="现在统计一下这次对话进展到哪了？"))
    result = agent.invoke({"messages": messages})
    print(f"[agent] {result['messages'][-1].content}")


if __name__ == "__main__":
    main()
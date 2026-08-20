"""test_05 · 01 AgentState 自定义扩展：state_schema 是在"原有基础上"扩展，不是另起炉灶。

回应用户第一层困惑：**"如果我自定义扩展了 AgentState，它会在原有基础上进行扩展吗？"**
答案是**会**。AgentState 自带三个默认字段 messages / jump_to / structured_response（详见 runoob 16），
state_schema 接收一个"继承了 AgentState 的子类"，等于在默认字段之外再叠加你自己业务字段，
默认字段原样保留。

真实场景：跨境电商客服质检 Agent。每次对话都要携带"会员等级、订单累计金额"两个业务上下文，
工具按这些字段给差异化问候/权限；同时证明默认的 messages 字段仍在，AI 每轮仍在正常对话。

不继承 AgentState 会怎样？（对比关键）
- 直接用 `TypedDict` 定义 state_schema → 只有你写的字段，messages/jump_to 全没了，Agent 直接崩。
- 继承 AgentState 再扩展 → 默认字段 + 你的字段**并存**。这就是"在原有基础上扩展"。
"""

from typing import Annotated, Any

from langchain.agents import AgentState, create_agent
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage
from langchain.tools import InjectedState, tool


# 1) 自定义状态：必须"继承 AgentState"才能保留默认字段
class SupportAgentState(AgentState):
    """客服质检的会话状态：在默认字段之上扩展两个业务字段。"""
    member_tier: str        # 会员等级：normal / vip
    order_total: float      # 历史订单累计金额（元）


# 2) 工具通过 InjectedState 读取"本次运行"的自定义扩展字段
@tool
def member_status(state: Annotated[dict[str, Any], InjectedState]) -> str:
    """读取本次会话扩展的业务字段（会员等级、累计订单额），返回会员权益摘要。

    参数不进模型 schema，由运行时把当前 state 注入。
    """
    tier = state.get("member_tier", "normal")
    total = state.get("order_total", 0.0)
    if tier == "vip" and total >= 5000:
        return f"[VIP·资深] 累计 ¥{total:.0f}，享免运费 + 专属客服"
    if tier == "vip":
        return f"[VIP] 累计 ¥{total:.0f}，享免运费"
    return f"[普通会员] 累计 ¥{total:.0f}，消费满 5000 可升级 VIP"


def main():
    # 确定性任务：关闭思考模式、temperature=0，保证工具调用格式稳定
    model = init_chat_model(
        "deepseek:deepseek-v4-flash",
        temperature=0,
        extra_body={"thinking": {"type": "disabled"}},
    )

    # 3) state_schema 指定"自定义子类"——这就是"在默认基础上扩展"
    agent = create_agent(
        model=model,
        tools=[member_status],
        state_schema=SupportAgentState,  # 继承 AgentState → 默认字段与自定字段并存
        system_prompt="你是客服助手，先调用 member_status 了解会员权益再回答。",
    )

    # 4) 调用时，除了 messages，还要为自定义字段提供初始值
    result = agent.invoke(
        {
            "messages": [HumanMessage(content="我是会员吗？有什么权益？")],
            "member_tier": "vip",
            "order_total": 6800.0,
        }
    )
    print(f"[回复] {result['messages'][-1].content}\n")

    # 5) 验证：自定义字段进出了原始 state，且默认 messages 字段也一并返回
    print("[状态快照] 自定义字段与默认字段并存：")
    print(f"  自定: member_tier={result.get('member_tier')} order_total={result.get('order_total')}")
    print(f"  默认: messages 共 {len(result.get('messages', []))} 条"
          f" | structured_response={result.get('structured_response')}")


if __name__ == "__main__":
    main()
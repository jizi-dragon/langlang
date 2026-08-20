"""test_05 · 02 stream_mode 逐层追踪：updates（"做了什么"）vs values（"完整输入输出"）。

回应用户第二层困惑：**"updates 方便检验模型做了什么，values 能完整检验每一步输入输出"**
——user 的判断是对的。stream() 把一次 Agent 运行拆成"节点级 or 状态级"两种观察口径：

- `stream_mode="updates"`：只报**每个节点本次**产出的增量（model 节点报 AI 消息+tool_call，
  tools 节点报工具结果）。轻、聚焦"模型这步做了什么"，适合判断 Agent 是否乱来。
- `stream_mode="values"`：每个节点执行后 dump **完整 state**（messages 从头到尾全量）。
  重、冗长，适合你要拿到"每步整份输入输出"做审计/回放。

真实场景：同一个"查会员 + 算优惠 + 汇总"的客服 Agent，跑两次 stream，
对照两种模式看到的信息密度差异。工具全部纯本地，无外部依赖。
"""

from typing import Annotated, Any

from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage
from langchain.tools import InjectedState, tool
from langchain.agents import AgentState, create_agent


# 扩展字段必须用 state_schema 声明，否则 InjectedState 读不到（见 01 的重点）
class DemoAgentState(AgentState):
    member_tier: str  # vip / normal


# 两个纯本地工具，制造一次"多步"循环：模型会先调用查询再计算
@tool
def check_tier(state: Annotated[dict[str, Any], InjectedState]) -> str:
    """读取会话内置的会员等级并返回折扣率。"""
    tier = state.get("member_tier", "normal")
    return {"vip": 0.9, "normal": 1.0}[tier]


@tool
def apply_discount(amount: float, rate: float) -> str:
    """对金额应用折扣率，返回应付金额。"""
    return f"应付 ¥{amount * rate:.0f}"


def build_agent():
    model = init_chat_model(
        "deepseek:deepseek-v4-flash",
        temperature=0,
        extra_body={"thinking": {"type": "disabled"}},
    )
    return create_agent(
        model=model,
        tools=[check_tier, apply_discount],
        state_schema=DemoAgentState,  # 声明扩展字段，InjectedState 才能读到 member_tier
        system_prompt="你是电商客服，按步骤先查会员折扣再算应付金额。",
    )


def run_updates(agent, messages, extra_state):
    """updates：只看每个节点"本次"产出，轻量、聚焦模型行为。"""
    print("=== stream_mode='updates'（每节点增量）===")
    for chunk in agent.stream({"messages": messages, **extra_state}, stream_mode="updates"):
        for node_name, update in chunk.items():  # chunk: {节点名: 该节点更新的字段}
            print(f"· 节点 [{node_name}] 更新了: {list(update.keys())}")
            for msg in update.get("messages", []):
                if getattr(msg, "tool_calls", None):
                    for tc in msg.tool_calls:
                        print(f"    → AI 请求调工具 {tc['name']}({tc['args']})")
                elif msg.type == "tool":
                    print(f"    → 工具结果: {msg.content}")
                elif msg.type == "ai":
                    print(f"    → AI 最终回复: {msg.content[:60]}")
    print()


def run_values(agent, messages, extra_state):
    """values：每节点后 dump 完整 state 全量，重、适合审计回放。"""
    print("=== stream_mode='values'（每节点完整状态）===")
    for i, state in enumerate(
        agent.stream({"messages": messages, **extra_state}, stream_mode="values")
    ):
        msgs = state.get("messages", [])
        print(f"· 状态 #{i}：共 {len(msgs)} 条消息, 自定义字段 member_tier={state.get('member_tier')}")
        for m in msgs:
            kind = m.type
            if kind in ("ai", "tool") and m.content:
                print(f"     [{kind}] {str(m.content)[:70]}")
    print()


if __name__ == "__main__":
    messages = [HumanMessage(content="我会员消费了 100 块算一下折扣后多少钱")]
    # 同一个 Agent、同一入口，仅 stream_mode 不同
    run_updates(build_agent(), messages, {"member_tier": "vip"})
    run_values(build_agent(), messages, {"member_tier": "vip"})
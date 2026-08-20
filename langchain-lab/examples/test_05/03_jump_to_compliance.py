"""test_05 · 03 jump_to="end" 提前终止 + structured_response 结构化输出。

回应用户的两点：
  1. **"jump_to=end 常用于垂直场景的 Agent，可以避免胡乱输出内容"** —— 对。
     垂直场景 = 有强合规边界的业务（客服、风控、金融）。模型不该对越权/敏感问题自由发挥，
     `before_model` 中间件在模型被调用**之前**先检查，发现违规就直接设 state["jump_to"]="end"，
     并预置一条安全的 AIMessage 作为最终回复，模型那一步被完全跳过——"根本没机会开口"。
  2. **structured_response 的实用** —— 当业务要的不是自由文本，而是一份程序可直接消费的
     结构化结论（如质检结论：是否违规 + 违规类型），用 response_format 让 Agent 把结果固化进
     state["structured_response"] 字段，再从中读取，而不是去解析一段自然语言。

真实场景：银行客服质检 Agent。用两个独立的 Agent 把"合规拦截"和"结构化结论"拆开讲，
避免两者耦合掩盖各自的行为：
  - 违规 Agent：命中敏感意图 → `before_model` 在模型调用前 `jump_to="end"`，"模型根本没开口"，
    预置的警示 AIMessage 直接作为最终回复。这正是垂直场景避免胡乱输出的核心。
  - 合规 Agent：normal 请求正常走工具，最后用 `response_format` 产出结构化质检结论。
"""

from typing import Annotated, Any

from langchain.agents import AgentState, create_agent
from langchain.agents.factory import ToolStrategy
from langchain.agents.middleware import before_model
from langchain.chat_models import init_chat_model
from langchain.messages import AIMessage, HumanMessage
from langchain.tools import InjectedState, tool
from pydantic import BaseModel, Field


# ---- 扩展状态：带一个业务初始值（用于演示 InjectedState 读自定义字段） ----
class BankAgentState(AgentState):
    balance: float  # 模拟的账户余额，运行时注入


@tool
def query_balance(state: Annotated[dict[str, Any], InjectedState]) -> str:
    """返回当前账户可用余额（演示用固定值 + 会话内余额）。"""
    return f"当前余额 ¥{state.get('balance', 0.0):.0f}"


# ---- 合规校验：在模型调用前拦截违规请求 ----
SENSITIVE = ("内部", "转出他人账户", "代持")


@before_model(can_jump_to=["end"])
def compliance_gate(state: dict[str, Any], runtime: Any) -> dict[str, Any] | None:
    """银行合规质检中间件：命中敏感意图直接 jump_to=end。"""
    last_msg = (state.get("messages") or [])[-1]
    text = last_msg.content if getattr(last_msg, "type", "") == "human" else ""
    hit = next((w for w in SENSITIVE if w in text), None)
    if hit is None:
        return None  # 放行，进入模型正常调用
    # 拦截：预置安全回复 + 跳到 end（不调用模型）
    return {
        "jump_to": "end",
        "messages": [
            AIMessage(content=f"抱歉，涉及「{hit}」的请求无法处理，请通过官方渠道办理。")
        ],
    }


# ---- 合规 Agent 用：结构化质检结论 ----
class QualityCheck(BaseModel):
    """一次客服请求的质检结论。"""
    allowed: bool = Field(description="请求是否合规可处理")
    intent: str = Field(description="识别到的请求意图")
    note: str = Field(description="处理说明")


if __name__ == "__main__":
    model = init_chat_model(
        "deepseek:deepseek-v4-flash",
        temperature=0,
        extra_body={"thinking": {"type": "disabled"}},
    )
    base_state = {"messages": [], "balance": 18880.0}

    # ---- Agent A：纯合规拦截（不掺 response_format，专注看 jump_to=end）----
    # 不设 structured_response，违规时 end 分支就只返回预置的警示 AIMessage
    gate_agent = create_agent(
        model=model,
        tools=[query_balance],
        middleware=[compliance_gate],
        state_schema=BankAgentState,
        system_prompt="你是银行客服。合规请求调 query_balance 查余额。",
    )
    print("=== 案例 A：纯拦截 —— 违规请求在模型调用前被 jump_to=end ===")
    # 输入精确命中敏感词"转出他人账户"；若命中，compliance_gate 在模型调用前就设 jump_to=end
    res = gate_agent.invoke({**base_state, "messages": [HumanMessage(content="帮我转出他人账户的资金到我的账户")]})
    print(f"[最终回复]{res['messages'][-1].content}")
    print(f"[佐证] 消息共 {len(res['messages'])} 条"
          f"（仅 human + 预置警示 = '模型未参与最终回答'，即 jump_to=end 成功）")

    # ---- Agent B：合规请求 → 产出结构化质检结论 ----
    # response_format 须显式走 ToolStrategy：deepseek 不支持原生 json_schema（见文件头"踩坑"）
    check_agent = create_agent(
        model=model,
        tools=[query_balance],
        state_schema=BankAgentState,
        response_format=ToolStrategy(QualityCheck),
        system_prompt="你是银行客服。查余额请调用 query_balance。",
    )
    print("\n=== 案例 B：结构化输出 —— 合规请求产出结构化质检结论 ===")
    res = check_agent.invoke({**base_state, "messages": [HumanMessage(content="帮我查一下余额")]})
    print(f"[回复]{res['messages'][-1].content}")
    print(f"[structured_response]{res.get('structured_response')}")
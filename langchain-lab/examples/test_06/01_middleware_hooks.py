"""test_06 · 01 中间件钩子：before_model 前置拦截 + after_model 输出审核。

回应用户最陌生的点——"中间件到底怎么用、能解决什么问题"：
把与"回答内容"无关的**横切事务**（鉴权、敏感词、审核）收拢到固定的挂钩点，
而不是散落在业务代码里到处 if/else。

本脚本以"银行客服质检"为垂直场景，演示三个最常用的钩子：

- @before_model(can_jump_to=["end"])
    每次模型调用**之前**检查用户消息；命中敏感词（如卡号、密码）就设 jump_to="end"
    并预置一条安全回复，**模型根本不执行**——合规/风控硬闸门（和 test_05 一脉相承）。
- @after_model
    每次模型调用**之后**审核 AI 输出；若涉及禁区话题则用兜底话术**替换**该条消息，
    而不是让它原样返回给用户。
- @after_agent
    整次问题只触发一次，统计模型被调了几次。

关键认知：钩子**执行次数和循环绑定**。带工具时模型会被调多次，before/after_model
就触发多次；而 before/after_agent 整次只触发一次——运行日志会让你直观看到这个节律。
"""

from langchain.agents import create_agent
from langchain.agents.middleware import after_agent, after_model, before_model
from langchain.chat_models import init_chat_model
from langchain.messages import AIMessage, HumanMessage
from langchain.tools import tool

# 质检词表：命中用户消息 → 拦截；命中模型输出 → 兜底替换
SENSITIVE = ["卡号", "密码", "身份证号"]
FORBIDDEN = ["政治", "暴力", "色情"]


@before_model(can_jump_to=["end"])  # 声明本钩子允许跳转到的目标（安全机制，未声明则 jump_to 被忽略）
def security_gate(state, runtime):
    """前置拦截：用户消息含敏感词就直接结束，不让模型回答。"""
    messages = state.get("messages", [])
    if not messages:
        return None
    content = str(messages[-1].content)
    for word in SENSITIVE:
        if word in content:
            print(f"[before_model] 拦截：用户消息命敏感词「{word}」，模型不执行")
            return {
                "jump_to": "end",
                "messages": [AIMessage(content=f"抱歉，涉及「{word}」的请求为保护信息安全不予处理。")],
            }
    return None


@after_model
def output_audit(state, runtime):
    """输出审核：AI 回复涉禁区话题就用兜底话术替换，不让它原样返回。"""
    messages = state.get("messages", [])
    if not messages:
        return None
    last = messages[-1]
    content = str(last.content)
    for topic in FORBIDDEN:
        if getattr(last, "tool_calls", None):  # 本次是"请求工具"而非最终回答，不用审
            return None
        if topic in content:
            print(f"[after_model] 审核：回复含禁区「{topic}」，已替换为兜底话术")
            return {
                "messages": [
                    AIMessage(content="抱歉，我无法回答这个话题。请咨询与银行服务相关的问题。")
                ]
            }
    return None


@after_agent
def report(state, runtime):
    """整次问题结束时统计模型被调用的次数。"""
    ai_calls = sum(1 for m in state.get("messages", []) if m.type == "ai")
    print(f"[after_agent] 本轮共 {ai_calls} 次模型调用、{len(state.get('messages', []))} 条消息")


@tool
def query_account(card_last4: str) -> str:
    """按卡号后四位查询账户摘要（演示用，返回脱敏数据）。"""
    return f"卡号 ****{card_last4}：余额 ¥12,480.00，本月消费 ¥3,260.00"


def build_agent():
    model = init_chat_model(
        "deepseek:deepseek-v4-flash",
        temperature=0,
        extra_body={"thinking": {"type": "disabled"}},
    )
    return create_agent(
        model=model,
        tools=[query_account],
        middleware=[security_gate, output_audit, report],
        system_prompt="你是银行客服。查账户时先调用 query_account，回复中不得虚构信息。",
    )


def run_case(agent, title, content):
    print(f"\n========== {title} ==========")
    result = agent.invoke({"messages": [HumanMessage(content=content)]})
    for m in result["messages"]:
        if m.type == "tool":
            print(f"  [tool {m.name}] {m.content}")
        elif m.type == "ai":
            print(f"  [agent] {m.content}")


if __name__ == "__main__":
    agent = build_agent()

    # 案例 A：合法请求（需工具 → 模型被调 2 次，before/after_model 各触发 2 次）
    run_case(agent, "案例 A（合法，走工具循环）", "查一下我尾号 6688 的账户余额")

    # 案例 B：命中敏感词 → before_model 直接 jump_to=end，模型那步根本没跑
    run_case(agent, "案例 B（命中敏感词，被拦截）", "请告诉我我的银行卡号是多少")
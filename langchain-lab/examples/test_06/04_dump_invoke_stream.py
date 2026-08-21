"""test_06 · 04 全量 dump：把 agent.invoke / agent.stream 的返回**原样完整**打出来。

目的：不裁剪、不摘要，让你直视模型/Agent 每一步到底返回了什么、长什么样，
从而理解 invoke 与 stream 各模式的**数据结构**，而非只看漂亮的结果文本。
本脚本不解析、不美化，只负责打印原始对象。

覆盖：
- invoke()：完整 result dict（含 messages 里每条消息的类型/content/tool_calls/additional_kwargs）
- stream(stream_mode="messages")：逐 token 的 (AIMessageChunk, metadata)
- stream(stream_mode="updates")：每节点增量 {节点名: state 更新}
- stream(stream_mode="values")：每节点后的完整 state 全量
- stream(stream_mode="custom")：中间件 stream_writer 推来的自定义事件
- stream(stream_mode=["updates","custom"])：多模式 → (mode, chunk) 二元组

带一个纯本地工具，制造一次"模型→工具→模型"的小循环，好让你完整看到 tool_call。
"""

import pprint

from langchain.agents import create_agent
from langchain.agents.middleware import before_model
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage
from langchain.tools import tool


@before_model
def push_status(state, runtime):
    """推一条自定义事件，供 stream_mode='custom' 演示。"""
    runtime.stream_writer({"type": "status", "message": "模型调用开始…"})
    return None


@tool
def local_weather(city: str) -> str:
    """本地演示工具：按城市返回固定天气（不访问外部服务）。"""
    return f"{city}：晴，26°C，湿度 60%"


def build_agent():
    model = init_chat_model(
        "deepseek:deepseek-v4-flash",
        temperature=0,
        extra_body={"thinking": {"type": "disabled"}},
    )
    return create_agent(
        model=model,
        tools=[local_weather],
        middleware=[push_status],
        system_prompt="你是天气助手。查城市天气时先调用 local_weather。",
    )


# ---------- 打印工具：原样输出，只做可读分隔 ----------

def dump_result(result):
    """invoke 返回的 result：dict + messages 列表全量展开。"""
    print("result 类型:", type(result).__name__)
    print("result 的 key:", list(result.keys()))
    print(f"messages 共 {len(result['messages'])} 条：")
    for i, m in enumerate(result["messages"]):
        print(f"\n  --- messages[{i}] type={m.type} ---")
        print(f"    repres: {m!r}")
        print(f"    content: {m.content!r}")
        tc = getattr(m, "tool_calls", None)
        if tc:
            print(f"    tool_calls: {tc!r}")
        if m.type == "tool":
            print(f"    (工具结果 name={m.name} 已在 content 上方)")
        ak = getattr(m, "additional_kwargs", None)
        if ak:
            print(f"    additional_kwargs: {pprint.pformat(ak)}")


def run_invoke(agent, content):
    print("\n" + "=" * 70)
    print("模式：agent.invoke()（一次拿完整结果）")
    print("=" * 70)
    result = agent.invoke({"messages": [HumanMessage(content=content)]})
    dump_result(result)


def run_stream_messages(agent, content):
    print("\n" + "=" * 70)
    print("模式：agent.stream(stream_mode='messages')（逐 token）")
    print("=" * 70)
    for i, (msg_chunk, metadata) in enumerate(
        agent.stream({"messages": [HumanMessage(content=content)]}, stream_mode="messages")
    ):
        print(f"\n  --- chunk[{i}] type={type(msg_chunk).__name__} ---")
        print(f"    content: {msg_chunk.content!r}")
        print(f"    metadata: {pprint.pformat(metadata)}")


def run_stream_updates(agent, content):
    print("\n" + "=" * 70)
    print("模式：agent.stream(stream_mode='updates')（每节点增量）")
    print("=" * 70)
    for chunk in agent.stream(
        {"messages": [HumanMessage(content=content)]}, stream_mode="updates"
    ):
        for node_name, update in chunk.items():
            print(f"\n  --- 节点 [{node_name}] ---")
            print(f"    更新字段: {list(update.keys())}")
            for m in update.get("messages", []):
                print(f"    · type={m.type} content={m.content!r}")
                tc = getattr(m, "tool_calls", None)
                if tc:
                    print(f"      tool_calls={tc!r}")


def run_stream_values(agent, content):
    print("\n" + "=" * 70)
    print("模式：agent.stream(stream_mode='values')（每节点完整 state 全量）")
    print("=" * 70)
    for i, state in enumerate(
        agent.stream({"messages": [HumanMessage(content=content)]}, stream_mode="values")
    ):
        print(f"\n  --- 状态 #{i}：共 {len(state.get('messages', []))} 条消息 ---")
        for m in state.get("messages", []):
            print(f"    [{m.type}] {m.content!r}")


def run_stream_custom_and_updates(agent, content):
    print("\n" + "=" * 70)
    print("模式：agent.stream(stream_mode=['custom','updates'])（多模式 → 二元组）")
    print("=" * 70)
    for mode, chunk in agent.stream(
        {"messages": [HumanMessage(content=content)]},
        stream_mode=["custom", "updates"],
    ):
        print(f"\n  --- mode='{mode}' ---")
        print(f"    chunk: {pprint.pformat(chunk)}")


if __name__ == "__main__":
    agent = build_agent()
    # 选一个会触发工具的问题，把"模型→工具→模型"完整流程都暴露出来
    query = "查一下深圳的天气"

    run_invoke(agent, query)
    run_stream_messages(agent, query)
    run_stream_updates(agent, query)
    run_stream_values(agent, query)
    run_stream_custom_and_updates(agent, query)
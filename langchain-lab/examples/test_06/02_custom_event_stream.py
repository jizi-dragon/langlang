"""test_06 · 02 自定义事件流：middleware 用 stream_writer 推"进行到哪一步"给前端。

回应用户的疑问——"自定义事件到底有什么意义"：
前端实时界面**不止需要"回答正文"（逐 token 的 stream_mode='messages'），
还需要"过程状态"**——正在思考、正在调用哪个工具、是否完成。
`runtime.stream_writer()` 就是让中间件把这类**状态字典**推给前端，帮用户熬过等待的几秒。

本脚本以"电商客服质检"为垂直场景：Agent 先查质检规则、再出结论，执行中有停顿，
我们用 before/after_model 钩子在**每次模型调用前后**各推一条自定义事件，
再用 `stream_mode=["custom", "updates"]` 同时消费两类事件，直观看到：
custom 事件负责"过程反馈"，updates 事件负责"每次节点的产出"。
"""

from langchain.agents import create_agent
from langchain.agents.middleware import after_model, before_model
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage
from langchain.tools import tool


@before_model
def pushing_start(state, runtime):
    """每次模型调用前：通知前端"开始干活"。"""
    runtime.stream_writer({"type": "status", "message": "正在思考…"})
    return None


@after_model
def pushing_end(state, runtime):
    """每次模型调用后：判断这次是"要调工具"还是"给结论"，分别发状态。"""
    last = state["messages"][-1] if state.get("messages") else None
    tools = getattr(last, "tool_calls", None)
    if tools:
        names = [t["name"] for t in tools]
        runtime.stream_writer({"type": "status", "message": f"正在调用工具：{', '.join(names)}"})
    else:
        runtime.stream_writer({"type": "status", "message": "质检结论已生成"})


@tool
def fetch_quality_rule(category: str) -> str:
    """按服务类别取该环节的质检标准（演示用，本地字典）。"""
    rules = {
        "退货": "七天无理由、商品不影响二次销售、运费规则按平台公示",
        "咨询": "当日 24h 内首次响应、禁用绝对化用语",
        "投诉": "30 分钟内回复、致歉先行、给出补偿或升级方案",
    }
    return rules.get(category, f"未找到 {category} 的质检规则")


def build_agent():
    model = init_chat_model(
        "deepseek:deepseek-v4-flash",
        temperature=0,
        extra_body={"thinking": {"type": "disabled"}},
    )
    return create_agent(
        model=model,
        tools=[fetch_quality_rule],
        middleware=[pushing_start, pushing_end],
        system_prompt="你是电商客服质检员。先查环节质检规则，再给出是否符合标准的结论。",
    )


if __name__ == "__main__":
    agent = build_agent()
    print("=== 混合流式：stream_mode=['custom','updates'] ===\n")

    # 多模式时 agent.stream 每条产出是 (mode, payload) 二元组
    for mode, chunk in agent.stream(
        {"messages": [HumanMessage(content="质检一条'退货'类会话，看是否符合标准")]},
        stream_mode=["custom", "updates"],
    ):
        if mode == "custom":
            # 通道 B：middleware 通过 stream_writer 推来的"进行到哪一步"
            print(f"[自定义事件] 状态: {chunk['message']}")
        else:  # updates
            # 通道 A：每个节点的增量产出
            for node_name, update in chunk.items():
                for m in update.get("messages", []):
                    if m.type == "tool":
                        print(f"[updates/tools] {m.name}: {m.content}")
                    elif m.type == "ai" and getattr(m, "tool_calls", None):
                        print(f"[updates/model] 请求调用: {[t['name'] for t in m.tool_calls]}")
                    elif m.type == "ai" and m.content:
                        print(f"[updates/model] 回复: {m.content}")
"""冒烟测试：验证 langchain / langgraph 依赖可用，且最小图逻辑正确。

注意：本脚本不调用任何 LLM，因此无需 API Key，可离线运行。
目标是在不依赖外部网络的前提下，确认容器运行时与依赖装到位。
"""

from importlib.metadata import version as pkg_version

import langchain
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict


class State(TypedDict):
    text: str


def upper(state: State) -> dict:
    return {"text": state["text"].upper()}


def exclaim(state: State) -> dict:
    return {"text": state["text"] + "!"}


graph_builder = StateGraph(State)
graph_builder.add_node("upper", upper)
graph_builder.add_node("exclaim", exclaim)
graph_builder.add_edge(START, "upper")
graph_builder.add_edge("upper", "exclaim")
graph_builder.add_edge("exclaim", END)

graph = graph_builder.compile()
result = graph.invoke({"text": "hello langgraph"})
assert result["text"] == "HELLO LANGGRAPH!"

print("smoke test OK")
print(f"langchain={langchain.__version__}")
print(f"langgraph={pkg_version('langgraph')}")
print(f"langchain-openai={pkg_version('langchain-openai')}")
print(f"result={result['text']}")
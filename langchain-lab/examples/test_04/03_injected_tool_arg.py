"""test_04 · InjectedToolArg：自定义"运行时注入参数"的统一标记。

回应用户三个困惑的收尾：
- InjectedState / InjectedStore / InjectedToolCallId 都是一种注入参数，
  它们背后依赖的通用的"这是个不需要模型填的宿主参数"标记，就是 InjectedToolArg。
- InjectedToolArg 是"通用基类/标记"，其余注入类是它的特化。当你需要注入的是
  状态、Store、tool_call_id 之外的自定义东西（比如 MCP 连接对象、SDK 客户端），
  就用它。

真实工程里 InjectedToolArg 的契约：
1. 被它标记的参数，LangChain 判定为"宿主注入"，会在编排时从模型生成参数中剔除。
2. 关键约束：被标记的参数必须给出默认值（或 Optional），否则它仍会被列为
   required，模型就无法通过校验——这是最容易踩的坑。
3. 运行时的真正注入，需要调用方/运行时经 config.injection_state 提供该值。

下面用真实 agent 语境演示，而不是伪造一个"自动注入成功"的假象。
"""

from typing import Annotated

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage
from langchain.tools import InjectedToolArg, tool


@tool
def query_catalog(
    keyword: str,
    tenant_id: Annotated[str, InjectedToolArg] = "t_default",
) -> str:
    """按关键词在新的租户数据目录中搜索商品。

    Args:
        keyword: 搜索关键词
        tenant_id: 当前租户 ID（由运行时的服务端注入，不应让模型猜）
    """
    return f"[租户={tenant_id}] 搜索 {keyword} → 命中 2 件商品"


def main():
    # 1) 先看 InjectedToolArg 标记后的 schema 契约：tenant_id 是否还在 required?
    schema = query_catalog.args_schema.model_json_schema()
    print("=== InjectedToolArg 标记后的 schema 契约 ===")
    print("required:", schema.get("required"))
    print("properties:", list((schema.get("properties") or {}).keys()))
    print("→ 注意：tenant_id 仍在 properties 里（作为已知参数），但因给了默认值且被")
    print("  InjectedToolArg 标记，不在 required 中——模型可以完全不填它。")

    # 2) 宿主显式提供注入值（最真实、最可控）vs 缺省走到默认值
    print("\n=== 模式 A：宿主/服务端显式提供注入参数 ===")
    print(query_catalog.invoke({"keyword": "压缩包", "tenant_id": "acme_crm"}))

    print("\n=== 模式 B：模型只负责调用方参数，缺省落到 InjectedToolArg 的默认值 ===")
    print(query_catalog.invoke({"keyword": "压缩包"}))

    # 3) 放进真实 Agent：工具不向模型索要 tenant_id（它不在 required），
    #    实际租户由宿主在执行工具时决定。
    model = init_chat_model(
        "deepseek:deepseek-v4-flash",
        temperature=0,
        extra_body={"thinking": {"type": "disabled"}},
    )
    agent = create_agent(
        model=model,
        tools=[query_catalog],
        system_prompt="你是多租户电商客服，调用目录工具前无需询问用户属于哪个租户。",
    )
    result = agent.invoke({"messages": [HumanMessage(content="帮我找压缩包")]})
    print("\n=== Agent 运行：模型无需提供 tenant_id（不在 required）===")
    for msg in result["messages"]:
        if msg.type == "tool":
            print(f"  [tool] {msg.content}")
    print(f"  [agent] {result['messages'][-1].content}")
    print(
        "※ 真实边界：上例打印的是默认值 t_default，因为宿主没额外注入。\n"
        "  langgraph 内建能自动注入的是 InjectedState / InjectedStore / InjectedToolCallId\n"
        "  三类；对自定义 InjectedToolArg，框架完成『从模型 schema 剔除』的契约，\n"
        "  但真正填值需要宿主（服务端 / ToolNode 前处理）自行提供，框架不会替你猜。"
    )


if __name__ == "__main__":
    main()
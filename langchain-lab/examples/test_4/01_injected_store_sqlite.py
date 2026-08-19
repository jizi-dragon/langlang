"""test_04 · InjectedStore + SQLite：让工具读写真正的数据库。

核心认知（回应用户困惑）：InjectedStore 不是"框架自动收集偏好"，而是 LangChain
把你要用的"持久化存储对象"注入给工具，让工具能读写它。存进 InMemoryStore 只是内存；
本例换成 SqliteStore 后，数据真正落盘到一个 SQLite 文件，进程结束、换一次对话都在。

正确连接 SqliteStore 的关键：sqlite3 连接必须用 isolation_level=None（autocommit），
否则会和 SqliteStore 内部的显式事务冲突，报 cannot start a transaction within a transaction。
"""

import json
import sqlite3
from typing import Annotated

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage
from langchain.tools import InjectedStore, tool
from langgraph.store.base import BaseStore
from langgraph.store.sqlite import SqliteStore

DB_PATH = "test_4/business.db"


def build_store(db_path: str = DB_PATH) -> SqliteStore:
    """构造一个以 SQLite 为后端的持久化 Store，并预置存量用户偏好。"""
    # check_same_thread=False：Agent 的工具默认在线程池执行，SQLite 连接默认线程独占，
    # 必须放行跨线程，否则报 SQLite objects created in a thread can only be used in that same thread。
    # 事务管理交给 SqliteStore 内部的 BEGIN/COMMIT，因此连接需 autocommit(isolation_level=None)。
    conn = sqlite3.connect(db_path, isolation_level=None, check_same_thread=False)
    store = SqliteStore(conn)
    store.setup()

    # 预置"已有用户偏好"：这里模拟公司库里本来就有这些数据。
    # 再次强调：不是框架变出来的，而是业务系统预先写入 Store 的。
    existing = {
        "u_001": {"name": "小明", "interests": ["理发券"], "member": True},
        "u_002": {"name": "阿兰", "interests": [], "member": False},
    }
    for uid, profile in existing.items():
        store.put(("users", uid), "profile", {"data": profile})
    conn.commit()
    return store


@tool
def get_user_profile(
    user_id: str,
    store: Annotated[BaseStore, InjectedStore()],
) -> str:
    """读取指定用户 Iris 的档案。用户偏好是从真实数据库读取的，跨会话持久存在。

    Args:
        user_id: 用户 ID，如 u_001
    """
    item = store.get(("users", user_id), "profile")
    if item is None:
        return f"未找到 {user_id} 的档案"
    p = item.value["data"]
    interests = "、".join(p["interests"]) if p["interests"] else "（无）"
    member = "是" if p["member"] else "否"
    return f"{p['name']} | 会员={member} | 兴趣：{interests}"


@tool
def save_interest(
    user_id: str,
    interest: str,
    store: Annotated[BaseStore, InjectedStore()],
) -> str:
    """往指定用户档案追加一个兴趣点，并写回数据库。用于演示 Agent 在对话中收集到新偏好后落库。

    Args:
        user_id: 用户 ID，如 u_001
        interest: 用户新透露的兴趣，如 爬虫
    """
    item = store.get(("users", user_id), "profile")
    profile = dict(item.value["data"]) if item else {"name": user_id, "interests": [], "member": False}
    if interest not in profile["interests"]:
        profile["interests"].append(interest)
    store.put(("users", user_id), "profile", {"data": profile})
    return f"已保存新兴趣：{interest}"


def main():
    model = init_chat_model(
        "deepseek:deepseek-v4-flash",
        temperature=0,
        extra_body={"thinking": {"type": "disabled"}},
    )
    store = build_store()
    agent = create_agent(
        model=model,
        tools=[get_user_profile, save_interest],
        store=store,
        system_prompt="你是电商客服，读取用户偏好后推荐合适商品，并可在对话中把用户新透露的偏好保存下来。",
    )

    # 第一轮：读取既有偏好（来自数据库）
    result = agent.invoke({"messages": [HumanMessage(content="帮我查一下 u_001 用户有什么兴趣？")]})
    print("=== 读取已有偏好（来自数据库）===")
    for msg in result["messages"]:
        if msg.type == "tool":
            print(f"  [tool {msg.name}] {msg.content}")
    print(f"  [agent] {result['messages'][-1].content}")

    # 第二轮：对话中收集新偏好并写库
    result = agent.invoke({"messages": [HumanMessage(content="u_001 说他对爬虫很感兴趣，帮他记下来")]})
    print("\n=== 对话中收集新偏好并写库 ===")
    for msg in result["messages"]:
        if msg.type == "tool":
            print(f"  [tool {msg.name}] {msg.content}")


if __name__ == "__main__":
    main()
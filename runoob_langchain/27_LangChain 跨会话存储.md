# LangChain 跨会话存储 —— Store

Checkpointer 解决了"单个对话内记忆"的问题。但如果你需要在不同对话之间共享数据——比如用户偏好、学习进度——就需要用到 Store。

## Checkpointer vs Store

| 维度 | Checkpointer | Store |
| --- | --- | --- |
| 作用域 | 单个对话线程（thread_id） | 跨所有对话线程 |
| 数据类型 | Agent 状态快照（自动管理） | 任意键值数据（手动管理） |
| 典型用途 | 多轮对话记忆 | 用户偏好、知识库、配置 |
| 数据组织 | thread_id → checkpoint | (namespace, key) → value |

## Store 的基本操作

Store 使用 命名空间 + 键 的层级结构来组织数据：

## 实例
```
from langgraph.store.memory import InMemoryStore
```

运行结果：

```
偏好设置: {'theme': 'dark', 'language': 'zh-CN', 'level': '入门'}
学习进度: {'completed_courses': ['HTML 基础', 'Python 基础'], 'total_hours': 35}

用户的所有数据 (2 项):
  preferences: {'theme': 'dark', 'language': 'zh-CN', 'level': '入门'}
  progress: {'completed_courses': ['HTML 基础', 'Python 基础'], 'total_hours': 35}

删除后: None
```

## 在 Agent 中使用 Store

将 Store 传给 create_agent()，Agent 中的所有工具都能通过 InjectedStore 访问它：

## 实例
```
from dotenv import load_dotenv

load_dotenv()

from typing import Annotated

from langgraph.store.base import BaseStore

from langgraph.store.memory import InMemoryStore

from langchain.tools import tool, InjectedStore

from langchain.agents import create_agent

from langchain.chat_models import init_chat_model

from langchain.messages import HumanMessage

# 创建 Store 并预置数据

store = InMemoryStore()

store.put(("runoob", "courses"), "catalog", {

    "Python3 基础教程": {"price": "免费", "hours": 20, "level": "入门"},

    "Python 数据分析": {"price": "会员", "hours": 30, "level": "进阶"},

    "Java 面向对象": {"price": "免费", "hours": 25, "level": "进阶"},

})

store.put(("runoob", "users"), "user_vip_001", {

    "name": "小明",

    "membership": "VIP",

    "joined": "2024-01-15",

})

@tool

def query_course_info(

    course_name: str,

    store: Annotated[BaseStore, InjectedStore()],

) -> str:

    """查询菜鸟教程 RUNOOB 中课程的详细信息。

    Args:

        course_name: 课程名称

    """

    item = store.get(("runoob", "courses"), "catalog")

    catalog = item.value if item else {}

    if course_name in catalog:

        info = catalog[course_name]

        return (

            f"《{course_name}》- 价格：{info['price']}，"

            f"时长：{info['hours']}小时，难度：{info['level']}"

        )

    return f"未找到课程《{course_name}》"

@tool

def get_user_membership(

    user_id: str,

    store: Annotated[BaseStore, InjectedStore()],

) -> str:

    """查询用户会员信息。

    Args:

        user_id: 用户 ID

    """

    item = store.get(("runoob", "users"), user_id)

    if item is None:

        return f"未找到用户 {user_id}"

    user = item.value

    return (

        f"用户 {user['name']}，{user['membership']} 会员，"

        f"注册日期 {user['joined']}"

    )

model = init_chat_model("deepseek:deepseek-v4-flash", temperature=0)

agent = create_agent(

    model=model,

    tools=[query_course_info, get_user_membership],

    store=store,

    system_prompt="你是菜鸟教程 RUNOOB 的课程顾问。",

)

# 查询课程信息（数据来自 Store）

result = agent.invoke({

    "messages": [HumanMessage(content="Python3 基础教程多少钱？")]

})

print(f"查询课程: {result['messages'][-1].content}")

# 查询用户信息（数据来自 Store）

result = agent.invoke({

    "messages": [HumanMessage(content="帮我查一下用户 user_vip_001 的信息")]

})

print(f"查询用户: {result['messages'][-1].content}")
```

运行结果：

```
查询课程: 《Python3 基础教程》是免费的，学习时长约20小时，难度为入门级别。
查询用户: 用户小明是 VIP 会员，注册日期为 2024年1月15日。
```

## Store 的持久化

InMemoryStore 的数据在程序重启后丢失。生产环境可以使用 PostgresStore 等持久化方案：

## 实例
```
# 开发阶段

from langgraph.store.memory import InMemoryStore

store = InMemoryStore()

# 生产环境（需要 PostgreSQL）

# from langgraph.store.postgres import PostgresStore

# store = PostgresStore.from_conn_string("postgresql://...")
```

## Store 使用建议

| 场景 | namespace 示例 | key 示例 | 说明 |
| --- | --- | --- | --- |
| 用户偏好 | ("users", user_id) | preferences | 主题、语言、通知设置 |
| 学习进度 | ("users", user_id) | progress | 已完成课程、学习时长 |
| 知识库 | ("kb", collection) | doc_id | 文档、FAQ、产品信息 |
| 会话摘要 | ("sessions", thread_id) | summary | 长对话的摘要，供 Checkpointer 之外的场景使用 |

> Checkpointer 负责"对话到哪了"，Store 负责"用户是谁、会什么、喜欢什么"。两者配合使用，才能构建出有持续记忆的智能 Agent。

其他扩展

# LangChain 工具访问 -- InjectedState 与 InjectedStore

有时工具需要访问更多上下文信息，比如当前对话的状态、用户的持久化数据等。

LangChain 通过依赖注入机制，让工具函数能够自动获取这些信息。

## InjectedState——在工具中访问 Agent 状态

默认情况下，工具只能通过参数接收模型传来的数据。但有时工具需要知道当前对话的上下文——比如之前的对话历史、用户已确认的信息等。

InjectedState 让工具可以直接读取 Agent 的完整状态。

## 实例
```
from typing import Annotated, Any
```

运行结果：

```
已记住偏好: 暗色主题。(当前对话共 0 条消息，之前偏好: 无)
```

### 在 Agent 中使用 InjectedState

## 实例
```
from typing import Annotated, Any

from langchain.tools import tool, InjectedState

from langchain.agents import create_agent

from langchain.chat_models import init_chat_model

from langchain.messages import HumanMessage

@tool

def conversation_stats(

    state: Annotated[dict[str, Any], InjectedState],

) -> str:

    """获取当前对话的统计信息，如消息数量、对话长度等。

    不需要任何参数，统计信息从当前状态中自动读取。

    """

    messages = state.get("messages", [])

    human_msgs = [m for m in messages if m.type == "human"]

    ai_msgs = [m for m in messages if m.type == "ai"]

    tool_msgs = [m for m in messages if m.type == "tool"]

    return (

        f"对话统计：共 {len(messages)} 条消息 | "

        f"用户消息 {len(human_msgs)} 条 | "

        f"AI 回复 {len(ai_msgs)} 条 | "

        f"工具调用 {len(tool_msgs)} 次"

    )
```

> InjectedState 让你可以访问 AgentState 中的所有字段。如果你扩展了 state_schema（增加了自定义字段），这些字段也可以被 InjectedState 读取到。

## InjectedStore——在工具中访问持久化存储

Agent 状态（state）是对话级别的，对话结束就没了。而 Store 是跨会话的持久化存储，可以用来保存用户偏好、学习进度等长期信息。

InjectedStore 让工具可以直接读写 Store。

## 实例
```
from typing import Annotated

from langgraph.store.base import BaseStore

from langgraph.store.memory import InMemoryStore

from langchain.tools import tool, InjectedStore, InjectedState

from langchain.agents import create_agent

from langchain.chat_models import init_chat_model

from langchain.messages import HumanMessage

# 创建一个持久化存储（在实际项目中可以用数据库存储）

store = InMemoryStore()

# 预置一些数据

store.put(("users", "user_001"), "profile", {

    "data": {

        "name": "小明",

        "level": "入门",

        "completed_courses": ["HTML 基础教程"]

    }

})

@tool

def get_user_profile(

    store: Annotated[BaseStore, InjectedStore()],

) -> str:

    """获取当前用户的学习档案信息。

    从持久化存储中读取用户数据。

    """

    # 从 Store 中读取数据

    # Store 使用命名空间 (namespace, key) 来组织数据

    item = store.get(("users", "user_001"), "profile")

    if item is None:

        return "未找到用户档案"

    profile = item.value["data"]

    return (

        f"用户档案：姓名={profile['name']}，"

        f"水平={profile['level']}，"

        f"已完成课程={', '.join(profile['completed_courses'])}"

    )

@tool

def save_course_progress(

    course_name: str,

    store: Annotated[BaseStore, InjectedStore()],

) -> str:

    """保存用户的学习进度到持久化存储。

    Args:

        course_name: 已完成的课程名称

        store: 系统自动注入的持久化存储

    """

    # 读取现有数据

    item = store.get(("users", "user_001"), "profile")

    profile = item.value["data"] if item else {"name": "小明", "level": "入门", "completed_courses": []}

    # 更新课程列表

    if course_name not in profile["completed_courses"]:

        profile["completed_courses"].append(course_name)

    # 写回 Store

    store.put(("users", "user_001"), "profile", {"data": profile})

    return (

        f"学习进度已更新！已完成 {len(profile['completed_courses'])} 门课程："

        f"{', '.join(profile['completed_courses'])}"

    )

# 测试工具

print(get_user_profile.invoke({}))

print(save_course_progress.invoke({"course_name": "Python3 基础教程"}))

print(get_user_profile.invoke({}))
```

运行结果：

```
用户档案：姓名=小明，水平=入门，已完成课程=HTML 基础教程
学习进度已更新！已完成 2 门课程：HTML 基础教程, Python3 基础教程
用户档案：姓名=小明，水平=入门，已完成课程=HTML 基础教程, Python3 基础教程
```

## 在 Agent 中结合 Store

将 Store 传给 create_agent()，Agent 中的所有工具都能通过 InjectedStore 访问它：

## 实例
```
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

    "data": {

        "Python3 基础教程": {"price": "免费", "duration": "20小时"},

        "Python 数据分析": {"price": "会员", "duration": "30小时"},

        "HTML 基础教程": {"price": "免费", "duration": "15小时"},

    }

})

@tool

def query_course_price(

    course_name: str,

    store: Annotated[BaseStore, InjectedStore()],

) -> str:

    """查询菜鸟教程 RUNOOB 中指定课程的价格信息。

    Args:

        course_name: 课程名称

    """

    item = store.get(("runoob", "courses"), "catalog")

    catalog = item.value["data"] if item else {}

    if course_name in catalog:

        info = catalog[course_name]

        return f"《{course_name}》- 价格：{info['price']}，学习时长：{info['duration']}"

    return f"未找到课程《{course_name}》"

model = init_chat_model("deepseek:deepseek-v4-flash", temperature=0)

agent = create_agent(

    model=model,

    tools=[query_course_price],

    store=store,  # 将 Store 传入 Agent

    system_prompt="你是菜鸟教程 RUNOOB 的课程顾问。",

)

result = agent.invoke({

    "messages": [HumanMessage(content="Python3 基础教程和 Python 数据分析分别多少钱？")]

})

print(result["messages"][-1].content)
```

运行结果：

```
根据查询结果：
- 《Python3 基础教程》是免费的，学习时长约 20 小时
- 《Python 数据分析》是会员课程，学习时长约 30 小时

建议先从免费的 Python3 基础教程开始学习。
```

## InjectedState vs InjectedStore 对比

| 维度 | InjectedState | InjectedStore |
| --- | --- | --- |
| 作用域 | 当前对话（单次 Agent 运行） | 跨会话（多次 Agent 运行共享） |
| 生命周期 | 对话结束即消失 | 持久化存储 |
| 典型用途 | 读取消息历史、当前对话的中间结果 | 用户偏好、学习进度、配置信息 |
| 传入方式 | InjectedState（自动注入） | InjectedStore()（需要括号） |
| 数据组织 | 扁平字典 | 命名空间 + 键的层级结构 |

## InjectedToolArg——标记通用注入参数

除了专门的 InjectedState 和 InjectedStore，你还可以用 InjectedToolArg 标记任何需要框架注入的参数：

## 实例
```
from typing import Annotated

from langchain.tools import tool, InjectedToolArg

@tool

def my_tool(

    normal_param: str,

    injected_param: Annotated[str, InjectedToolArg],

) -> str:

    """一个包含注入参数的示例工具。

    Args:

        normal_param: 这个参数由模型提供

        injected_param: 这个参数由框架注入（Agent 不需要提供）

    """

    return f"normal={normal_param}, injected={injected_param}"
```

> InjectedToolArg 是通用的注入标记，InjectedState、InjectedStore 和 InjectedToolCallId 都是基于它实现的。大多数情况下使用专门的注入标记即可，InjectedToolArg 用于扩展自定义注入逻辑。

其他扩展

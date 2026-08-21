# LangChain create_agent() 函数

create_agent() 是 LangChain 最核心的函数，它会创建一个完整的 Agent 图（StateGraph），包含模型调用、工具执行、循环控制等全部逻辑。

### 语法

create_agent() 函数语法格式如下：

```
from langchain.agents import create_agent

agent = create_agent(
    model,                     # str | BaseChatModel：语言模型
    tools=None,                # Sequence：工具列表
    *,
    system_prompt=None,        # str | SystemMessage：系统提示
    middleware=(),             # Sequence[AgentMiddleware]：中间件列表
    response_format=None,      # ResponseFormat | type：结构化输出配置
    state_schema=None,         # type[AgentState]：自定义状态结构
    context_schema=None,       # type：运行时上下文结构
    checkpointer=None,         # Checkpointer：对话持久化
    store=None,                # BaseStore：跨会话存储
    interrupt_before=None,     # list[str]：在哪些节点前暂停
    interrupt_after=None,      # list[str]：在哪些节点后暂停
    debug=False,               # bool：是否输出详细日志
    name=None,                 # str：Agent 名称
    cache=None,                # BaseCache：缓存配置
)
```

### model 参数——模型配置

model 可以接受两种形式：字符串（由 init_chat_model() 处理）或已构建好的 BaseChatModel 实例。

## 实例
```
from langchain.agents import create_agent
```

> 推荐使用方式 1（传字符串）。create_agent() 内部会自动处理模型初始化、工具绑定、结构化输出等逻辑。方式 2 适合你需要在 Agent 之外也使用同一个模型实例的场景。

### tools 参数——工具列表

tools 接受三种格式的工具：

## 实例
```
from langchain.tools import tool

from langchain.agents import create_agent

# 格式 1：@tool 装饰的函数（最常用）

@tool

def search_course(keyword: str) -> str:

    """搜索菜鸟教程课程"""

    return f"搜索结果：{keyword} 相关课程"

# 格式 2：Pydantic BaseModel 类

from pydantic import BaseModel, Field

class WeatherQuery(BaseModel):

    """查询天气"""

    city: str = Field(description="城市名称")

# 格式 3：字典（描述远程工具或内置工具）

mcp_tool = {

    "type": "mcp",

    "server_label": "weather_server",

    "server_url": "https://weather.example.com/sse",

    "allowed_tools": ["get_forecast"],

}

# 混合使用

agent = create_agent(

    model="deepseek:deepseek-v4-flash",

    tools=[search_course, WeatherQuery, mcp_tool],

)
```

传 None 或空列表表示 Agent 无工具可用，此时它就是一个纯粹的对话模型：

## 实例
```
from langchain.agents import create_agent

from langchain.messages import HumanMessage

# 无工具 Agent——等价于直接调用模型

agent = create_agent(

    model="deepseek:deepseek-v4-flash",

    tools=None,

    system_prompt="你是菜鸟教程 RUNOOB 的助手",

)

result = agent.invoke({

    "messages": [HumanMessage(content="Python 适合零基础学习吗？")]

})

print(result["messages"][-1].content)
```

### system_prompt 参数——系统提示

定义 Agent 的行为角色和约束规则。支持字符串和 SystemMessage 对象。

## 实例
```
from langchain.agents import create_agent

from langchain.messages import SystemMessage

# 方式 1：字符串（简单直接）

agent = create_agent(

    model="deepseek:deepseek-v4-flash",

    system_prompt="你是菜鸟教程 RUNOOB 的学习顾问。回答要简洁，不超过 100 字。",

)

# 方式 2：SystemMessage 对象（可在多个 Agent 间复用）

system_msg = SystemMessage(

    content="你是菜鸟教程 RUNOOB 的学习顾问。回答要简洁，不超过 100 字。"

)

agent = create_agent(

    model="deepseek:deepseek-v4-flash",

    system_prompt=system_msg,

)
```

> system_prompt 是可选的，但不传的话模型会以"通用助手"的角色回答。对于有明确业务场景的应用，建议始终设置 system_prompt 来约束模型的行为边界。

### state_schema 参数——自定义状态

默认的 AgentState 只包含 messages、jump_to 和 structured_response。如果你需要额外的状态字段，可以扩展它：

## 实例
```
from typing import Annotated

from langchain.agents import create_agent, AgentState

from langchain.messages import HumanMessage

from langchain.tools import tool, InjectedState

from typing_extensions import TypedDict

# 扩展 AgentState，添加自定义字段

class LearningAgentState(AgentState):

    """自定义状态，增加学习进度相关字段"""

    user_level: str                       # 用户等级

    completed_topics: list[str]           # 已完成的主题列表

@tool

def track_progress(

    topic: str,

    state: Annotated[dict, InjectedState],

) -> str:

    """记录用户的学习进度。

    Args:

        topic: 刚学完的主题名称

    """

    completed = state.get("completed_topics", [])

    completed.append(topic)

    return (

        f"已记录学习进度。当前已完成 {len(completed)} 个主题："

        f"{', '.join(completed)}"

    )

agent = create_agent(

    model="deepseek:deepseek-v4-flash",

    tools=[track_progress],

    state_schema=LearningAgentState,  # 使用自定义状态

    system_prompt="你是菜鸟教程 RUNOOB 的学习助手。",

)

# 运行时需要提供自定义状态的初始值

result = agent.invoke({

    "messages": [HumanMessage(content="我学完了 Python 基础，帮我记录一下")],

    "user_level": "入门",

    "completed_topics": ["HTML 基础"],

})

print(f"用户等级: {result.get('user_level')}")

print(f"已完成主题: {result.get('completed_topics')}")

print(f"回复: {result['messages'][-1].content[:100]}")
```

运行结果：

```
用户等级: 入门
已完成主题: ['HTML 基础', 'Python 基础']
回复: 已记录学习进度。当前已完成 2 个主题：HTML 基础, Python 基础
```

### 返回值——CompiledStateGraph

create_agent() 返回一个 CompiledStateGraph 对象，这是 LangGraph 的编译后的图，提供了多种运行方式：

| 方法 | 说明 | 适用场景 |
| --- | --- | --- |
| invoke(input, config) | 同步运行，等待完整结果 | 脚本、简单接口 |
| ainvoke(input, config) | 异步运行，等待完整结果 | Web 服务 |
| stream(input, config, stream_mode) | 同步流式运行 | 实时展示中间步骤 |
| astream(input, config, stream_mode) | 异步流式运行 | WebSocket、SSE |
| get_state(config) | 获取当前状态 | 查看/恢复对话状态 |
| update_state(config, values) | 更新状态 | 手动修改对话状态 |

其他扩展

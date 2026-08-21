# LangChain Agent 工作流程

上一节我们了解了 create_agent() 的参数。

本节深入 Agent 内部，理解它是如何工作的——模型和工具之间如何协作，Agent 什么时候停止。

## Agent 执行循环

Agent 的核心是一个简单的循环：调用模型 → 检查是否需要工具 → 执行工具 → 重复。直到模型不再请求工具调用，Agent 停止并返回最终结果。

下面我们通过追踪 Agent 的每一步来理解这个过程。

## 实例
```
from dotenv import load_dotenv
```

运行结果：

```
=== Agent 执行过程追踪 ===

--- 步骤 1 ---
节点: model
  → 请求调用工具: get_weather({'city': '杭州'})
  → 请求调用工具: get_time({'city': '杭州'})

--- 步骤 2 ---
节点: tools
  → 工具结果 [get_weather]: 晴，25°C
  → 工具结果 [get_time]: 14:30

--- 步骤 3 ---
节点: model
  → AI 回复: 杭州现在天气晴朗，气温25°C，当前时间是14:30。
```

从这个追踪中可以看到 Agent 执行了 3 个步骤：

- 步骤 1（model 节点）：模型收到问题，判断需要调用 get_weather 和 get_time 两个工具，返回两个 tool_call
- 步骤 2（tools 节点）：执行两个工具，获取天气和时间结果
- 步骤 3（model 节点）：模型收到工具结果，判断信息足够，生成最终回复

## stream_mode 详解

stream() 支持多种 stream_mode，每种提供不同粒度的信息：

| 模式 | 返回内容 | 适用场景 |
| --- | --- | --- |
| updates | 每个节点执行后的状态更新 | 追踪 Agent 执行步骤，显示中间结果 |
| values | 每个节点执行后的完整状态 | 需要在每一步看到完整消息历史 |
| messages | 逐 Token 的消息流 | 前端流式展示 AI 打字效果 |
| custom | 自定义事件 | Middleware 通过 stream_writer 发送自定义事件 |

### stream_mode="values"——查看完整状态变化

## 实例
```
print("=== stream_mode='values' ===\n")

for i, chunk in enumerate(agent.stream(

    {"messages": [HumanMessage(content="杭州天气怎么样？")]},

    stream_mode="values",

)):

    messages = chunk.get("messages", [])

    print(f"状态 {i}: {len(messages)} 条消息")

    for msg in messages:

        print(f"  [{msg.type}] {str(msg.content)[:80]}")

    if i >= 3:  # 只看前几个状态

        break
```

运行结果：

```
=== stream_mode='values' ===

状态 0: 1 条消息
  [human] 杭州天气怎么样？

状态 1: 2 条消息
  [human] 杭州天气怎么样？
  [ai]

状态 2: 3 条消息
  [human] 杭州天气怎么样？
  [ai]
  [tool] 晴，25°C

状态 3: 4 条消息
  [human] 杭州天气怎么样？
  [ai]
  [tool] 晴，25°C
  [ai] 杭州今天天气晴朗，气温25°C，适合出门活动。
```

### stream_mode="messages"——逐 Token 流式输出

## 实例
```
print("=== stream_mode='messages'（流式打字效果）===\n")

for msg_chunk, metadata in agent.stream(

    {"messages": [HumanMessage(content="用一句话介绍菜鸟教程 RUNOOB")]},

    stream_mode="messages",

):

    # msg_chunk 是 AIMessageChunk，每个只包含一个 Token

    if hasattr(msg_chunk, 'content') and msg_chunk.content:

        print(msg_chunk.content, end="", flush=True)

print()
```

## Agent 的退出条件

Agent 什么时候停止？主要有以下几种情况：

| 退出条件 | 说明 | 示例 |
| --- | --- | --- |
| 无工具调用 | 模型返回的 AIMessage 中 tool_calls 为空 | 模型认为任务完成，直接回复 |
| return_direct=True | 工具标记为直接返回，执行后立即结束 | 查询类工具，结果即最终答案 |
| structured_response | 模型产出了结构化输出 | response_format 指定的结构化输出完成 |
| jump_to="end" | Middleware 通过状态控制主动结束 | 检测到问题越权，提前终止 |

## 实例
```
from langchain.tools import tool

from langchain.agents import create_agent

from langchain.chat_models import init_chat_model

from langchain.messages import HumanMessage

# 情况 1：模型直接回复（不需要工具）

model = init_chat_model("deepseek:deepseek-v4-flash", temperature=0)

agent = create_agent(

    model=model,

    tools=[],  # 无工具

)

result = agent.invoke({

    "messages": [HumanMessage(content="用一句话介绍菜鸟教程")]

})

# 模型直接回复，循环只执行一次

print(f"无工具场景，消息数: {len(result['messages'])}")

print(f"回复: {result['messages'][-1].content[:80]}...")

# 情况 2：需要工具调用（多轮循环）

@tool

def search_course(keyword: str) -> str:

    """搜索菜鸟教程课程"""

    return f"找到 {keyword} 相关课程 3 门"

agent_with_tools = create_agent(

    model=model,

    tools=[search_course],

)

result = agent_with_tools.invoke({

    "messages": [HumanMessage(content="搜索 Python 课程")]

})

print(f"\n有工具场景，消息数: {len(result['messages'])}")

# 通常会有：human, ai(tool_call), tool(result), ai(final)

for msg in result["messages"]:

    print(f"  [{msg.type}]", end="")

    if hasattr(msg, 'tool_calls') and msg.tool_calls:

        print(f" tool_calls: {[tc['name'] for tc in msg.tool_calls]}")

    else:

        print(f" {str(msg.content)[:50]}")
```

运行结果：

```
无工具场景，消息数: 2
回复: 菜鸟教程是一个面向初学者的编程学习平台，提供丰富的教程和实例...

有工具场景，消息数: 4
  [human] 搜索 Python 课程
  [ai] tool_calls: ['search_course']
  [tool] 找到 python 相关课程 3 门
  [ai] 在菜鸟教程中搜索 "Python 课程" 找到了 3 门相关课程...
```

## invoke vs stream 对比

| 方法 | 返回时机 | 适用场景 | 用户体验 |
| --- | --- | --- | --- |
| invoke() | 全部完成后一次性返回 | 脚本、API 接口、批处理 | 等待后看到完整结果 |
| stream() | 逐步返回中间状态 | 聊天界面、需要展示过程 | 实时看到进展 |
| ainvoke() | 异步全部完成后返回 | Web 服务、异步框架 | 不阻塞事件循环 |
| astream() | 异步逐步返回 | WebSocket、SSE 推送 | 服务端实时推送 |

## 在 with_config 中传入线程 ID

如果你使用了 checkpointer（后续章节会详细介绍），需要通过 config 传入 thread_id 来管理对话线程：

## 实例
```
# config 用于传递运行时配置

# thread_id 用于区分不同的对话线程

config = {"configurable": {"thread_id": "conversation-001"}}

# invoke 方式

result = agent.invoke(

    {"messages": [HumanMessage(content="你好")]},

    config=config,

)

# stream 方式也支持 config

for chunk in agent.stream(

    {"messages": [HumanMessage(content="你好")]},

    config=config,

    stream_mode="updates",

):

    print(chunk)
```

其他扩展

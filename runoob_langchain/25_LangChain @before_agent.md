# LangChain @before_agent 与 @after_agent

before_agent 和 after_agent 是 Agent 级别的钩子，分别在 Agent 执行之前和完成之后各执行一次。适合做初始化、预处理、后处理和统计分析。

## before_agent -- Agent 开始前的准备工作

before_agent 在 Agent 正式开始执行前运行，只执行一次。你可以在这里做输入预处理、用户信息验证、资源初始化等。

### 场景 1：输入预处理 -- 自动修正用户输入

## 实例
```
from dotenv import load_dotenv
```

### 场景 2：访问控制 -- 权限检查

## 实例
```
from langchain.agents.middleware import before_agent

@before_agent

def access_control(state, runtime):

    """检查用户是否有权限使用 Agent"""

    # 从 runtime.context 获取用户信息

    context = runtime.context

    if context is None:

        return None

    user_role = context.get("user_role", "guest")

    # 访客用户只能使用有限功能

    if user_role == "guest":

        messages = state.get("messages", [])

        if messages:

            last_content = str(messages[-1].content)

            # 检查是否涉及限制功能

            restricted_keywords = ["删除", "管理", "配置", "admin"]

            if any(kw in last_content for kw in restricted_keywords):

                return {

                    "jump_to": "end",

                    "messages": [HumanMessage(

                        content="您当前的权限不足，无法执行此操作。请登录后重试。"

                    )]

                }

    return None
```

## after_agent -- Agent 完成后的处理

after_agent 在 Agent 完成所有处理后执行（只执行一次）。你可以在这里格式化最终输出、记录统计信息、清理资源等。

### 场景 3：统计分析 -- 记录对话数据

## 实例
```
from langchain.agents.middleware import after_agent

@after_agent

def conversation_stats(state, runtime):

    """统计对话信息并追加到结果中"""

    messages = state.get("messages", [])

    # 统计数据

    model_calls = 0

    tool_calls = 0

    total_chars = 0

    for msg in messages:

        if msg.type == "ai":

            model_calls += 1

            if hasattr(msg, 'tool_calls') and msg.tool_calls:

                tool_calls += len(msg.tool_calls)

        if hasattr(msg, 'content') and msg.content:

            total_chars += len(str(msg.content))

    # 通过 custom stream 发送统计信息

    runtime.stream_writer({

        "type": "stats",

        "model_calls": model_calls,

        "tool_calls": tool_calls,

        "total_messages": len(messages),

        "total_chars": total_chars,

    })

    return None

model = init_chat_model("deepseek:deepseek-v4-flash", temperature=0)

agent = create_agent(

    model=model,

    tools=[search_course],

    middleware=[conversation_stats],

    system_prompt="你是菜鸟教程 RUNOOB 的课程顾问。",

)

# 使用 stream_mode=["updates", "custom"] 接收自定义事件

for mode, chunk in agent.stream(

    {"messages": [HumanMessage(content="查一下 Python 课程")]},

    stream_mode=["updates", "custom"],

):

    if mode == "custom" and chunk.get("type") == "stats":

        print(f"统计信息: {chunk}")
```

运行结果：

```
统计信息: {'type': 'stats', 'model_calls': 2, 'tool_calls': 1,
            'total_messages': 4, 'total_chars': 127}
```

### 场景 4：格式化输出 -- 统一回复风格

## 实例
```
from langchain.agents.middleware import after_agent

from langchain.messages import AIMessage

@after_agent

def format_output(state, runtime):

    """在结果中追加格式化的总结信息"""

    messages = state.get("messages", [])

    if not messages:

        return None

    # 找到最后一条 AI 消息（最终回复）

    last_ai = None

    for msg in reversed(messages):

        if msg.type == "ai" and msg.content:

            last_ai = msg

            break

    if last_ai:

        # 统计信息

        tool_msgs = [m for m in messages if m.type == "tool"]

        tool_count = len(tool_msgs)

        footer = (

            f"\n\n---\n"

            f"> 本次对话共进行 {len(messages)} 条消息，"

            f"调用了 {tool_count} 次工具。\n"

            f"> 由菜鸟教程 RUNOOB AI 助手提供支持。"

        )

        # 追加到最终回复

        return {

            "messages": [

                AIMessage(content=last_ai.content + footer)

            ]

        }

    return None

model = init_chat_model("deepseek:deepseek-v4-flash", temperature=0)

agent = create_agent(

    model=model,

    tools=[search_course],

    middleware=[format_output],

    system_prompt="你是菜鸟教程 RUNOOB 的课程顾问。",

)

result = agent.invoke({

    "messages": [HumanMessage(content="Python 有什么课程？")]

})

print(result["messages"][-1].content)
```

运行结果：

```
菜鸟教程 RUNOOB 中有 Python3 基础教程，共30章，完全免费，非常适合 Python 初学者入门学习。

---
> 本次对话共进行 4 条消息，调用了 1 次工具。
> 由菜鸟教程 RUNOOB AI 助手提供支持。
```

## 四个钩子的完整协作示例

## 实例
```
from langchain.agents.middleware import (

    before_agent, after_agent, before_model, after_model

)

from langchain.agents import create_agent

from langchain.chat_models import init_chat_model

from langchain.messages import HumanMessage

from langchain.tools import tool

# ----- 定义所有钩子 -----

@before_agent

def init_session(state, runtime):

    """开始：初始化会话"""

    print(">>> 会话开始")

    return None

@before_model

def pre_model_check(state, runtime):

    """每次模型调用前"""

    msg_count = len(state.get("messages", []))

    print(f"  [model前] 消息数: {msg_count}")

    return None

@after_model

def post_model_check(state, runtime):

    """每次模型调用后"""

    last = state["messages"][-1] if state.get("messages") else None

    if last and hasattr(last, 'tool_calls') and last.tool_calls:

        print(f"  [model后] 需要工具调用")

    return None

@after_agent

def finish_session(state, runtime):

    """结束：清理资源"""

    total = len(state.get("messages", []))

    print(f"<<< 会话结束，共 {total} 条消息")

    return None

# ----- 创建 Agent -----

@tool

def get_weather(city: str) -> str:

    """查询天气"""

    return f"{city}: 晴"

model = init_chat_model("deepseek:deepseek-v4-flash", temperature=0)

agent = create_agent(

    model=model,

    tools=[get_weather],

    middleware=[init_session, pre_model_check, post_model_check, finish_session],

    system_prompt="你是助手。",

)

result = agent.invoke({

    "messages": [HumanMessage(content="杭州天气？")]

})

print(f"\n最终回复: {result['messages'][-1].content}")
```

运行结果：

```
>>> 会话开始
  [model前] 消息数: 2
  [model后] 需要工具调用
  [model前] 消息数: 3
<<< 会话结束，共 4 条消息

最终回复: 杭州今天晴天，适合出行。
```

## Middleware 钩子总结

| 钩子 | 执行次数 | 何时使用 | 关键能力 |
| --- | --- | --- | --- |
| before_agent | 1 次 | 权限检查、输入预处理、资源初始化 | 可 jump_to="end" 提前终止 |
| before_model | 每次循环 | 消息裁剪、内容过滤、上下文注入 | 可 jump_to 控制流程 |
| wrap_model_call | 每次循环 | 重试、降级、缓存、prompt 修改 | 完全控制模型执行 |
| after_model | 每次循环 | 响应审核、内容追加、日志 | 可替换模型输出 |
| wrap_tool_call | 每次工具调用 | 工具重试、缓存、参数改写 | 完全控制工具执行 |
| after_agent | 1 次 | 输出格式化、统计分析、清理 | 最终状态修改 |

其他扩展

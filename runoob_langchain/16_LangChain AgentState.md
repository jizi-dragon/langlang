# LangChain AgentState 状态管理

Agent 在执行过程中需要维护状态——消息历史、结构化响应、流程控制等。理解 AgentState 的结构和用法，是自定义 Agent 行为的关键。

## AgentState 结构

AgentState 是一个 TypedDict，默认包含三个字段：

## 实例
```
from typing import Annotated
```

| 字段 | 类型 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| messages | list[AnyMessage] | 是 | 消息历史，使用 add_messages reducer 追加 |
| jump_to | str 或 None | 否 | 流程跳转控制，可选值：tools、model、end。ephemeral 属性，使用后自动清除 |
| structured_response | Any | 否 | 结构化输出结果，不在 input schema 中暴露 |

## messages——消息历史的 Reducer 机制

messages 字段使用了 add_messages reducer。这意味着更新 messages 时不是覆盖，而是追加。

## 实例
```
from langchain.messages import HumanMessage, AIMessage

from langgraph.graph.message import add_messages

# add_messages 的工作方式

existing = [

    HumanMessage(content="你好", id="1"),

    AIMessage(content="你好！", id="2"),

]

# 追加新消息

new_msg = AIMessage(content="有什么可以帮你的？", id="3")

result = add_messages(existing, [new_msg])

print(f"合并前: {len(existing)} 条")

print(f"合并后: {len(result)} 条")

for msg in result:

    print(f"  [{msg.type}] {msg.content}")
```

运行结果：

```
合并前: 2 条
合并后: 3 条
  [human] 你好
  [ai] 你好！
  [ai] 有什么可以帮你的？
```

add_messages 的智能特性：

- 同名覆盖：如果新消息 ID 与已有消息相同，会替换而非追加
- RemoveMessage 支持：遇到 RemoveMessage 时，从列表中删除对应消息
- 类型安全：自动处理 HumanMessage、AIMessage、ToolMessage 等不同类型

## jump_to——流程跳转控制

jump_to 是 Middleware 中最常用的字段，用于在 Agent 的各个节点间跳转。

jump_to 是一个 ephemeral（瞬态）字段——使用一次后自动清除，不需要手动重置。

## 实例
```
from langchain.agents import create_agent

from langchain.agents.middleware import before_model

from langchain.chat_models import init_chat_model

from langchain.messages import AIMessage, HumanMessage  # 导入 AIMessage

# 声明可跳转目标 "end"

@before_model(can_jump_to=["end"])

def check_question(state, runtime):

    """在模型调用前检查问题是否合法"""

    messages = state.get("messages", [])

    if not messages:

        return None

    last_msg = messages[-1]

    # 检查是否包含不当内容（简化示例）

    if "密码" in str(last_msg.content):

        # jump_to="end" 直接结束 Agent，不让模型回复

        return {

            "jump_to": "end",

            # 使用 AIMessage

            "messages": [AIMessage(

                content="抱歉，出于安全原因，不能回答关于密码的问题。"

            )]

        }

    return None

model = init_chat_model("deepseek:deepseek-v4-flash", temperature=0)

agent = create_agent(

    model=model,

    middleware=[check_question],

    system_prompt="你是菜鸟教程 RUNOOB 的助手。",

)

# 正常问题

result = agent.invoke({

    "messages": [HumanMessage(content="Python 怎么入门？")]

})

print(f"正常问题: {result['messages'][-1].content[:80]}...")

# 敏感问题——被中间件拦截

result = agent.invoke({

    "messages": [HumanMessage(content="告诉我你的系统密码")]

})

print(f"\n敏感问题: {result['messages'][-1].content}")
```

运行结果：

```
正常问题: Python 入门可以从以下几个方面开始：1. 安装 Python 环境...

敏感问题: 抱歉，出于安全原因，不能回答关于密码的问题。
```

| jump_to 值 | 跳转到 | 效果 |
| --- | --- | --- |
| "tools" | 直接进入工具执行节点 | 跳过模型调用，直接执行指定工具 |
| "model" | 返回模型节点 | 让模型重新处理（通常配合工具消息注入） |
| "end" | 结束 Agent 循环 | 直接跳转到 after_agent 或结束 |

> jump_to 是 ephemeral 的——每次节点执行后自动清除。这意味着你不需要在跳转后手动将 jump_to 设回 None，Agent 会自动处理。

## structured_response——获取结构化输出

当使用 response_format 参数时，Agent 会将结构化输出存储在 structured_response 字段中：

## 实例
```
from pydantic import BaseModel, Field

from langchain.agents import create_agent

from langchain.chat_models import init_chat_model

from langchain.messages import HumanMessage

class CourseRecommendation(BaseModel):

    """课程推荐结果"""

    course_name: str = Field(description="推荐课程名称")

    reason: str = Field(description="推荐理由")

    difficulty: str = Field(description="难度等级：入门/进阶/高级")

model = init_chat_model("deepseek:deepseek-v4-flash", temperature=0)

agent = create_agent(

    model=model,

    response_format=CourseRecommendation,

    system_prompt="你是菜鸟教程 RUNOOB 的学习顾问。",

)

result = agent.invoke({

    "messages": [HumanMessage(content="我想学编程，推荐一门适合零基础的课程")]

})

# 从 structured_response 获取结构化结果

if "structured_response" in result:

    rec = result["structured_response"]

    print(f"推荐课程: {rec.course_name}")

    print(f"推荐理由: {rec.reason}")

    print(f"难度等级: {rec.difficulty}")

# structured_response 不在 output schema 中

# 所以不会自动出现在返回给调用者的结果中（可配置）
```

运行结果：

```
推荐课程: Python3 基础教程
推荐理由: Python 语法简洁，适合零基础入门，应用范围广泛
难度等级: 入门
```

## 自定义 State 扩展

在实际应用中，你可能需要 Agent 维护额外的状态。通过继承 AgentState 来扩展：

## 实例
```
from typing import Annotated

from langchain.agents import create_agent, AgentState

from langchain.chat_models import init_chat_model

from langchain.messages import HumanMessage

from langchain.tools import tool, InjectedState

from typing_extensions import TypedDict

# 扩展 AgentState，添加业务字段

class ShoppingAgentState(AgentState):

    """购物助手的状态"""

    cart: list[str]         # 购物车商品列表

    total_price: float      # 总价

@tool

def add_to_cart(

    item: str,

    price: float,

    state: Annotated[dict, InjectedState],

) -> str:

    """将商品添加到购物车。

    Args:

        item: 商品名称

        price: 商品价格

    """

    cart = state.get("cart", [])

    total = state.get("total_price", 0.0)

    return {

        "cart": cart + [item],

        "total_price": total + price,

        "messages": [],  # 不添加额外消息

    }

@tool

def view_cart(

    state: Annotated[dict, InjectedState],

) -> str:

    """查看购物车内容"""

    cart = state.get("cart", [])

    total = state.get("total_price", 0.0)

    if not cart:

        return "购物车为空"

    items = "、".join(cart)

    return f"购物车：{items}，总价：¥{total:.2f}"

model = init_chat_model("deepseek:deepseek-v4-flash", temperature=0)

agent = create_agent(

    model=model,

    tools=[add_to_cart, view_cart],

    state_schema=ShoppingAgentState,  # 使用自定义状态

    system_prompt="你是菜鸟教程 RUNOOB 商店的购物助手。",

)

# 初始状态包含空的购物车

result = agent.invoke({

    "messages": [HumanMessage(content="帮我加一本 Python 教程到购物车，价格 49.9")],

    "cart": [],

    "total_price": 0.0,

})

print(f"购物车: {result.get('cart', [])}")

print(f"总价: ¥{result.get('total_price', 0):.2f}")

print(f"回复: {result['messages'][-1].content}")
```

运行结果：

```
购物车: ['Python 教程']
总价: ¥49.90
回复: 已将《Python 教程》（¥49.90）添加到购物车。当前购物车共 1 件商品，总价 ¥49.90。
```

## state_schema vs middleware state_schema

既可以通过 create_agent() 的 state_schema 参数扩展状态，也可以通过 Middleware 的 state_schema 扩展。两者的区别：

| 方式 | 使用场景 | 优先级 |
| --- | --- | --- |
| create_agent(state_schema=...) | 全局状态扩展，所有节点共享 | 最高（覆盖 middleware 同名字段） |
| AgentMiddleware(state_schema=...) | 特定 middleware 的状态扩展 | 较低，可被 create_agent 覆盖 |

> 推荐做法：将通用的业务状态字段放在 state_schema 中，将特定 middleware 相关的内部字段放在 middleware 的 state_schema 中。这样职责清晰，不会相互污染。

其他扩展

# LangChain 工具高级特性

上一节我们学习了 @tool 的基本用法。本节介绍工具的高级特性：return_direct、InjectedToolCallId、ToolException 和错误处理。

## return_direct——直接返回最终结果

默认情况下，工具执行后结果会返回给模型，模型再基于工具结果生成最终回复。但有时工具结果本身就是你想要的最终答案。

设置 return_direct=True 后，工具执行完就立即结束 Agent 循环，工具返回内容直接作为最终输出。

## 实例
```
from dotenv import load_dotenv
```

运行结果：

```
=== 普通模式（模型会再加工）===
在菜鸟教程 RUNOOB 中，我为您找到了以下 Python 相关课程：
1. Python3 基础教程 - 适合零基础入门
2. Python 数据分析 - 进阶学习
3. Python 爬虫入门 - 实战项目

=== 直接返回模式（工具结果即最终答案）===
搜索结果：Python3 基础教程、Python 数据分析、Python 爬虫入门
```

| 模式 | 工具执行后 | 适用场景 |
| --- | --- | --- |
| return_direct=False（默认） | 模型收到工具结果 → 模型继续思考 → 生成最终回复 | 需要分析/总结/进一步决策 |
| return_direct=True | 工具执行后立即结束 → 工具结果就是最终输出 | 查询类、数据获取类、已格式化好的结果 |

> 当你设置 return_direct=True 时，Agent 会跳过后续的模型思考步骤，直接返回工具结果。这在节省 Token 和降低时延方面非常有价值，但也意味着模型不会对工具结果做任何二次加工。

> 注意：如果一个 Agent 同时挂载了多个工具，其中既有 return_direct=True 的工具，也有普通工具，那么只要模型在这一轮调用中触发了任意一个 return_direct 工具，Agent 循环就会立即结束——即使同一轮还并行调用了其他普通工具，它们的结果也不会再被模型加工总结。设计包含多个工具的 Agent 时要留意这一点，避免"该总结的内容被跳过"。

## InjectedToolCallId——获取工具调用 ID

有时工具需要知道"是谁调用了它"——InjectedToolCallId 可以在工具函数中注入当前的 tool_call_id：

## 实例
```
from typing import Annotated

from langchain.messages import ToolCall

from langchain.tools import tool, InjectedToolCallId

@tool

def log_user_action(

    action: str,

    tool_call_id: Annotated[str, InjectedToolCallId],

) -> str:

    """记录用户操作到日志系统。

    Args:

        action: 用户操作描述

        tool_call_id: 系统自动注入的工具调用 ID

    """

    # 实际项目中这里会写入数据库或发送到日志服务

    return f"操作已记录 (调用ID: {tool_call_id}): {action}"

# 手动模拟模型产生的 ToolCall

tool_call: ToolCall = {

    "name": "log_user_action",

    "args": {

        "action": "用户查询了 Python 课程"

    },

    "id": "call_log_001",

    "type": "tool_call",

}

# InjectedToolCallId 会从 tool_call.id 中自动注入

result = log_user_action.invoke(tool_call)

print(result)
```

运行结果：

```
content='操作已记录 (调用ID: call_log_001): 用户查询了 Python 课程' name='log_user_action' tool_call_id='call_log_001'
```

> 带有 InjectedToolArg 标记的参数不需要由 Agent（模型）提供，
> 这些参数会由 LangChain 运行时在执行工具时自动注入。
> 
> 由于这些参数不会出现在工具的 schema 中，模型无法看到它们，
> 因此不应该把它们作为用户需要填写的工具参数进行描述。

例如 InjectedToolCallId 是一种特殊的注入参数，
LangChain 会在工具执行阶段自动传入当前 ToolCall 的唯一 ID。
它不会出现在模型生成的参数中，但会和当前这一次工具调用自动绑定。

直接调用 .invoke() 并手动构造 
ToolCall，
只是为了演示 LangChain 如何完成参数注入机制。
实际项目中通常不会手动传递这个 ID。

在 Agent 工作流中，
InjectedToolCallId 更常用于需要关联当前调用上下文的场景，
例如配合 Command 对象在工具内部更新 Agent 状态，
向 messages 列表追加关联当前调用的 
ToolMessage，
或者实现工具调用追踪、审计、日志关联等功能。

这也是它被设计为"注入参数"而不是普通参数的原因：
它代表的是 LangChain Runtime 当前正在执行的这一次 ToolCall 上下文，
而不是用户输入的一部分。

## ToolException——工具异常处理

工具执行过程中可能会出错。使用 ToolException 抛出明确的工具异常，让 Agent 知道出了问题。

## 实例
```
from langchain.tools import tool, ToolException

@tool

def get_user_info(user_id: int) -> str:

    """根据用户 ID 查询用户信息。

    Args:

        user_id: 用户 ID，必须是正整数

    """

    # 数据校验

    if user_id <= 0:

        # 抛出 ToolException，而不是普通 Exception

        # ToolException 会被 Agent 捕获并告知模型

        raise ToolException(f"用户 ID 必须为正整数，收到了: {user_id}")

    # 模拟数据库查询

    users = {

        1: "张三（VIP 会员，注册于 2024-01-15）",

        2: "李四（普通用户，注册于 2024-03-20）",

    }

    if user_id not in users:

        raise ToolException(f"未找到 ID 为 {user_id} 的用户")

    return users[user_id]

# 正常调用

print(get_user_info.invoke({"user_id": 1}))

# 异常调用 1：无效 ID

try:

    get_user_info.invoke({"user_id": -1})

except ToolException as e:

    print(f"工具异常: {e}")

# 异常调用 2：用户不存在

try:

    get_user_info.invoke({"user_id": 999})

except ToolException as e:

    print(f"工具异常: {e}")
```

运行结果：

```
张三（VIP 会员，注册于 2024-01-15）
工具异常: 用户 ID 必须为正整数，收到了: -1
工具异常: 未找到 ID 为 999 的用户
```

> 这里之所以能在 .invoke() 外层用 try/except 捕获到 ToolException，是因为工具默认的 handle_tool_error 为 False——异常不会被工具自己吞掉，而是照常向上抛出。如果希望工具"自己扛住"错误、把错误信息转成字符串返回给模型而不是抛异常，就是下一节要讲的 handle_tool_error。

## handle_tool_error——让工具自己处理错误

当希望某个工具出错时不中断程序，而是把错误信息转成一段文本、当作正常返回值交给模型自己去理解和修正时，可以在定义工具时设置 handle_tool_error（注意是单数，没有 s）。这是 BaseTool 上的一个属性，最简单的设置方式是直接写在 @tool 装饰器里：

## 实例
```
from langchain.tools import tool, ToolException

from langchain.agents import create_agent

from langchain.chat_models import init_chat_model

from langchain.messages import HumanMessage

# handle_tool_error=True：出错时不再抛异常，

# 而是把 ToolException 的内容转成字符串，正常返回给模型

@tool(handle_tool_error=True)

def get_weather(city: str) -> str:

    """查询指定城市的天气。

    Args:

        city: 城市名称，必须是中文全称，如 "杭州"、"北京"

    """

    weather_data = {

        "杭州": "晴，25°C",

        "北京": "多云，18°C",

        "上海": "小雨，22°C",

    }

    if city not in weather_data:

        # 城市不在数据中时抛出 ToolException

        raise ToolException(

            f"未收录城市 '{city}'。"

            f"可使用城市：{', '.join(weather_data.keys())}。"

            f"请使用中文城市全称。"

        )

    return f"{city}天气：{weather_data[city]}"

# 测试：用错误城市名调用

# handle_tool_error=True 时，错误信息会作为正常结果返回，而不是抛出异常

result = get_weather.invoke({"city": "北境"})

print(f"handle_tool_error=True: {result}")

# 如果想让所有工具的错误都由 Agent 统一处理（而不是逐个工具设置），

# 可以在 create_agent 内部使用的 ToolNode 层面配置。

# 在较新版本的 langchain 中，可以这样为整个 Agent 打开错误兜底：

model = init_chat_model("deepseek:deepseek-v4-flash", temperature=0)

agent = create_agent(

    model=model,

    tools=[get_weather],

    system_prompt="你是一个天气查询助手。",

)

result = agent.invoke({

    "messages": [HumanMessage(content="查询北境的天气")]

})

print("\n=== Agent 收到 handle_tool_error 转换后的错误信息，并据此向用户解释 ===")

print(result["messages"][-1].content[:200])
```

运行结果：

```
handle_tool_error=True: 未收录城市 '北境'。可使用城市：杭州, 北京, 上海。请使用中文城市全称。

=== Agent 收到 handle_tool_error 转换后的错误信息，并据此向用户解释 ===
抱歉，我没有查询到"北境"的天气数据。目前支持查询的城市有：杭州、北京、上海。
请问您是想查询其中哪一个城市呢？
```

| handle_tool_error | 行为 | 适用场景 |
| --- | --- | --- |
| False（默认） | ToolException 照常向上抛出，调用方需自行 try/except | 不可恢复的错误，需要中断流程 |
| True | 捕获 ToolException，将其内容作为工具的正常返回值交给模型 | 希望 Agent 自行阅读错误信息并修正/重试 |
| str | 捕获异常后，用指定的固定字符串替换错误信息 | 不想暴露具体报错细节，只给统一提示 |
| Callable[[ToolException], str] | 捕获异常后，用自定义函数处理异常并生成返回内容 | 需要按异常类型/内容定制不同的提示 |

> 注意：不要用 tool.with_config(handle_tool_errors=True) 这种写法——with_config() 是 Runnable 通用的运行时配置方法，只用于设置 callbacks、tags、metadata 等，并不会真正修改工具的错误处理行为。控制单个工具的错误处理，要用 @tool(handle_tool_error=...)（单数）；如果想在 Agent/图（Graph）层面统一为所有工具配置错误处理策略，则是在底层的 ToolNode 上设置 handle_tool_errors（复数），而不是作用在单个工具对象上。两者字段名相似但作用层级不同，使用时注意区分。

## 完整示例——带错误处理的 Agent

## 实例
```
from langchain.tools import tool, ToolException

from langchain.agents import create_agent

from langchain.chat_models import init_chat_model

from langchain.messages import HumanMessage

@tool(handle_tool_error=True)

def book_course(user_name: str, course_name: str) -> str:

    """为用户预订菜鸟教程 RUNOOB 的课程。

    Args:

        user_name: 用户姓名

        course_name: 课程名称

    """

    # 校验用户是否存在

    valid_users = {"张三", "李四", "王五"}

    if user_name not in valid_users:

        raise ToolException(

            f"用户 '{user_name}' 不存在。"

            f"有效用户：{', '.join(sorted(valid_users))}"

        )

    # 校验课程是否存在

    valid_courses = {"Python3 基础教程", "HTML 基础教程", "Java 面向对象"}

    if course_name not in valid_courses:

        raise ToolException(

            f"课程 '{course_name}' 不存在。"

            f"有效课程：{', '.join(sorted(valid_courses))}"

        )

    return f"已为 {user_name} 成功预订《{course_name}》"

model = init_chat_model("deepseek:deepseek-v4-flash", temperature=0)

agent = create_agent(

    model=model,

    tools=[book_course],

    system_prompt="你是菜鸟教程 RUNOOB 的课程顾问。",

)

# 正常调用

result = agent.invoke({

    "messages": [HumanMessage(content="帮张三预订 Python3 基础教程")]

})

print(f"成功: {result['messages'][-1].content[:100]}")

# 错误调用：用户不存在

result = agent.invoke({

    "messages": [HumanMessage(content="帮赵六预订 Python3 基础教程")]

})

print(f"\n错误-用户不存在:")

for msg in result["messages"]:

    if msg.type == "tool":

        print(f"  [{msg.type}] {msg.content[:80]}")

    elif msg.type == "ai" and msg.content:

        print(f"  [{msg.type}] {msg.content[:100]}")
```

运行结果：

```
成功: 已经为您成功预订《Python3 基础教程》，张三同学，祝您学习愉快！

错误-用户不存在:
  [tool] 用户 '赵六' 不存在。有效用户：张三, 李四, 王五
  [ai] 抱歉，系统中没有找到名为"赵六"的用户，暂时无法为您完成预订。
目前可预订的用户有：张三、李四、王五。请确认姓名后重新尝试。
```

> 可以看到，工具设置了 handle_tool_error=True 后，ToolException 的内容会以一条 ToolMessage 的形式正常出现在对话历史里（上面输出中的 [tool] 那一行），而不会让程序崩溃；模型看到这条错误信息后，会用自然语言把它转达给用户，并给出可用的替代方案。这正是 return_direct、InjectedToolCallId、ToolException 和 handle_tool_error 组合使用时的典型效果：既保证了工具调用的健壮性，又不牺牲用户体验。

其他扩展

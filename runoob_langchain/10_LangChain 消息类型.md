# LangChain 消息类型

在 LangChain 中，所有的对话都通过消息（Message）对象传递。理解各种消息类型的用途是编写 Agent 的基础。

## 四种核心消息类型

LangChain 定义了四种核心消息类型，分别对应对话中的不同角色：

| 类型 | 角色 | 说明 | 典型内容 |
| --- | --- | --- | --- |
| HumanMessage | 用户 | 用户发送的消息 | "今天天气怎么样？" |
| AIMessage | AI 助手 | 模型的回复，可能包含 tool_calls | "今天杭州晴天，25°C" |
| SystemMessage | 系统 | 系统指令，定义 AI 的角色和行为规则 | "你是一个专业的天气助手" |
| ToolMessage | 工具 | 工具执行后的返回结果 | "晴，25°C，湿度 60%" |

## HumanMessage——用户消息

HumanMessage 代表用户发送给 AI 的消息。它是最常见的消息类型，也是对话的起点。

## 实例
```
from langchain.messages import HumanMessage
```

运行结果：

```
类型: human
内容: 菜鸟教程 RUNOOB 是什么？
角色: user

模型回复: 菜鸟教程（RUNOOB）是一个面向编程初学者的学习网站，提供丰富的编程教程。
它的 Python 课程非常适合零基础学习者，从环境配置到基础语法再到实战项目都有覆盖。
```

### HumanMessage 的快捷创建方式

在构建消息列表时，可以使用元组或字典作为快捷方式：

## 实例
```
from langchain.messages import HumanMessage

# 方式 1：标准构造

msg1 = HumanMessage(content="你好")

# 方式 2：元组快捷方式 (role, content)

msg2 = ("user", "你好")

msg3 = ("human", "你好")

# 方式 3：字典快捷方式

msg4 = {"role": "user", "content": "你好"}

# 四种方式等价，都会在 Agent 内部被转换为 HumanMessage

print(type(msg1))  # <class 'langchain_core.messages.human.HumanMessage'>
```

## AIMessage——AI 回复

AIMessage 代表模型的回复。与普通文本不同，AIMessage 可能包含 tool_calls（工具调用请求）。

## 实例
```
from langchain.messages import AIMessage

# 普通 AI 回复（无工具调用）

ai_msg = AIMessage(content="菜鸟教程是一个编程学习平台")

# 包含工具调用的 AI 回复

ai_with_tools = AIMessage(

    content="",  # 工具调用时 content 通常为空

    tool_calls=[

        {

            "name": "get_weather",

            "args": {"city": "杭州"},

            "id": "call_abc123",

            "type": "tool_call",

        }

    ]

)

print("=== 普通 AI 消息 ===")

print(f"content: {ai_msg.content}")

print(f"tool_calls: {ai_msg.tool_calls}")   # []

print("\n=== 含工具调用的 AI 消息 ===")

print(f"content: {ai_with_tools.content}")

print(f"tool_calls: {ai_with_tools.tool_calls}")

# [{'name': 'get_weather', 'args': {'city': '杭州'}, ...}]
```

### AIMessage 的附加信息

## 实例
```
from langchain.chat_models import init_chat_model

model = init_chat_model("deepseek:deepseek-v4-flash")

response = model.invoke("介绍菜鸟教程 RUNOOB")

# AIMessage 包含丰富的元数据

print(f"内容: {response.content}")

print(f"消息ID: {response.id}")

print(f"模型名: {response.response_metadata.get('model_name')}")

print(f"完成原因: {response.response_metadata.get('finish_reason')}")

# usage_metadata 包含 Token 用量信息

if response.usage_metadata:

    print(f"输入 tokens: {response.usage_metadata.get('input_tokens')}")

    print(f"输出 tokens: {response.usage_metadata.get('output_tokens')}")

    print(f"总计 tokens: {response.usage_metadata.get('total_tokens')}")
```

运行结果：

```
内容: 菜鸟教程（RUNOOB）是一个面向初学者的免费编程学习平台...
消息ID: msg_abc123def456
模型名: deepseek-v4-flash
完成原因: stop
输入 tokens: 19
输出 tokens: 47
总计 tokens: 66
```

## SystemMessage——系统指令

SystemMessage 用于设定 AI 的行为、角色和约束。它放在消息列表的最前面，指导模型如何回复。

## 实例
```
from langchain.messages import HumanMessage, SystemMessage

from langchain.chat_models import init_chat_model

model = init_chat_model("deepseek:deepseek-v4-flash", temperature=0.7)

# 没有系统指令的回复

messages_no_system = [HumanMessage(content="介绍菜鸟教程")]

response = model.invoke(messages_no_system)

print(f"无系统指令: {response.content[:80]}...")

# 有系统指令的回复

messages_with_system = [

    SystemMessage(content="你是一个小红书风格的博主，回复要活泼、使用 emoji、带话题标签"),

    HumanMessage(content="介绍菜鸟教程")

]

response = model.invoke(messages_with_system)

print(f"\n有系统指令: {response.content}")
```

运行结果：

```
无系统指令: 菜鸟教程是一个面向初学者的在线编程学习平台，提供丰富的教程和实例...

有系统指令: 宝藏网站！给所有想学编程的新手安利菜鸟教程 RUNOOB！
超全面的免费教程，从 HTML 到 Python 全部都有唷～
实例超多上手超快，绝对是编程小白的入门神器！
#编程学习 #免费教程 #零基础入门 #菜鸟教程
```

## ToolMessage——工具返回结果

ToolMessage 包含工具执行后的返回结果。它必须与对应的 tool_call 关联。

## 实例
```
from langchain.messages import HumanMessage, AIMessage, ToolMessage

from langchain.chat_models import init_chat_model

# 模拟一轮完整的工具调用对话

messages = [

    HumanMessage(content="杭州天气怎么样？"),

    # 模型请求调用工具

    AIMessage(

        content="",

        tool_calls=[

            {"name": "get_weather", "args": {"city": "杭州"},

             "id": "call_abc", "type": "tool_call"}

        ]

    ),

    # 工具返回结果（必须包含 tool_call_id 与上面的 id 对应）

    ToolMessage(

        content="晴，25°C，湿度 60%",

        tool_call_id="call_abc",   # 与 tool_call 的 id 对应

        name="get_weather",        # 工具名称

    ),

]

model = init_chat_model("deepseek:deepseek-v4-flash")

response = model.invoke(messages)

print(f"模型基于工具结果的回复: {response.content}")
```

运行结果：

```
模型基于工具结果的回复: 杭州今天天气晴朗，气温25°C，湿度60%，适合户外活动。
```

> ToolMessage 的 tool_call_id 必须与 AIMessage 中 tool_call 的 id 精确匹配。如果不匹配，模型可能会忽略这个工具结果，或者产生混乱的行为。

## AIMessageChunk——流式输出的消息片段

当你使用 stream() 流式输出时，每个到达的片段是 AIMessageChunk，而非完整的 AIMessage：

## 实例
```
from langchain.chat_models import init_chat_model

model = init_chat_model("deepseek:deepseek-v4-flash")

print("流式输出过程：")

# stream() 返回的是 AIMessageChunk 迭代器

for chunk in model.stream("用一句话介绍菜鸟教程 RUNOOB"):

    # 每个 chunk 是一小段文本

    print(chunk.content, end="", flush=True)

print()  # 换行
```

运行结果：

```
流式输出过程：
菜鸟教程（RUNOOB）是一个面向编程初学者的免费在线学习平台，提供丰富的编程教程和实例。
```

## 消息类型速查表

| 消息类型 | type 属性 | role 属性 | 关键字段 | 何时使用 |
| --- | --- | --- | --- | --- |
| HumanMessage | human | user | content | 用户输入 |
| AIMessage | ai | assistant | content, tool_calls, usage_metadata | 模型回复 |
| AIMessageChunk | ai | assistant | content（增量） | 流式输出的片段 |
| SystemMessage | system | system | content | 设定 AI 角色 |
| ToolMessage | tool | tool | content, tool_call_id, name | 工具执行结果 |

## ContentBlock——结构化消息内容

到目前为止，我们使用的消息内容都是纯字符串。但实际上每条消息的内容可以是多个 ContentBlock（内容块）组成的列表。

最常用的三种内容块：

| 类型 | 说明 | 用途 |
| --- | --- | --- |
| PlainTextContentBlock | 纯文本内容 | 普通文字消息 |
| ImageContentBlock | 图片内容（base64 或 URL） | 多模态模型的图片输入 |
| ToolCall | 工具调用请求 | AI 请求调用工具 |

## 实例
```
from langchain.messages import HumanMessage

from langchain.messages import PlainTextContentBlock, ImageContentBlock

# 使用内容块构建消息

# content 可以是纯字符串（简单场景）

simple_msg = HumanMessage(content="你好")

# content 也可以是 ContentBlock 列表（复杂场景）

complex_msg = HumanMessage(content=[

    PlainTextContentBlock(text="这张图片里是什么？"),

    # 图片可以是 URL 或 base64 编码

    ImageContentBlock(

        url="https://example.com/photo.jpg"

    ),

])

print(f"简单消息内容类型: {type(simple_msg.content)}")

# 输出: <class 'str'>

print(f"复杂消息内容类型: {type(complex_msg.content)}")

# 输出: <class 'list'>

print(f"内容块数量: {len(complex_msg.content)}")

# 输出: 2
```

> 当你只需要发送纯文本时，直接传字符串即可，LangChain 会自动处理。只有当你需要在单条消息中混合文本和图片时，才需要手动构建 ContentBlock 列表。

## 多模态消息——让模型"看"图片

如果你的模型支持多模态输入（如 GPT-4o、Claude 3+），可以让它分析图片内容：

## 实例
```
import base64

from pathlib import Path

from langchain.messages import HumanMessage

from langchain.chat_models import init_chat_model

# 将本地图片编码为 base64

def encode_image(image_path: str) -> str:

    """读取图片文件并转换为 base64 编码"""

    with open(image_path, "rb") as f:

        return base64.b64encode(f.read()).decode("utf-8")

# 创建多模态模型（需支持图片输入）

model = init_chat_model("deepseek:deepseek-v4-flash")

# 构建包含图片的消息

# 注意：content 使用列表格式，包含文本块和图片块

image_data = encode_image("screenshot.png")

messages = [

    HumanMessage(content=[

        {"type": "text", "text": "请描述这张菜鸟教程 RUNOOB 官网截图的内容"},

        {

            "type": "image_url",

            "image_url": {

                "url": f"data:image/png;base64,{image_data}",

                "detail": "auto"  # 可选：low, high, auto

            }

        }

    ])

]

response = model.invoke(messages)

print(f"图片分析结果: {response.content}")
```

如果你的消息只包含图片不包含文字，可以直接用：

## 实例
```
from langchain.chat_models import init_chat_model

model = init_chat_model("deepseek:deepseek-v4-flash")

# 使用 URL 直接引用在线图片

messages = [

    {

        "role": "user",

        "content": [

            {"type": "text", "text": "这张图描述了什么内容？"},

            {

                "type": "image_url",

                "image_url": {"url": "https://www.runoob.com/wp-content/uploads/2024/01/logo.png"}

            }

        ]

    }

]

response = model.invoke(messages)

print(response.content)
```

> 并非所有模型都支持多模态输入。OpenAI 的 GPT-4o 系列、Anthropic 的 Claude 3+、Google 的 Gemini 系列支持。如果你用不支持的模型发送图片，会收到错误。

## ToolCall——工具调用消息

AIMessage 中的 tool_calls 字段是一个 ToolCall 列表，每个 ToolCall 代表模型请求调用一个工具：

## 实例
```
from langchain.messages import AIMessage

from langchain.messages.tool import ToolCall

# 手动构建一个 ToolCall

tool_call = ToolCall(

    name="get_weather",        # 工具名称

    args={"city": "杭州"},     # 调用参数

    id="call_abc123",         # 唯一标识

    type="tool_call",         # 固定值

)

# 创建包含 tool_calls 的 AIMessage

ai_message = AIMessage(

    content="",               # 有 tool_calls 时 content 通常为空

    tool_calls=[tool_call],

)

print(f"工具名称: {ai_message.tool_calls[0]['name']}")

print(f"调用参数: {ai_message.tool_calls[0]['args']}")

print(f"调用 ID: {ai_message.tool_calls[0]['id']}")
```

### 检查 AIMessage 是否包含工具调用

## 实例
```
from langchain.chat_models import init_chat_model

model = init_chat_model("deepseek:deepseek-v4-flash", temperature=0)

# 绑定工具后，模型可能返回 tool_calls

tools = [{

    "type": "function",

    "function": {

        "name": "get_weather",

        "description": "查询天气",

        "parameters": {

            "type": "object",

            "properties": {

                "city": {"type": "string", "description": "城市名"}

            },

            "required": ["city"]

        }

    }

}]

model_with_tools = model.bind_tools(tools)

# 触发工具调用的问题

response = model_with_tools.invoke("杭州天气怎么样？")

# 两种方式判断是否有工具调用

# 方式 1：检查 tool_calls 列表是否非空

if response.tool_calls:

    print("模型请求调用工具")

# 方式 2：检查 content 是否为空

# （大多数模型在有 tool_calls 时 content 为空）

if not response.content:

    print("模型的 content 为空，说明它想调用工具而非直接回复")
```

## trim_messages()——裁剪消息历史

当对话越来越长时，消息列表可能超出模型的上下文窗口。trim_messages() 函数帮助你智能地裁剪消息历史。

## 实例
```
from langchain.messages import (

    HumanMessage, AIMessage, SystemMessage, trim_messages

)

from langchain.chat_models import init_chat_model

# 模拟一段很长的对话历史

messages = [

    SystemMessage(content="你是菜鸟教程 RUNOOB 的 AI 助手"),

    HumanMessage(content="Python 怎么入门？"),

    AIMessage(content="Python 入门可以从基础知识开始..."),

    HumanMessage(content="有推荐的 IDE 吗？"),

    AIMessage(content="推荐 VS Code 或 PyCharm..."),

    HumanMessage(content="如何安装第三方库？"),

    AIMessage(content="使用 pip install 命令..."),

    HumanMessage(content="NumPy 是什么？"),

    AIMessage(content="NumPy 是一个科学计算库..."),

    HumanMessage(content="pandas 和 NumPy 有什么区别？"),

]

model = init_chat_model("deepseek:deepseek-v4-flash")

# 裁剪消息以适应模型的上下文窗口（最多 1000 tokens）

# strategy="last" 保留最后的系统消息和最近的对话

trimmed = trim_messages(

    messages,

    max_tokens=1000,           # 最多保留 1000 tokens

    strategy="last",           # 保留最后的系统消息 + 最近的对话

    token_counter=model,       # 使用模型的 token 计数方式

    include_system=True,       # 始终保留 SystemMessage

    start_on="human",          # 裁剪后以 human 消息开头

)

print(f"裁剪前: {len(messages)} 条消息")

print(f"裁剪后: {len(trimmed)} 条消息")

for msg in trimmed:

    snippet = msg.content[:50] if isinstance(msg.content, str) else str(msg.content)[:50]

    print(f"  [{msg.type}] {snippet}...")
```

运行结果：

```
裁剪前: 10 条消息
裁剪后: 5 条消息
  [system] 你是菜鸟教程 RUNOOB 的 AI 助手...
  [human] 如何安装第三方库？...
  [ai] 使用 pip install 命令...
  [human] NumPy 是什么？...
  [ai] NumPy 是一个科学计算库...
```

| 策略 | 说明 | 适用场景 |
| --- | --- | --- |
| strategy="last" | 保留 system 消息 + 最近的对话 | 长对话中只关心最新上下文 |
| strategy="first" | 保留 system 消息 + 最早的对话 | 确保关键上下文不被裁剪 |

> start_on="human" 确保裁剪后的消息列表以用户消息开头（而不是 AI 消息），避免让模型收到一条孤立的 AI 回复开头。

## RemoveMessage——删除特定消息

在某些高级场景中，你可能需要从消息历史中删除特定消息（如敏感内容清洗、重新生成回复等）：

## 实例
```
from langchain.messages import HumanMessage, AIMessage, RemoveMessage

# 假设有一段对话

messages = [

    HumanMessage(content="你好", id="msg_1"),

    AIMessage(content="你好！有什么可以帮你的？", id="msg_2"),

    HumanMessage(content="帮我查天气", id="msg_3"),

]

# 使用 RemoveMessage 删除特定消息（通过 ID）

# RemoveMessage 配合 add_messages reducer 使用

# 在更新 Agent 状态时，RemoveMessage 会从列表中移除对应 ID 的消息

removal = RemoveMessage(id="msg_3")

print(f"要删除的消息 ID: {removal.id}")

print(f"类型: {removal.type}")  # remove
```

> RemoveMessage 通常配合 AgentState 的 add_messages reducer 使用。在 middleware 或 after_model 钩子中返回 RemoveMessage 可以动态清理消息历史。

## 消息属性的通用方法

所有消息类型都继承自 BaseMessage，共享一些通用方法：

## 实例
```
from langchain.messages import HumanMessage, AIMessage

msg = HumanMessage(content="你好，菜鸟教程")

# 基本属性

print(f"content: {msg.content}")      # 消息内容

print(f"type: {msg.type}")            # 消息类型（human/ai/system/tool）

print(f"id: {msg.id}")                # 自动生成的唯一 ID

# text 属性：如果是文本内容，返回文本；否则返回 ""

print(f"text: {msg.text}")

# pretty_repr()：格式化打印，适合调试

print(f"美化输出:\n{msg.pretty_repr()}")
```

运行结果：

```
content: 你好，菜鸟教程
type: human
id: 00000000-0000-4000-8000-000000000000
text: 你好，菜鸟教程
美化输出:
================================ Human Message =================================
你好，菜鸟教程
```

其他扩展

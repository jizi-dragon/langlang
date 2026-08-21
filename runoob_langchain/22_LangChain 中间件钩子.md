# LangChain 中间件钩子 -- @before_model 与 @after_model

before_model 和 after_model 是最常用的两个 中间件（Middleware） 钩子。它们在每次模型调用前后执行，适合做内容过滤、消息预处理、响应审核等。

## @before_model——模型调用前拦截

@before_model 在每次调用模型之前执行。你可以在这里修改消息、注入上下文条件、或直接跳过模型调用。

### 场景 1：消息预处理——限制对话长度

## 实例
```
from dotenv import load_dotenv
```

运行结果：

```
消息数: 8
回复: 你好！看起来你正在进行多轮对话测试。有什么可以帮你的吗？
```

### 场景 2：内容过滤——屏蔽敏感词

## 实例
```
from langchain.agents.middleware import before_model

SENSITIVE_WORDS = ["密码", "银行卡号", "身份证号"]

@before_model

def content_filter(state, runtime):

    """检查用户消息是否包含敏感词，如果包含则拦截"""

    messages = state.get("messages", [])

    if not messages:

        return None

    last_msg = messages[-1]

    content = str(last_msg.content) if hasattr(last_msg, 'content') else ""

    for word in SENSITIVE_WORDS:

        if word in content:

            print(f"[拦截] 检测到敏感词: {word}")

            # jump_to="end" 直接结束，不让模型回复

            return {

                "jump_to": "end",

                "messages": [

                    HumanMessage(content=f"抱歉，为了安全，不能处理包含「{word}」的请求。")

                ]

            }

    return None

model = init_chat_model("deepseek:deepseek-v4-flash", temperature=0)

agent = create_agent(

    model=model,

    middleware=[content_filter],

    system_prompt="你是菜鸟教程 RUNOOB 的助手。",

)

# 正常问题

result = agent.invoke({

    "messages": [HumanMessage(content="Python 怎么入门？")]

})

print(f"正常问题: {result['messages'][-1].content[:80]}")

# 敏感问题

result = agent.invoke({

    "messages": [HumanMessage(content="我的银行卡号是多少？你能帮我查吗？")]

})

print(f"\n敏感问题: {result['messages'][-1].content}")
```

运行结果：

```
[拦截] 检测到敏感词: 银行卡号
正常问题: Python 入门可以从安装 Python 环境开始...

敏感问题: 抱歉，为了安全，不能处理包含「银行卡号」的请求。
```

## @after_model——模型调用后处理

@after_model 在模型回复后执行，适合审核模型输出、提取关键信息、追加后续指令等。

### 场景 3：响应内容审核

## 实例
```
from langchain.agents.middleware import after_model

FORBIDDEN_TOPICS = ["政治", "暴力", "色情"]

@after_model

def response_audit(state, runtime):

    """审核模型回复，如果涉及禁止话题则替换"""

    messages = state.get("messages", [])

    if not messages:

        return None

    last_msg = messages[-1]

    content = str(last_msg.content) if hasattr(last_msg, 'content') else ""

    for topic in FORBIDDEN_TOPICS:

        if topic in content:

            runtime.stream_writer({

                "type": "warning",

                "message": f"检测到回复包含「{topic}」相关内容，已被替换"

            })

            # 返回一个覆盖的消息（通过 add_messages reducer）

            from langchain.messages import AIMessage

            return {

                "messages": [

                    AIMessage(content="抱歉，我无法回答这个问题。"

                                      "请询问编程学习相关的内容。")

                ]

            }

    return None

model = init_chat_model("deepseek:deepseek-v4-flash", temperature=0)

agent = create_agent(

    model=model,

    middleware=[response_audit],

    system_prompt="你是菜鸟教程 RUNOOB 的助手。",

)

result = agent.invoke({

    "messages": [HumanMessage(content="Python 有哪些学习资源？")]

})

print(f"正常回复: {result['messages'][-1].content}")
```

### 场景 4：自动追加提示信息

## 实例
```
from langchain.agents.middleware import after_model

from langchain.messages import AIMessage

@after_model

def append_disclaimer(state, runtime):

    """在每次模型回复后自动追加免责声明"""

    messages = state.get("messages", [])

    if not messages:

        return None

    last_msg = messages[-1]

    # 只在 AI 的最终回复（没有 tool_calls）时追加

    if (last_msg.type == "ai"

        and last_msg.content

        and not (hasattr(last_msg, 'tool_calls') and last_msg.tool_calls)):

        # 替换最后一条 AI 消息，加上免责声明

        return {

            "messages": [

                AIMessage(

                    content=(

                        last_msg.content

                        + "\n\n---\n*以上内容由菜鸟教程 RUNOOB AI 助手生成，仅供参考。*"

                    )

                )

            ]

        }

    return None

model = init_chat_model("deepseek:deepseek-v4-flash", temperature=0)

agent = create_agent(

    model=model,

    middleware=[append_disclaimer],

    system_prompt="你是菜鸟教程的助手。",

)

result = agent.invoke({

    "messages": [HumanMessage(content="Python 容易学吗？")]

})

print(result["messages"][-1].content)
```

运行结果：

```
Python 是一门非常适合初学者的编程语言，它的语法简洁、贴近自然语言...
---
*以上内容由菜鸟教程 RUNOOB AI 助手生成，仅供参考。*
```

## can_jump_to——流程跳转控制

在 before_model 和 after_model 中，你可以通过 can_jump_to 参数和 jump_to 状态来控制 Agent 的流程：

## 实例
```
from langchain.agents.middleware import before_model

@before_model(can_jump_to=["end"])  # 声明可以跳转到的目标

def conditional_exit(state, runtime):

    """在特定条件下直接结束 Agent"""

    messages = state.get("messages", [])

    if not messages:

        return None

    # 如果用户说"再见"，直接结束

    last_content = str(messages[-1].content)

    if last_content.strip() in ["再见", "拜拜", "bye"]:

        return {

            "jump_to": "end",  # 直接结束 Agent

            "messages": [{"role": "assistant", "content": "再见！期待下次为您服务。"}]

        }

    return None
```

| can_jump_to 值 | 含义 | 适用场景 |
| --- | --- | --- |
| ["end"] | 可跳转到结束 | 条件退出、安全拦截 |
| ["model"] | 可跳转回模型 | 需要让模型重新处理 |
| ["tools"] | 可跳转到工具节点 | 跳过模型直接执行工具 |
| ["model", "end"] | 可跳转到模型或结束 | 多种条件分支 |

> 如果不在 can_jump_to 中声明目标，jump_to 会被忽略。这是一种安全机制，防止中间件意外跳转到不合法的节点。

其他扩展

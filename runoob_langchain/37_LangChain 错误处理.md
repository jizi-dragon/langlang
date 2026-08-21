# LangChain 错误处理与调试

Agent 开发中不可避免会遇到各种错误。本篇梳理常见错误类型、调试方法和最佳实践。

## 常见错误类型

| 错误类型 | 典型原因 | 解决方案 |
| --- | --- | --- |
| ImportError | 未安装提供商包 | pip install langchain-deepseek 等 |
| API Key 错误 | .env 未配置或 Key 无效 | 检查环境变量和 Key 有效性 |
| 超时错误 | 网络问题或模型响应慢 | 设置 timeout 参数 |
| Token 超限 | 消息历史过长 | 使用 trim_messages() 裁剪 |
| 工具调用错误 | 工具内部异常 | 使用 ToolException + handle_tool_errors |
| 模型返回格式错误 | 模型输出不符合预期 | 使用结构化输出 + handle_errors |

## ModelRetryMiddleware——模型调用重试

LangChain 提供了内置的重试中间件：

## 实例
```
from langchain.agents.middleware import ModelRetryMiddleware
```

## ToolRetryMiddleware——工具调用重试

## 实例
```
from langchain.agents.middleware import ToolRetryMiddleware

agent = create_agent(

    model="deepseek:deepseek-v4-flash",

    tools=[my_tool],

    middleware=[

        ToolRetryMiddleware(

            max_retries=3,

            backoff_factor=1.5,

        )

    ],

)
```

> 内置的 RetryMiddleware 和自定义的 @wrap_model_call / @wrap_tool_call 可以共存。内置中间件放在 middleware 列表前面作为最外层保护。

## debug=True——详细日志

## 实例
```
from langchain.agents import create_agent

from langchain.chat_models import init_chat_model

from langchain.messages import HumanMessage

# 开启 debug 模式，输出详细执行日志

agent = create_agent(

    model=init_chat_model("deepseek:deepseek-v4-flash"),

    debug=True,  # 开启调试日志

    system_prompt="你是菜鸟教程 RUNOOB 的助手。",

)

# 执行时会打印：

# - 每个节点的输入状态

# - 每个节点的输出状态

# - 边（edge）的跳转决策

result = agent.invoke({

    "messages": [HumanMessage(content="你好")]

})
```

debug=True 输出的示例：

```
[DEBUG] Starting graph execution
[DEBUG] Executing node: model
[DEBUG] Node 'model' input: {'messages': [HumanMessage(content='你好')]}
[DEBUG] Node 'model' output: {'messages': [AIMessage(content='你好！...')]}
[DEBUG] Edge 'model' -> '__end__': routing to __end__
[DEBUG] Graph execution complete
```

## stream_mode="debug"——最详细的调试信息

## 实例
```
# 通过 stream_mode="debug" 获取最详细的信息

for event in agent.stream(

    {"messages": [HumanMessage(content="你好")]},

    stream_mode="debug",

):

    # event 包含：节点名、输入、输出、时间戳、任务信息等

    print(f"[{event['type']}] {event.get('name', '')}")

    if 'input' in event:

        print(f"  输入: {event['input']}")

    if 'output' in event:

        print(f"  输出: {event['output']}")
```

## 常见问题排查

### 问题 1：模型一直调用工具不停止

可能原因：工具返回的信息不充分，模型无法判断任务是否完成。解决方法：

- 让工具返回更明确的信息（如"任务已完成"）
- 设置 system_prompt 中的停止条件
- 使用 after_model 检查循环次数，超过阈值后 jump_to="end"

### 问题 2：模型调用了错误的工具或参数

可能原因：工具描述不清晰。解决方法：

- 优化工具函数的文档字符串
- 使用 args_schema 限制参数范围
- 使用更好的模型（如 deepseek-v4-pro 替代 deepseek-v4-flash）

### 问题 3：对话记忆不生效

检查清单：

- 是否传入了 checkpointer 参数？
- 是否每次使用了相同的 thread_id？
- 如果使用 SqliteSaver，数据库文件是否存在且可写？

其他扩展

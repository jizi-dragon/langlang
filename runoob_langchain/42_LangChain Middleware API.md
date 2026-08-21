# LangChain Middleware API

## AgentMiddleware 基类钩子方法

| 方法 | 签名 | 执行频率 | 返回值 |
| --- | --- | --- | --- |
| before_agent | (state, runtime) → dict 或 None | 1 次 | 状态更新或 None |
| abefore_agent | (state, runtime) → dict 或 None | 1 次 | 状态更新或 None |
| before_model | (state, runtime) → dict 或 None | 每次循环 | 状态更新或 None |
| abefore_model | (state, runtime) → dict 或 None | 每次循环 | 状态更新或 None |
| wrap_model_call | (request, handler) → ModelResponse 或 AIMessage | 每次循环 | 模型调用结果 |
| awrap_model_call | (request, handler) → ModelResponse 或 AIMessage | 每次循环 | 模型调用结果 |
| after_model | (state, runtime) → dict 或 None | 每次循环 | 状态更新或 None |
| aafter_model | (state, runtime) → dict 或 None | 每次循环 | 状态更新或 None |
| wrap_tool_call | (request, handler) → ToolMessage 或 Command | 每次工具调用 | 工具执行结果 |
| awrap_tool_call | (request, handler) → ToolMessage 或 Command | 每次工具调用 | 工具执行结果 |
| after_agent | (state, runtime) → dict 或 None | 1 次 | 状态更新或 None |
| aafter_agent | (state, runtime) → dict 或 None | 1 次 | 状态更新或 None |

## 装饰器一览

| 装饰器 | 参数 | 说明 |
| --- | --- | --- |
| @before_agent | state_schema, tools, can_jump_to, name | Agent 开始前执行 |
| @after_agent | state_schema, tools, can_jump_to, name | Agent 结束后执行 |
| @before_model | state_schema, tools, can_jump_to, name | 模型调用前执行 |
| @after_model | state_schema, tools, can_jump_to, name | 模型调用后执行 |
| @wrap_model_call | state_schema, tools, name | 拦截模型执行 |
| @wrap_tool_call | tools, name | 拦截工具执行 |
| @dynamic_prompt | 无 | 动态生成系统提示词 |

## ModelRequest 关键属性

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| model | BaseChatModel | 当前模型 |
| messages | list[AnyMessage] | 消息列表（不含 system message） |
| system_message | SystemMessage 或 None | 当前系统消息 |
| tools | list | 可用工具列表 |
| tool_choice | Any | 工具选择策略 |
| response_format | ResponseFormat 或 None | 结构化输出格式 |
| state | dict | Agent 当前状态 |
| runtime | Runtime | 运行时上下文 |

ModelRequest 的 override() 方法用于创建带修改的新请求：

## 实例
```
new_request = request.override(
```

## ModelResponse 结构

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| result | list[BaseMessage] | 模型返回的消息列表 |
| structured_response | Any 或 None | 结构化输出结果 |

## 特殊返回值 ExtendedModelResponse

| 属性 | 说明 |
| --- | --- |
| model_response | 底层的 ModelResponse |
| command | 可选的 Command 对象，用于额外状态更新 |

其他扩展

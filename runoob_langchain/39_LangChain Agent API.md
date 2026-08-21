# LangChain Agent API

## create_agent() 完整参数

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| model | str 或 BaseChatModel | 无（必填） | 语言模型 |
| tools | Sequence 或 None | None | 工具列表。支持 @tool 函数、Pydantic 模型、dict |
| system_prompt | str 或 SystemMessage 或 None | None | 系统提示词 |
| middleware | Sequence[AgentMiddleware] | () | 中间件列表 |
| response_format | ResponseFormat 或 type 或 dict 或 None | None | 结构化输出配置 |
| state_schema | type[AgentState] 或 None | None | 自定义状态结构 |
| context_schema | type 或 None | None | 运行时上下文结构 |
| checkpointer | Checkpointer 或 None | None | 对话持久化 |
| store | BaseStore 或 None | None | 跨会话存储 |
| interrupt_before | list[str] 或 None | None | 在这些节点前暂停 |
| interrupt_after | list[str] 或 None | None | 在这些节点后暂停 |
| debug | bool | False | 是否输出详细日志 |
| name | str 或 None | None | Agent 名称 |
| cache | BaseCache 或 None | None | 缓存配置 |

## CompiledStateGraph 方法

| 方法 | 说明 |
| --- | --- |
| invoke(input, config=None) | 同步运行，返回最终状态 |
| ainvoke(input, config=None) | 异步运行，返回最终状态 |
| stream(input, config=None, stream_mode="updates") | 同步流式运行 |
| astream(input, config=None, stream_mode="updates") | 异步流式运行 |
| get_state(config) | 获取当前状态快照 |
| update_state(config, values) | 手动更新状态 |

## AgentState 结构

| 字段 | 类型 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| messages | list[AnyMessage] | 是 | 消息历史（add_messages reducer） |
| jump_to | "tools" 或 "model" 或 "end" 或 None | 否 | 流程跳转（ephemeral） |
| structured_response | Any | 否 | 结构化输出结果（OmitFromInput） |

## 常用用法示例

## 实例
```
from langchain.agents import create_agent
```

其他扩展

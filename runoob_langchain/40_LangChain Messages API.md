# LangChain Messages API

## 所有消息类型

| 类型 | role | type | 关键属性 | 说明 |
| --- | --- | --- | --- | --- |
| HumanMessage | user | human | content | 用户消息 |
| AIMessage | assistant | ai | content, tool_calls, usage_metadata | AI 回复 |
| AIMessageChunk | assistant | ai | content（增量） | 流式输出的 Token 片段 |
| SystemMessage | system | system | content | 系统指令 |
| ToolMessage | tool | tool | content, tool_call_id, name | 工具执行结果 |
| RemoveMessage | - | remove | id | 删除指定消息 |

## ContentBlock 类型（多模态内容）

| 类型 | 说明 | 使用场景 |
| --- | --- | --- |
| PlainTextContentBlock | 纯文本 | 普通文字 |
| ImageContentBlock | 图片（base64 或 URL） | 多模态模型的图片输入 |
| AudioContentBlock | 音频 | 语音输入 |
| VideoContentBlock | 视频 | 视频输入 |
| FileContentBlock | 文件 | 文档输入 |
| ToolCall | 工具调用请求 | 模型请求调用工具 |
| ServerToolCall | 服务端工具调用 | 内置/MCP 工具调用 |

## 常用辅助函数

| 函数 | 说明 | 签名 |
| --- | --- | --- |
| trim_messages() | 裁剪消息历史以适应上下文窗口 | trim_messages(messages, *, max_tokens, strategy, token_counter, include_system, start_on) |

## 常用用法示例

## 实例
```
from langchain.messages import (
```

其他扩展

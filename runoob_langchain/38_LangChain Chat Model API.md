# LangChain Chat Model API

本文档列出 init_chat_model() 和 BaseChatModel 的完整 API 参考。

## init_chat_model() 完整参数

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| model | str 或 None | 无 | 模型名，格式为 provider:model_name。传 None 创建可配置模型 |
| model_provider | str 或 None | None | 单独指定提供商。当 model 无法自动推断时使用 |
| configurable_fields | "any" 或 list 或 None | None | 可运行时修改的字段。None=固定模型，"any"=全部可配 |
| config_prefix | str 或 None | None | 多模型场景下的配置键前缀 |
| temperature | float | 因模型而异 | 控制随机性，0~2。0=确定，2=最大创造性 |
| max_tokens | int | 模型上限 | 输出最大 Token 数 |
| timeout | int/float 或 None | None | 请求超时秒数 |
| max_retries | int | 因模型而异 | 失败重试次数 |
| base_url | str 或 None | 官方地址 | 自定义 API 端点 |
| rate_limiter | BaseRateLimiter | 无 | 速率限制器 |
| top_p | float 或 None | 因模型而异 | 核采样参数，0~1 |
| stop | list[str] | 无 | 停止序列 |

## BaseChatModel 方法

| 方法 | 说明 | 返回值 |
| --- | --- | --- |
| invoke(input, config=None, **kwargs) | 同步调用模型 | AIMessage |
| ainvoke(input, config=None, **kwargs) | 异步调用模型 | AIMessage |
| stream(input, config=None, **kwargs) | 同步流式调用 | Iterator[AIMessageChunk] |
| astream(input, config=None, **kwargs) | 异步流式调用 | AsyncIterator[AIMessageChunk] |
| batch(inputs, config=None, **kwargs) | 批量调用 | list[AIMessage] |
| bind_tools(tools, **kwargs) | 绑定工具列表 | Runnable[input, AIMessage] |
| with_structured_output(schema, **kwargs) | 绑定结构化输出 Schema | Runnable[input, BaseModel/dict] |
| bind(**kwargs) | 绑定运行时参数 | Runnable |

## 支持的模型提供商速查

| provider 名 | 安装包 | 示例 model 值 |
| --- | --- | --- |
| openai | langchain-deepseek | deepseek:deepseek-v4-flash |
| anthropic | langchain-anthropic | anthropic:claude-sonnet-4-5-20250929 |
| deepseek | langchain-deepseek | deepseek:deepseek-chat |
| google_genai | langchain-google-genai | google_genai:gemini-2.5-flash |
| ollama | langchain-ollama | ollama:llama3.2 |
| groq | langchain-groq | groq:llama-3.3-70b |
| xai | langchain-xai | xai:grok-3 |
| mistralai | langchain-mistralai | mistralai:mistral-large |
| openrouter | langchain-openrouter | openrouter:openai/gpt-4o |
| perplexity | langchain-perplexity | perplexity:sonar-pro |

## 常用用法示例

## 实例
```
from langchain.chat_models import init_chat_model
```

其他扩展

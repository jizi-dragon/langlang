# LangChain 配置与错误类

## RunnableConfig 配置项

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| configurable | dict | 运行时配置。最常用：thread_id 用于 Checkpointer |
| recursion_limit | int | 最大递归深度（默认 9999） |
| metadata | dict | 附加元数据 |
| tags | list[str] | 标签列表，用于过滤和分组追踪 |
| callbacks | list[BaseCallbackHandler] | 回调处理器 |

## 实例
```
config = {
```

## Checkpointer 实现类

| 类 | 导入路径 | 持久化 |
| --- | --- | --- |
| InMemorySaver | langgraph.checkpoint.memory | 否 |
| SqliteSaver | langgraph.checkpoint.sqlite | 是 |
| PostgresSaver | langgraph.checkpoint.postgres | 是 |

## 实例
```
# 内存

from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()

# SQLite

from langgraph.checkpoint.sqlite import SqliteSaver

checkpointer = SqliteSaver.from_conn_string("checkpoints.db")

# PostgreSQL

# from langgraph.checkpoint.postgres import PostgresSaver

# checkpointer = PostgresSaver.from_conn_string("postgresql://...")
```

## Store 实现类

| 类 | 导入路径 | 持久化 |
| --- | --- | --- |
| InMemoryStore | langgraph.store.memory | 否 |
| PostgresStore | langgraph.store.postgres | 是 |

## 实例
```
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()

store.put(("namespace",), "key", {"data": "value"})

item = store.get(("namespace",), "key")

items = store.search(("namespace",))

store.delete(("namespace",), "key")
```

## 常见异常类

| 异常 | 来源 | 说明 |
| --- | --- | --- |
| ToolException | langchain.tools | 工具内部异常。Agent 可捕获并重新决策 |
| ImportError | Python 内置 | 缺少依赖包。错误信息会提示安装命令 |
| ValueError | Python 内置 | 参数验证失败或配置错误 |
| NotImplementedError | Python 内置 | Middleware 方法未实现（如只定义了同步但异步调用） |
| StructuredOutputError | langchain.agents.structured_output | 结构化输出相关错误（格式不符、多个输出等） |
| StructuredOutputValidationError | langchain.agents.structured_output | 结构化输出校验失败 |
| MultipleStructuredOutputsError | langchain.agents.structured_output | 模型返回了多个结构化输出 |
| TimeoutError | Python 内置 / 各 SDK | 请求超时 |

## LaunchDarkly 配置检查清单

| 检查项 | 命令/方法 |
| --- | --- |
| Python 版本 | python --version（需要 3.10+） |
| langchain 版本 | python -c "import langchain; print(langchain.__version__)" |
| 依赖安装 | pip list \| grep langchain |
| API Key 配置 | python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('DEEPSEEK_API_KEY', 'NOT SET')[:10])" |
| 模型连通性 | 使用 init_chat_model() 发送简单请求测试 |

> 本教程的 API 参考基于 LangChain v1.3.0。由于 LangChain 仍在快速发展，建议在使用时查阅最新的官方文档以获取最新 API 信息。

其他扩展

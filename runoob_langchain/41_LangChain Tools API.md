# LangChain Tools API

## @tool 装饰器

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| args_schema | BaseModel 或 None | None | 参数校验模型。不传则从函数签名自动生成 |
| return_direct | bool | False | 是否直接返回（跳过模型再思考） |
| name | str 或 None | 函数名 | 工具名称 |
| description | str 或 None | 函数文档字符串 | 工具描述 |

## BaseTool 主要属性与方法

| 属性/方法 | 说明 |
| --- | --- |
| name | 工具名称（字符串） |
| description | 工具描述（字符串） |
| args_schema | 参数 Pydantic 模型 |
| return_direct | 是否直接返回（bool） |
| invoke(input) | 调用工具，input 是参数字典 |
| ainvoke(input) | 异步调用工具 |

## 依赖注入标记

| 标记 | 用途 | 用法 |
| --- | --- | --- |
| InjectedState | 注入 Agent 状态 | Annotated[dict, InjectedState] |
| InjectedStore | 注入跨会话存储 | Annotated[BaseStore, InjectedStore()] |
| InjectedToolCallId | 注入工具调用 ID | Annotated[str, InjectedToolCallId] |
| InjectedToolArg | 通用注入标记 | Annotated[T, InjectedToolArg] |

## 常用用法示例

## 实例
```
from langchain.tools import tool, InjectedState, InjectedStore, ToolException
```

其他扩展

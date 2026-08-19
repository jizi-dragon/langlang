# test_03 · 工具高级特性（真实工程化版）

本章把 runoob 笔记中两个章节（`11 @tool.md` 基础、`12 工具高级特性.md`）的知识点，
挂到**真实的和风天气 API** 上重新实现，让你看清每个特性"在真实项目里该长在哪、什么时候必须用"。

## 三个核心问题

### 1. 为什么笔记学起来枯燥？

**根因不是你的问题，是笔记的呈现方式问题**：

- 笔记用 `search_courses / get_stock_price / convert_currency` 这类**硬编码字典**当工具返回值，
  你看到的其实是"Python 函数假装在干活"，没有任何副作用、没有真实 I/O。
- 真实项目的工具**必须有真实的副作用**——调外部 API、读写数据库、写日志——
  只有这样才能体会工具的价值：**"模型负责决策，工具负责真实地做事"**。
- 所以本章没有照抄它的假数据，而是全部换成真实天气 API（杭州今天真的晴 26~34°C）。

### 2. 这些特性要学到什么深度？

| 知识点 | 需要学多深 | 为什么 |
| --- | --- | --- |
| `@tool` 基本用法（docstring 驱动） | **必须掌握** | agent 的核心，写不好工具 agent 就不会正确调用 |
| `args_schema`（Pydantic 校验） | **必须掌握** | 真实项目脏参数进外部系统的第一道闸 |
| `ToolException` | **必须掌握** | 工具出错时向上表达，是 agent 稳健性的基础 |
| `handle_tool_error` | **必须掌握** | 让模型能"看到错误并自我修正"，是你既做 Agent 就绕不开的 |
| `return_direct` | **了解 + 会用** | 优化工具，用错场景会丢掉模型的总结能力 |
| `InjectedToolCallId` | **了解概念即可** | 审计/埋点才用，知道"运行时注入"的含义即可，用到再深入 |

一句话标准：**"工具怎么做"和"工具出错了怎么办"这两件事，直接决定你的 agent 会不会是玩具。**

### 3. 真实场景：什么时候用得上？

| 特性 | 真实使用场景 | 本项目示范 |
| --- | --- | --- |
| args_schema | 任何调外部 API / 数据库的工具，先校验入参再放行 | `01_args_schema.py`：城市白名单，防脏参数打到和风 |
| ToolException + handle_tool_error | 工具内部业务校验失败，希望模型能读错误并重新引导用户 | `02_tool_exception.py`：查不存在的城市 |
| return_direct | 天气/汇率/地图这类"结果即答案"的查询工具，省 token、降时延 | `03_return_direct.py` |
| InjectedToolCallId | 审计日志、埋点、把工具结果绑定回对话上下文 | `04_injected_tool_call_id.py` |

## 运行方式

```powershell
cd langchain-lab
.\dev.ps1 examples/test_03/01_args_schema.py
.\dev.ps1 examples/test_03/02_tool_exception.py
.\dev.ps1 examples/test_03/03_return_direct.py
.\dev.ps1 examples/test_03/04_injected_tool_call_id.py
```

## 对笔记的一处必要修正

runoob 笔记写 `@tool(handle_tool_error=True)` 作为装饰器参数，但 **langchain 1.3.15
的 `tool()` 装饰器不支持该参数**（签名只有 args_schema / return_direct 等）。
兼容且正确的写法是给工具实例赋值（单数，ToolNode 层才是复数 handle_tool_errors）：

```python
@tool
def f(...): ...
f.handle_tool_error = True
```

工具的 `ToolException` 抛出方式与笔记一致，二者组合才能让模型看到错误、自我修正。
# test_06 · Agent 扩充技能：提示词 / 流式输出 / 结构化输出 / 输出策略 / 中间件

本章把 runoob 笔记 **`17 提示词`、`18 流式输出`、`19 结构化输出`、`20 输出策略`、
`21 中间件`、`22 中间件钩子`** 六节，扣到"银行 / 电商客服质检"垂直场景里落脚。
其中**提示词、流式输出、结构化输出**你在前面章节已接触，本章是加深与辨析；
真正新的、也是**最值得理解的两块：中间件（含钩子）与自定义事件流**。

## 三个脚本各回答你一个困惑

### 01 中间件钩子：到底怎么用、解决什么问题（`01_middleware_hooks.py`）

中间件 = 处理"与回答内容无关"的**横切事务**（鉴权、敏感词、审核、统计）。没有它，
这些杂活会散落在每个工具/分支里到处重复；有了它，收拢到固定挂钩点即可。

- `@before_model(can_jump_to=["end"])`：**每次模型调用前**检查，命中敏感词就 `jump_to="end"`
  并预置安全回复，**模型这一步根本没执行**——合规/风控硬闸门。
- `@after_model`：**每次模型调用后**审核输出，涉禁区话题用兜底话术**替换**该条消息。
- `@after_agent`：**整次仅一次**，统计本轮模型被调了几次。

运行日志会让你直观看到钩子节律：带工具时 `before/after_model` **触发 2 次**，
`before/after_agent` **只触发 1 次**；命中敏感词的案例则整个循环只有 2 条消息。

### 02 自定义事件流：价值在"实时界面"（`02_custom_event_stream.py`）

自定义事件不是给你终端看的，是给**前端实时界面**的：界面除了要"回答正文"（`messages`），
还需要"进行到哪一步"（`custom`）。`runtime.stream_writer()` 让中间件把状态字典推给前端，
用户在等待的几秒能看到"正在思考… / 正在调用工具… / 已生成"。

脚本用 `stream_mode=["custom", "updates"]` 同时消费两类事件：
**custom** 报过程状态（来自 stream_writer），**updates** 报每节点产出（工具结果/回复）。

### 03 直接用 model 获取结构化输出（`03_structured_output_extract.py`）

判断标准一句话：**只要不需要工具/多步推理，就别上 Agent。**

- **信息提取**（客户原声 → 工单字段）：无工具、单次 → `model.with_structured_output(CustomerTicket)`，
  一次调用直接返回 Pydantic 实例，更快更省，可直接写工单系统。
- **多步推理**（查会员→算折扣→汇总）：需要工具循环 → 才用 `create_agent(response_format=...)`。
- DeepSeek 不支持原生 json_schema（test_05 已踩坑），`with_structured_output` 默认走
  function_calling 的 ToolStrategy，天然适配。

## 关于"输出策略"（20 节）的定位

你的判断是对的：**多数企业工程模型内定，根本不用手动选策略**——直接传 Pydantic，
LangChain 用 `AutoStrategy` 自动选即可。只有需要"出错重试"（`ToolStrategy(handle_errors=True)`）
或用到不支持原生结构化的模型时，才需显式指定。属于"知道有这回事"即可的知识，不必纠结。

## 工程文件

| 文件 | 主线 | 演示要点 |
|---|---|---|
| `01_middleware_hooks.py` | 银行客服质检 | before_model 敏感词拦截 + after_model 输出审核 + 钩子执行节律 |
| `02_custom_event_stream.py` | 电商客服质检 | stream_writer 推自定义事件 + custom/updates 双通道 |
| `03_structured_output_extract.py` | 工单系统 | with_structured_output 直接从原声提取工单字段 |
| `04_dump_invoke_stream.py` | 全量 dump | invoke 与 stream 各模式（messages/updates/values/custom/多模式）返回**原样完整**打印 |

## 运行方式

```powershell
cd langchain-lab
.\dev.ps1 examples/test_06/01_middleware_hooks.py
.\dev.ps1 examples/test_06/02_custom_event_stream.py
.\dev.ps1 examples/test_06/03_structured_output_extract.py
.\dev.ps1 examples/test_06/04_dump_invoke_stream.py
```

## 中间件钩子速查

| 钩子 | 时机 | 频率 | 用途 |
|---|---|---|---|
| `before_agent` / `after_agent` | Agent 开始 / 结束 | 仅 1 次 | 初始化、统计、清理 |
| `before_model` / `after_model` | 每次模型调用前 / 后 | 每轮 | 输入过滤、上下文注入、输出审核、token 统计 |
| `wrap_model_call` / `wrap_tool_call` | 包裹模型 / 工具 | 每轮 | 重试、降级、缓存、参数改写 |
| `can_jump_to=["end"]` | 配合 before/after | 声明可达目标 | 未声明的 jump_to 会被忽略（安全机制） |
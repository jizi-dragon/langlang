# test_05 · Agent 状态管理：AgentState 扩展 / stream_mode / jump_to / structured_response

本章把 runoob 笔记 `14 create_agent() 函数`、`15 Agent 工作流程`、`16 AgentState 状态管理` 三节，
放到**一个连贯的垂直场景（银行客服质检）**里落地，逐个验证你真正关心的三个问题。

## 你最关心的三个问题，先掰开

### 1. "我自定义扩展了 AgentState，它会在原有基础上扩展吗？" —— 会，关键是"继承"

`AgentState` 自带三个默认字段：`messages`（消息历史）、`jump_to`（流程跳转）、
`structured_response`（结构化结果）。自定义 state 时**必须继承 `AgentState`**，你的新字段只是**叠加**：

```python
class SupportAgentState(AgentState):   # 继承 → 默认字段还在
    member_tier: str                    # 新加的业务字段
    order_total: float
```

- state_schema 接受"继承了 AgentState 的子类" = **原有基础上扩展**，`messages`/`jump_to` 照常工作。
- 若改用一个**不继承**的裸 `TypedDict`，那只有你写的字段，`messages` 等全没，Agent 直接崩——
  "在原有基础上扩展"和"另起炉灶"的差别就在这一行继承。

运行 `01`，工具经 `InjectedState` 能读到 `member_tier/order_total`，且最终 state 里默认 `messages`
与自定义字段**并存**——直接证明"扩展而非替换"。

> 一个连带坑（02 里踩到）：扩展字段**必须用 state_schema 声明**，否则 `InjectedState`
> 在工具里读到的是 None（裸 dict 里没有这个 key）。

### 2. stream_mode 的 updates vs values —— 用途判断，你的理解是对的

- `updates`：只报**每个节点本次新增**的增量（model 节点报 AI 消息+tool_call、tools 节点报工具结果）。
  **轻、聚焦"模型这步做了什么"**——适合判断 Agent 有没有乱调工具、走了几步。
- `values`：每个节点后 dump **完整 state**（messages 全量累加）。**重、完整**——适合审计/回放，"每一步的完整输入输出"。

运行 `02` 对比同一个"查会员→算折扣→汇总"的循环，两种模式的打印密度一目了然。

### 3. jump_to="end" 和 structured_response 实用在哪？

- **jump_to="end"（垂直场景避免胡乱输出）**：用 `before_model` 中间件，在**模型被调用之前**先检查。
  命中规则（如违规词）就设 `state["jump_to"]="end"` 并预置一条安全 AIMessage——**模型那一步根本没执行**，
  只返回 2 条消息（human + 预置警示），不给模型自由发挥的机会。这是合规/风控场景的硬闸门。
- **structured_response（程序可直接消费的结论）**：业务要的不是自然语言，而是一份结构化结论时，
  用 `response_format` 让 Agent 输出固化进 `state["structured_response"]` 字段，
  再从中读，而不是去 parse 一段文本。

运行 `03` 看案例 A（违规被拦截、2 条消息）vs 案例 B（合规、产出受检结论）。

## 工程文件

| 文件 | 主线 | 演示要点 |
|---|---|---|
| `01_agent_state_extension.py` | 客服质检 | state_schema 继承扩展 + InjectedState 读自定义字段 |
| `02_stream_trace.py` | 电商客服 | updates vs values 同循环对比 |
| `03_jump_to_compliance.py` | 银行客服 | 违规 jump_to=end 拦截 + ToolStrategy 结构化输出 |

## 运行方式

```powershell
cd langchain-lab
# 先确保 Docker 启着（容器 langlab）
.\dev.ps1 examples/test_05/01_agent_state_extension.py
.\dev.ps1 examples/test_05/02_stream_trace.py
.\dev.ps1 examples/test_05/03_jump_to_compliance.py
```

## 本层的工程坑（实测）

| 现象 | 根因 | 解决方案 |
| --- | --- | --- |
| deepseek 报 400 "This response_format type is unavailable now" | `create_agent(response_format=裸Pydantic类)` 默认走 AutoStrategy→json_schema，DeepSeek 不支持原生 json_schema | 显式 `response_format=ToolStrategy(QualityCheck)`，走 function_calling 强制结构化 |
| `InjectedState` 读自定义字段为 None | 扩展字段没在 `state_schema` 声明，裸 state 里无该 key | 自定义字段必须先由自定义 State 类声明，再作为 state_schema 传入 |
| 违规请求没有被 jump_to 拦截 | 输入没精确命中中间件里的敏感词，被放行交给模型 | 中间件用**子串匹配** + 输入含完整敏感词，命中才设 jump_to=end |
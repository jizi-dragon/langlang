# test_04 · 工具访问：InjectedState / InjectedStore / InjectedToolArg

本章把 runoob 笔记 `13 工具访问.md` 的三个注入机制，放到**真实 SQLite 数据库持久化**的
业务场景里讲透，并纠正笔记用 InMemoryStore 带来的"持久化"误导。

## 你最关心的两个概念，先掰开

### 1. "用户偏好到底怎么收集来的？"

**结论：偏好不是框架收集的，是你（业务系统）写入 Store 的。**

runoob 伪代码里那行：
```python
store.put(("users", "user_001"), "profile", {...})
```
是作者**手写预置的假数据**，让你误以为框架会"自动收集"用户偏好。真实行业里，用户偏好的来源只有两个：

1. **业务库的存量数据**——用户早在 app 里填过资料（兴趣、会员状态等），就在你的 MySQL/SQLite 里。
   落地：Agent 启动前，你的业务代码把这些数据灌进 Store（一条用户 = 一个 namespace+key）。
2. **对话中当场透露的信息**——用户说"我对 X 感兴趣"，Agent 调 `save_interest` 这类工具，内部 `store.put(...)` 落库，下次对话就能读出来。

所以：**Store 是"读写的容器"，谁写谁读都由你的业务代码控制，框架只负责把访问能力注入给工具。**

### 2. "Agent 状态（State）到底是什么？"

**结论：State 是"这一次运行中，Agent 一路累积的数据快照"，对话结束就没了。**

Agent 处理一条消息，本质是状态机。每一步往 `state["messages"]`（以及你自定义的字段）里追加信息：

```
用户消息 → Agent思考(HumanMessage)
  → 决定调工具(AIMessage+tool_call)      state 累计
  → 工具返回(ToolMessage)                state 累计
  → Agent 组装最终回答(AIMessage)        state 累计
  → invoke 返回，整块 state 释放
```

**生命周期 = 一次 `agent.invoke()`**。返回即结束，不落盘。InjectedState 让工具能**读**这份运行中的状态（如当前对话消息统计），但它是"会话内的工作内存"，非持久化。

### 关键对比：InjectedState vs InjectedStore（回答"是不是一个东西"）

| | InjectedState | InjectedStore |
|---|---|---|
| 本质 | 本次运行的临时状态快照 | 跨会话的持久化存储 |
| 生命周期 | 一次 invoke 结束即消失 | 数据落库后永存 |
| 数据来源 | Agent 运行过程自己累积 | 业务代码写入（存量迁移 / 对话中保存） |
| 工具能做什么 | 只读当前对话上下文 | 读写长期数据 |
| 典型用途 | 对话统计、读同会话字段 | 用户偏好、学习进度、订单、档案 |

一句话：**Store 拉长信息的寿命（跨对话），State 只是当前这句话的信息积攒。**

> runoob 默认用 `InMemoryStore()`，那其实是**内存**，进程结束就没了，并不算真正持久化，
> 这也是"不学源码就觉得持久化了"的坑。正确工程化后端见下文。

## 本层的真实工程案例（数据库存储）

场景：**多租户电商客服 Agent**，工具真正读写一个 SQLite 数据库。

- `01_injected_store_sqlite.py`：用 `SqliteStore` 作为持久化后端，工具经 `InjectedStore`
  读写**真实落盘**的用户档案；对话中收集到新偏好也用工具写库，**跨进程验证数据仍在**。
- `02_injected_state.py`：工具读当前会话状态，统计"这轮对话聊到第几轮/几条消息"。
- `03_injected_tool_arg.py`：多租户场景，注入"当前租户 ID"这类宿主参数，模型不需要填。

## 运行方式

```powershell
cd langchain-lab
# 先确保 Docker 启着
.\dev.ps1 examples/test_04/01_injected_store_sqlite.py   # 数据库持久化 + 跨会话写入
.\dev.ps1 examples/test_04/02_injected_state.py          # 会话内状态读取
.\dev.ps1 examples/test_04/03_injected_tool_arg.py       # 通用注入标记
```

## 对 runoob 笔记的关键修正与工程坑

| 现象 | 根因 | 解决方案 |
| --- | --- | --- |
| 笔记用 `InMemoryStore`，误以为已持久化 | 内存本就进程级消失 | 换 `SqliteStore` 后端，数据真正落盘 SQLite 文件 |
| `sqlite3.OperationalError: cannot start a transaction within a transaction` | Python 3.11 sqlite3 默认隐式事务，与 SqliteStore 内部显式 BEGIN/COMMIT 冲突 | 用 `sqlite3.connect(..., isolation_level=None)`（autocommit） |
| `SQLite objects created in a thread can only be used in that same thread` | Agent 工具在线程池执行，SQLite 连接默认线程独占 | 建连接时加 `check_same_thread=False` |
| 自定义 `InjectedToolArg` 参数仍在 `properties` 里 | InjectedToolArg 只负责"剔除出 required"，不删字段 | 给注入参数设默认值（或 Optional），否则会留 required |
| 自定义 `InjectedToolArg` 宿主值没被自动填 | langgraph 内建自动注入仅限 State/Store/ToolCallId 三类 | 宿主自行在 ToolNode 前注入该值，框架不猜测来源 |

## InjectedToolArg 到底有什么意义（一句话）

它是"**这是个不需要模型填的宿主参数**"这一概念的**通用标记**：
- InjectedState / InjectedStore / InjectedToolCallId 都是它的**特化**。
- 当你要注入自定义东西（租户 ID、SDK 连接、MCP 对象）时，用 InjectedToolArg 标记，
  让 LangChain 把它从模型生成参数中剔除，实际值由你那边的宿主代码提供。
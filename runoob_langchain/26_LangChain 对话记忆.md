# LangChain 对话记忆 -- Checkpointer

默认情况下，每次 agent.invoke() 都是独立的，Agent 不记得之前聊过什么。

Checkpointer（检查点保存器）让 Agent 能够记住对话历史，实现真正的多轮对话。

## 没有 Checkpointer 的问题

先看看没有 Checkpointer 时的情况：

## 实例
```
from dotenv import load_dotenv
```

运行结果：

```
第一轮: 你好小明！很高兴认识你。
第二轮: 抱歉，我没有你的信息，不知道你叫什么名字。
```

## 使用 Checkpointer 记住对话

添加 Checkpointer 后，同一 thread_id 下的对话会自动关联：

## 实例
```
from langgraph.checkpoint.memory import InMemorySaver

from langchain.agents import create_agent

from langchain.chat_models import init_chat_model

from langchain.messages import HumanMessage

# 创建一个内存 Checkpointer

checkpointer = InMemorySaver()

model = init_chat_model("deepseek:deepseek-v4-flash", temperature=0)

agent = create_agent(

    model=model,

    checkpointer=checkpointer,  # 传入 Checkpointer

    system_prompt="你是菜鸟教程 RUNOOB 的助手。",

)

# 使用 thread_id 来标识对话线程

config = {"configurable": {"thread_id": "user-001"}}

# 第一轮

result1 = agent.invoke(

    {"messages": [HumanMessage(content="我叫小明，我在学 Python")]},

    config=config,

)

print(f"第一轮: {result1['messages'][-1].content}")

# 第二轮——使用相同的 thread_id，Agent 记住了！

result2 = agent.invoke(

    {"messages": [HumanMessage(content="我叫什么名字？我在学什么？")]},

    config=config,

)

print(f"第二轮: {result2['messages'][-1].content}")
```

运行结果：

```
第一轮: 你好小明！Python 是一门很好的入门语言，有什么需要帮助的吗？
第二轮: 你叫小明，你正在学习 Python。有什么具体问题我可以帮你吗？
```

> thread_id 是关键。同一个 thread_id 下的对话是连续的，不同 thread_id 之间的对话完全隔离。这让你可以用一个 Agent 实例同时服务多个用户。

## Checkpointer 的工作原理

Checkpointer 在每次 Agent 执行后自动保存状态快照（checkpoint）。下一次使用相同 thread_id 调用时，自动从最近的 checkpoint 恢复状态。

具体工作流程：

- 调用 agent.invoke()，传入 config（含 thread_id）
- Agent 检查是否有该 thread_id 的 checkpoint
- 如果有，加载历史消息，追加新消息后继续
- 执行完成后，自动保存新的 checkpoint

## 实例
```
from langgraph.checkpoint.memory import InMemorySaver

from langchain.agents import create_agent

from langchain.chat_models import init_chat_model

from langchain.messages import HumanMessage

checkpointer = InMemorySaver()

agent = create_agent(

    model=init_chat_model("deepseek:deepseek-v4-flash", temperature=0),

    checkpointer=checkpointer,

    system_prompt="你是菜鸟教程 RUNOOB 的助手。",

)

config = {"configurable": {"thread_id": "demo-001"}}

# 模拟多轮对话

questions = [

    "我叫小明",

    "我在学 Python",

    "帮我总结一下关于我的信息",

]

for i, q in enumerate(questions, 1):

    result = agent.invoke(

        {"messages": [HumanMessage(content=q)]},

        config=config,

    )

    # 查看 checkpoint 状态

    state = agent.get_state(config)

    print(f"\n第 {i} 轮后:")

    print(f"  消息数: {len(state.values.get('messages', []))}")

    print(f"  下一步: {state.next}")

    print(f"  回复: {result['messages'][-1].content[:80]}...")
```

运行结果：

```
第 1 轮后:
  消息数: 2
  下一步: ()
  回复: 你好小明！很高兴认识你。

第 2 轮后:
  消息数: 4
  下一步: ()
  回复: Python 是一门非常流行的编程语言，简单易学。

第 3 轮后:
  消息数: 6
  下一步: ()
  回复: 根据我们的对话，你的信息如下：你叫小明，正在学习 Python。
```

## Checkpointer 类型

| 类型 | 存储位置 | 持久化 | 安装 | 适用场景 |
| --- | --- | --- | --- | --- |
| InMemorySaver | 内存 | 否（程序退出后丢失） | 内置 | 开发调试、单元测试 |
| SqliteSaver | SQLite 数据库 | 是 | langgraph-checkpoint-sqlite | 单机部署、小型应用 |
| PostgresSaver | PostgreSQL | 是 | langgraph-checkpoint-postgres | 生产环境、多实例共享 |

如果 Agent 使用 ainvoke() 异步调用，需要改用对应的异步版本 AsyncSqliteSaver / AsyncPostgresSaver，用法与同步版本类似，只是需要配合 async with 使用。

### SqliteSaver 示例

InMemorySaver 只保存在内存中，程序退出后数据会丢失。如果希望对话能够持久化保存，可以使用 SqliteSaver。

首次使用需要安装 SQLite Checkpointer：

```
pip install langgraph-checkpoint-sqlite
```

## 实例
```
from langgraph.checkpoint.sqlite import SqliteSaver

from langchain.agents import create_agent

from langchain.chat_models import init_chat_model

from langchain.messages import HumanMessage

model = init_chat_model(

    "deepseek:deepseek-v4-flash",

    temperature=0,

)

# 必须用 with 语句进入，退出时会自动关闭数据库连接

with SqliteSaver.from_conn_string("conversations.db") as checkpointer:

    agent = create_agent(

        model=model,

        checkpointer=checkpointer,

        system_prompt="你是菜鸟教程 RUNOOB 的助手。",

    )

    config = {"configurable": {"thread_id": "user-001"}}

    result = agent.invoke(

        {

            "messages": [

                HumanMessage(content="你好")

            ]

        },

        config=config,

    )

    print(result["messages"][-1].content)
```

> SqliteSaver 会将每次对话产生的 checkpoint 保存在 SQLite 数据库中。即使程序退出或重新启动，只要继续使用相同的数据库文件和 thread_id，Agent 就能够恢复之前保存的对话状态。注意：with 代码块结束后数据库连接会关闭，因此涉及多次调用 Agent 的逻辑都应该放在 with 块内部；如果是长期运行的服务（如 Web 应用），建议在应用生命周期内持有该连接，或改用异步版本的 AsyncSqliteSaver。

## 管理对话线程

### 查看对话状态

## 实例
```
# 查看对话状态

state = agent.get_state(config)

print(f"下一步: {state.next}")  # () 表示空闲

print(f"消息数: {len(state.values.get('messages', []))}")

# 查看对话历史

for msg in state.values.get("messages", []):

    print(f"  [{msg.type}] {str(msg.content)[:60]}")
```

### 创建新线程

## 实例
```
# 不同的 thread_id = 不同的独立对话

config_alice = {"configurable": {"thread_id": "alice"}}

config_bob = {"configurable": {"thread_id": "bob"}}

# Alice 的对话

agent.invoke(

    {"messages": [HumanMessage(content="我是 Alice")]},

    config=config_alice,

)

# Bob 的对话——完全独立，不知道 Alice 说了什么

agent.invoke(

    {"messages": [HumanMessage(content="我是 Bob")]},

    config=config_bob,

)

# 验证隔离性

alice_state = agent.get_state(config_alice)

bob_state = agent.get_state(config_bob)

print(f"Alice 对话消息数: {len(alice_state.values['messages'])}")

print(f"Bob 对话消息数: {len(bob_state.values['messages'])}")
```

## 更新状态——手动修改对话

有时你需要手动修改对话状态，比如清空对话、插入系统消息等：

## 实例
```
from langchain.messages import SystemMessage

# 更新状态——插入一条系统消息

agent.update_state(

    config,

    {

        "messages": [

            SystemMessage(content="（用户升级到了 VIP 会员）")

        ]

    }

)

# 之后的对话会包含这条插入的消息
```

> update_state() 的参数会通过 add_messages reducer 处理（对 messages 字段而言），所以新消息会追加而不是覆盖。如果想清空历史重新开始，最简单的方式是换一个新的 thread_id；如果确实需要删除某几条历史消息，可以在 update_state() 中传入对应的 RemoveMessage（来自 langchain.messages）来精确移除指定的消息。

其他扩展

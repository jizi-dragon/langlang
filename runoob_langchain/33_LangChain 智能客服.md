# LangChain 智能客服机器人

本篇将前面学到的知识整合起来，构建一个完整的智能客服机器人。它能够查询知识库、处理订单、在必要时转接人工。

## 需求分析

| 功能 | 实现方式 |
| --- | --- |
| 知识库问答 | RAG 检索 + 模型回答 |
| 订单查询 | @tool 工具函数 |
| 对话记忆 | SqliteSaver Checkpointer |
| 敏感内容过滤 | @before_model Middleware |
| 人工转接 | HITL interrupt() / Command(resume=...) |

## 环境搭建

正式写代码之前，先把运行环境准备好。跟着下面几步操作，几分钟就能搭好。

### 第一步：确认 Python 版本

建议使用 Python 3.10 及以上版本。打开终端，输入：

```
python --version
```

如果版本低于 3.10，建议先升级 Python，再进行后续步骤。

### 第二步：创建并激活虚拟环境（推荐）

为了不污染系统的 Python 环境，建议为这个项目单独创建一个虚拟环境：

```
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境（Windows）
venv\Scripts\activate

# 激活虚拟环境（macOS / Linux）
source venv/bin/activate
```

激活成功后，终端提示符前面会出现 (venv) 字样。

### 第三步：安装依赖包

这个项目一共用到 6 个第三方库，分别负责不同的功能，建议按下面的顺序逐个安装，方便出问题时定位是哪一个库装的不对：

| 安装命令 | 作用 |
| --- | --- |
| pip install langchain | LangChain 核心库，提供 create_agent、@tool 等基础能力 |
| pip install langchain-deepseek | 让 init_chat_model 能识别 "deepseek:" 前缀，调用 DeepSeek 模型 |
| pip install langchain-openai | 提供 OpenAIEmbeddings，用于把知识库文本转成向量 |
| pip install langchain-chroma chromadb | 本地向量数据库，用于存储和检索知识库向量 |
| pip install langgraph-checkpoint-sqlite | SqliteSaver，把对话记忆持久化到 SQLite 文件 |
| pip install python-dotenv | 从 .env 文件读取 API 密钥等环境变量 |

也可以一条命令全部装好：

```
pip install langchain langchain-deepseek langchain-openai langchain-chroma chromadb langgraph-checkpoint-sqlite python-dotenv
```

### 第四步：配置 API 密钥

在项目根目录新建一个名为 .env 的文件（注意文件名以点开头，没有后缀），填入以下内容：

```
# DeepSeek 官网申请：https://platform.deepseek.com
DEEPSEEK_API_KEY=sk-你的deepseek密钥

# OpenAI 官网申请：https://platform.openai.com
# 这里只用来调用 embedding 接口，不涉及 Chat 模型
OPENAI_API_KEY=sk-你的openai密钥
```

如果没有 OpenAI 的 key，我们可以采用阿里百炼的，.env 的文件的代码如下：

```
# DeepSeek 官网申请：https://platform.deepseek.com
DEEPSEEK_API_KEY=sk-你的deepseek密钥

# 阿里云百炼控制台申请：https://bailian.console.aliyun.com
# 这里用来调用通义千问的 Embedding 服务，给知识库文本做向量化
DASHSCOPE_API_KEY=sk-你的百炼密钥
```

> .env 文件里保存的是私密密钥，务必不要提交到 Git 仓库或分享给他人。可以在项目里新建 .gitignore 文件，加入一行 .env 来避免误提交。

### 第五步：验证安装

新建一个 check_install.py 文件，运行下面的脚本，检查依赖和密钥是否都配置正确：

## 实例
```
# 文件路径：check_install.py
```

运行：

```
python check_install.py
```

如果正常配置了 key，输出如下：

```
langchain 版本: 1.3.0
环境配置成功~可以开始写客服机器人了！
```

如果报错，通常是某个包没装上或者 .env 里的密钥没填对，根据报错信息回到对应步骤检查即可。

## 完整代码

环境搭建完成后（依赖安装、.env 配置见上一节"环境搭建"），就可以编写完整的客服机器人代码了：

## 实例
```
# 文件路径：customer_service_bot.py

# 依赖安装、.env 配置见上一节"环境搭建"

from dotenv import load_dotenv

load_dotenv()

import os

import sqlite3

from typing import Annotated

from langchain.tools import tool

from langchain.agents import create_agent

from langchain.agents.middleware import before_model, after_model

from langchain.chat_models import init_chat_model

from langchain.messages import HumanMessage, AIMessage

from langchain_openai import OpenAIEmbeddings

from langchain_chroma import Chroma

from langchain_text_splitters import RecursiveCharacterTextSplitter

from langgraph.checkpoint.sqlite import SqliteSaver

from langgraph.types import interrupt, Command

# ========== 1. 准备知识库 ==========

knowledge_base = [

    "菜鸟教程 RUNOOB 创立于 2013 年，是国内领先的免费编程学习平台。",

    "平台提供 300+ 套教程，涵盖 Python、Java、HTML、CSS、JavaScript 等。",

    "Python3 基础教程共 30 章，累计学习人次超 500 万。课程完全免费。",

    "VIP 会员费用为 ¥99/月，¥799/年，包含视频课程和一对一答疑服务。",

    "退款政策：购买 7 天内且在 3 节课以内可全额退款。",

    "平台支持在线编程环境，无需安装任何软件即可编写运行代码。",

    "客服工作时间：周一至周五 9:00-18:00，周末 10:00-16:00。",

]

# 使用阿里云百炼（DashScope）的通义千问 Embedding 服务

# 百炼的 Embedding 接口兼容 OpenAI 接口规范，所以直接用 langchain-openai

# 的 OpenAIEmbeddings，把 base_url 指向百炼的兼容端点即可，

# 不需要再装 langchain-community / dashscope（该包已停止维护）。

# text-embedding-v4 是目前推荐的通用向量模型，默认输出 1024 维向量。

#

# 两个关键参数不能少：

# - check_embedding_ctx_length=False：OpenAIEmbeddings 默认会用 tiktoken

#   把文本预先编码成 token id 数组再发送（OpenAI 官方接口认这个格式），

#   但百炼的兼容接口只接受原始字符串，不关掉这个选项会报

#   "contents is neither str nor list of str" 错误。

# - chunk_size=10：百炼 Embedding 接口单次请求最多接受 10 条文本，

#   OpenAIEmbeddings 默认一次打包 1000 条，知识库稍大就会超限报错。

embeddings = OpenAIEmbeddings(

    model="text-embedding-v4",

    api_key=os.getenv("DASHSCOPE_API_KEY"),

    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",

    check_embedding_ctx_length=False,

    chunk_size=10,

)

chunks = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=30

                                         ).create_documents(knowledge_base)

vector_store = Chroma.from_documents(chunks, embeddings)

retriever = vector_store.as_retriever(search_kwargs={"k": 3})

# ========== 2. 定义工具 ==========

@tool

def search_kb(query: str) -> str:

    """搜索菜鸟教程知识库，获取关于平台、课程、政策等官方信息。

    Args:

        query: 搜索问题或关键词

    """

    docs = retriever.invoke(query)

    if not docs:

        return "未找到相关信息，建议转接人工客服。"

    return "\n".join(f"- {doc.page_content}" for doc in docs)

# 模拟订单数据库

orders_db = {

    "ORD-2024-001": {"user": "小明", "item": "VIP 年费会员",

                      "amount": 799, "status": "已完成", "date": "2024-01-15"},

    "ORD-2024-002": {"user": "小明", "item": "Python 实战课程",

                      "amount": 199, "status": "配送中", "date": "2024-03-20"},

}

@tool

def query_order(order_id: str) -> str:

    """根据订单号查询订单状态和详情。

    Args:

        order_id: 订单号，如 ORD-2024-001

    """

    order = orders_db.get(order_id.upper())

    if not order:

        return f"未找到订单 {order_id}。请确认订单号是否正确。"

    return (f"订单 {order_id}：{order['item']} | "

            f"金额 ¥{order['amount']} | "

            f"状态 {order['status']} | "

            f"日期 {order['date']}")

@tool

def transfer_to_human(reason: str) -> str:

    """将用户转接给人工客服。

    Args:

        reason: 转接原因

    """

    approval = interrupt({

        "action": "transfer_to_human",

        "reason": reason,

        "message": f"用户请求转接人工客服，原因：{reason}。是否转接？"

    })

    if approval.get("confirmed"):

        return (f"已为您转接人工客服，预计等待 {approval.get('wait_time', 3)} 分钟。"

                f"工单号：TK-{approval.get('ticket_id', 'N/A')}")

    return "转接已取消，我继续为您服务。"

# ========== 3. 定义 Middleware ==========

@before_model

def content_guard(state, runtime):

    """过滤用户输入中的不当内容"""

    last_msg = state["messages"][-1] if state.get("messages") else None

    if not last_msg:

        return None

    content = str(getattr(last_msg, 'content', ''))

    blocked = ["黄X", "X博", "违法"]

    for word in blocked:

        if word in content:

            return {

                "jump_to": "end",

                "messages": [HumanMessage(content="抱歉，我不能处理这个请求。")]

            }

    return None

@after_model

def auto_signature(state, runtime):

    """自动追加客服签名"""

    msgs = state.get("messages", [])

    if not msgs:

        return None

    last = msgs[-1]

    if last.type == "ai" and last.content and not (

        hasattr(last, 'tool_calls') and last.tool_calls

    ):

        # 关键：复用 last.id，让 add_messages reducer 原地替换该消息，

        # 而不是把它当成一条新消息追加到历史里（否则历史会越滚越大，

        # 每轮多出一条"无签名版"和一条"带签名版"）

        return {"messages": [AIMessage(

            id=last.id,

            content=last.content

            + "\n\n---\n菜鸟教程 RUNOOB 客服中心 | 工作时间 9:00-18:00"

        )]}

    return None

# ========== 4. 创建 Agent ==========

# SqliteSaver.from_conn_string() 返回的是上下文管理器，只适合"用完即关"的

# 一次性脚本。客服机器人需要在多次 chat() 调用之间保持同一个数据库连接，

# 所以这里自己建立连接后传给 SqliteSaver 构造函数。

# check_same_thread=False 是因为 Web 框架通常会跨线程调用同一个连接。

conn = sqlite3.connect("customer_service.db", check_same_thread=False)

checkpointer = SqliteSaver(conn)

model = init_chat_model("deepseek:deepseek-v4-flash", temperature=0)

agent = create_agent(

    model=model,

    tools=[search_kb, query_order, transfer_to_human],

    middleware=[content_guard, auto_signature],

    checkpointer=checkpointer,

    system_prompt="""你是菜鸟教程 RUNOOB 的智能客服"小菜"。

## 你的职责

1. 热情接待每一位用户，用"您"称呼

2. 关于平台信息、课程内容、政策等问题，使用 search_kb 查询

3. 关于订单查询，使用 query_order 工具

4. 遇到无法解决的问题，使用 transfer_to_human 转接人工

## 行为准则

- 回答简洁，每次 2-3 句话

- 不知道的就查询知识库，查不到就诚实告知

- 保持友好亲切的语气""",

)

# ========== 5. 对话接口 ==========

def chat(thread_id: str, message: str) -> str:

    """处理用户消息并返回回复"""

    config = {"configurable": {"thread_id": thread_id}}

    # 运行 Agent

    result = agent.invoke(

        {"messages": [HumanMessage(content=message)]},

        config=config,

    )

    # 检查是否需要转接（HITL）

    state = agent.get_state(config)

    if state.tasks and state.tasks[0].interrupts:

        interrupt_info = state.tasks[0].interrupts[0].value

        return f"[需要审批] {interrupt_info.get('message', '')}"

    return result["messages"][-1].content

def resume_transfer(thread_id: str, confirmed: bool,

                     wait_time: int = 3, ticket_id: str = "0001") -> str:

    """人工客服后台审批后，恢复被 interrupt() 中断的转接流程。

    对应 transfer_to_human 工具里等待的 approval 数据。

    """

    config = {"configurable": {"thread_id": thread_id}}

    result = agent.invoke(

        Command(resume={

            "confirmed": confirmed,

            "wait_time": wait_time,

            "ticket_id": ticket_id,

        }),

        config=config,

    )

    return result["messages"][-1].content

# ========== 6. 测试 ==========

if __name__ == "__main__":

    user_id = "user_xiaoming"

    print("=== 测试 1：知识库查询 ===")

    print(chat(user_id, "Python3 教程有多少章？"))

    print()

    print("=== 测试 2：订单查询 ===")

    print(chat(user_id, "我的订单 ORD-2024-001 状态是什么？"))

    print()

    print("=== 测试 3：VIP 咨询 ===")

    print(chat(user_id, "VIP 会员多少钱？"))

    print()

    print("=== 测试 4：测试记忆 ===")

    print(chat(user_id, "我刚才问过什么问题？"))

    print()

    print("=== 测试 5：人工转接（HITL） ===")

    print(chat(user_id, "我要投诉，请转人工"))       # 触发 interrupt，等待审批

    print(resume_transfer(user_id, confirmed=True,

                           wait_time=5, ticket_id="8823"))  # 后台确认后恢复

    conn.close()
```

运行结果：

```
=== 测试 1：知识库查询 ===
您好！菜鸟教程的 **Python3 基础教程共 30 章**，完全免费，累计学习人次已超 500 万哦！如需了解其他教程，也可以随时问我～

---
菜鸟教程 RUNOOB 客服中心 | 工作时间 9:00-18:00

=== 测试 2：订单查询 ===
您好！您查询的订单 **ORD-2024-001** 状态为 **已完成**。订单内容是 **VIP 年费会员**，金额 **¥799**，下单日期为 **2024-01-15**。请问还有什么可以帮您的吗？

---
菜鸟教程 RUNOOB 客服中心 | 工作时间 9:00-18:00

=== 测试 3：VIP 咨询 ===
您好！VIP 会员有 **¥99/月** 和 **¥799/年** 两种套餐，包含视频课程和一对一答疑服务哦～请问您需要办理哪种呢？

---
菜鸟教程 RUNOOB 客服中心 | 工作时间 9:00-18:00

---
菜鸟教程 RUNOOB 客服中心 | 工作时间 9:00-18:00

=== 测试 4：测试记忆 ===
您好！您刚才问了以下三个问题：
1. **Python3 教程有多少章？** —— 共 30 章，完全免费
2. **我的订单 ORD-2024-001 状态是什么？** —— 状态为"已完成"
3. **VIP 会员多少钱？** —— ¥99/月 或 ¥799/年

还有什么需要我帮忙的吗？

---
菜鸟教程 RUNOOB 客服中心 | 工作时间 9:00-18:00

---
菜鸟教程 RUNOOB 客服中心 | 工作时间 9:00-18:00

=== 测试 5：人工转接（HITL） ===
[需要审批] 用户请求转接人工客服，原因：用户要求投诉，需要转接人工客服处理。是否转接？
您好！已经为您转接人工客服，预计等待约 5 分钟。您的工单号是 **TK-8823**，请稍候，客服会尽快为您处理～

---
菜鸟教程 RUNOOB 客服中心 | 工作时间 9:00-18:00

---
菜鸟教程 RUNOOB 客服中心 | 工作时间 9:00-18:00
```

## 项目总结

这个客服机器人整合了以下 LangChain 特性：

| 特性 | 在项目中的使用 |
| --- | --- |
| RAG 检索 | search_kb 工具 + Chroma 向量存储 |
| 工具调用 | query_order、transfer_to_human |
| Checkpointer | SqliteSaver 持久化对话，实现多轮记忆 |
| Middleware | before_model 内容过滤 + after_model 签名追加（复用消息 id 原地替换） |
| HITL | interrupt() 暂停执行 + Command(resume=...) 审批后恢复，实现完整的人工转接闭环 |

其他扩展

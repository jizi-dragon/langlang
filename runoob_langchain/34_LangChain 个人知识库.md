# LangChain 个人知识库问答系统

本篇构建一个能加载 Markdown 文件、PDF 文档，并基于这些内容进行问答的个人知识库系统。

## 系统设计

- 文档加载：支持 Markdown、TXT、PDF 多种格式
- 向量检索：Chroma 持久化存储，支持增量更新
- 引用来源：回答中附带来源文档和片段位置
- 流式输出：逐 Token 显示回答

## 完整代码

运行前需要在 .env 文件中配置 DEEPSEEK_API_KEY（Chat 模型）和 DASHSCOPE_API_KEY（阿里云百炼，用于知识库文本向量化），具体申请方式和常见问题排查见《LangChain 智能客服机器人》一节。

## 实例
```
# 文件路径：knowledge_qa.py
```

> 目前 TextLoader、PyPDFLoader 这类本地文件加载器还没有独立出来的维护包，仍然只能从 langchain_community.document_loaders 导入，运行时可能会看到 langchain-community 整体的 DeprecationWarning——这个警告目前可以忽略，等官方推出独立的文档加载器包后再迁移即可；和前面 embedding 那种"已有现成替代方案却没换"的情况不同。

继续 Agent 部分：

## 实例
```
# ========== 创建知识库并添加示例数据 ==========

kb = KnowledgeBase("./my_knowledge_db")

# 添加一些示例知识

kb.add_text(

    "菜鸟教程 RUNOOB 的 Python3 基础教程包含以下章节："

    "1. Python 简介与环境搭建 2. 基本数据类型 3. 运算符与表达式 "

    "4. 条件判断 if-else 5. 循环 for/while 6. 函数定义与调用 "

    "7. 模块与包 8. 文件操作 9. 异常处理 10. 面向对象编程",

    source="Python3 教程大纲"

)

kb.add_text(

    "要成为一名优秀的 Python 开发者，建议按以下路线学习："

    "第一步，掌握 Python 基础语法（1-2 周）；"

    "第二步，学习数据结构和算法基础（2-3 周）；"

    "第三步，选择一个方向深入学习（Web 开发/数据分析/AI）；"

    "第四步，做 2-3 个实战项目巩固知识。",

    source="Python 学习路线"

)

kb.add_text(

    "菜鸟教程的在线编程环境支持 Python、JavaScript、Java、C++ 等多种语言。"

    "用户无需安装任何软件，打开浏览器即可编写和运行代码。"

    "在线环境还支持代码高亮、自动补全和错误提示功能。",

    source="在线编程环境说明"

)

# 也可以加载本地文件，PDF 和 Markdown/TXT 都会自动识别：

# kb.add_file("./docs/产品手册.pdf")

# kb.add_file("./docs/常见问题.md")

# ========== 创建 RAG Agent ==========

@tool

def search_knowledge(query: str) -> str:

    """在个人知识库中搜索相关信息。搜索时使用完整的问题或关键短语。

    Args:

        query: 搜索问题或关键短语

    """

    docs = kb.search(query, k=3)

    if not docs:

        return "知识库中未找到相关信息。"

    results = []

    for i, doc in enumerate(docs, 1):

        source = doc.metadata.get("source", "未知来源")

        page = doc.metadata.get("page")

        location = f"{source}" + (f" 第 {page + 1} 页" if page is not None else "")

        content = doc.page_content[:200]

        results.append(f"[{i}] 来源：{location}\n{content}")

    return "\n\n---\n\n".join(results)

model = init_chat_model("deepseek:deepseek-v4-flash", temperature=0)

agent = create_agent(

    model=model,

    tools=[search_knowledge],

    system_prompt="""你是个人知识库助手。

## 规则

1. 所有问题必须先用 search_knowledge 工具检索知识库

2. 回答时注明信息来源（文档名称，如果是 PDF 还要注明页码）

3. 如果知识库中没有相关内容，如实告知

4. 回答要结构化，使用数字列表或分段""",

)

# ========== 测试：非流式，同时看检索到的内容 ==========

def ask(question: str):

    """提问，同时打印检索到的原始片段和最终回答，方便调试"""

    print(f"\n{'='*60}")

    print(f"Q: {question}")

    print(f"{'='*60}")

    result = agent.invoke({

        "messages": [HumanMessage(content=question)]

    })

    # 显示检索到的内容

    for msg in result["messages"]:

        if msg.type == "tool":

            print(f"\n[检索到的内容]")

            print(msg.content[:300])

    print(f"\n[回答]")

    print(result["messages"][-1].content)

# ========== 测试：流式，对应系统设计里的"流式输出" ==========

def ask_stream(question: str):

    """提问并逐 Token 流式打印回答，实现打字机效果"""

    print(f"\n{'='*60}")

    print(f"Q: {question}")

    print(f"{'='*60}")

    print("\n[回答] ", end="", flush=True)

    for chunk, metadata in agent.stream(

        {"messages": [HumanMessage(content=question)]},

        stream_mode="messages",

    ):

        # metadata["langgraph_node"] == "model" 表示这个 chunk 来自模型生成

        # 最终回答的节点，过滤掉工具调用等其他类型的 chunk

        if metadata.get("langgraph_node") == "model" and chunk.content:

            print(chunk.content, end="", flush=True)

    print()

ask("Python3 基础教程包含哪些章节？")

ask("如何规划 Python 学习路线？")

ask_stream("菜鸟教程的在线编程环境支持哪些功能？")
```

运行结果：

```
============================================================
Q: Python3 基础教程包含哪些章节？
============================================================

[检索到的内容]
[1] 来源：Python3 教程大纲
菜鸟教程 RUNOOB 的 Python3 基础教程包含以下章节：...

[回答]
Python3 基础教程包含以下章节（来源：Python3 教程大纲）：
1. Python 简介与环境搭建
2. 基本数据类型
3. 运算符与表达式
...

============================================================
Q: 如何规划 Python 学习路线？
============================================================

[回答]
根据知识库中的 Python 学习路线建议（来源：Python 学习路线）：
第一步：掌握基础语法（1-2 周）
第二步：学习数据结构和算法（2-3 周）
第三步：选择方向深入学习（Web/数据分析/AI）
第四步：做 2-3 个实战项目巩固

============================================================
Q: 菜鸟教程的在线编程环境支持哪些功能？
============================================================

[回答] 根据知识库中的说明（来源：在线编程环境说明），菜鸟教程的在线编程环境：
1. 支持 Python、JavaScript、Java、C++ 等多种语言
2. 无需安装任何软件，打开浏览器即可编写和运行代码
3. 支持代码高亮、自动补全和错误提示功能
```

> 最后一个问题用的是 ask_stream()，实际运行时"[回答]"后面的文字会一个字一个（或几个字符一批）地陆续打印出来，就像打字机效果；上面为了方便展示，直接贴出了打印完成后的最终文本。

其他扩展

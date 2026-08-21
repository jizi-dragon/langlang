# LangChain 构建 RAG Agent

前两篇我们准备了向量存储和检索器。

本篇将它们集成到 Agent 中，构建一个完整的 RAG Agent——能够基于私有知识库回答问题的智能助手。

## 创建 Retriever 工具

将检索器包装成一个工具，Agent 就能在需要时自动搜索知识库。

如果没有 OpenAI 的 key 可以采用阿里百炼的 Embedding 服务，参考配置 https://www.runoob.com/langchain/langchain-alibailian.html：

```
# OpenAI 的文本嵌入模型
# 将文本转换为向量（一组浮点数）

# 使用阿里云百炼（DashScope）的通义千问 Embedding 服务
embeddings = OpenAIEmbeddings(
    model="text-embedding-v4",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    check_embedding_ctx_length=False,
    chunk_size=10,
)
```

## 实例（OpenAI）
```
import os
```

运行结果：

```
Q: 菜鸟教程是什么时候创立的？
A: 菜鸟教程（RUNOOB）创立于 2013 年，是一个完全免费的编程学习平台。
------------------------------------------------------------
Q: Python3 基础教程有多少章？
A: Python3 基础教程共 30 章，包含环境搭建、基本语法、函数、类、异常处理等内容。
------------------------------------------------------------
Q: 菜鸟教程一共有多少套教程？
A: 菜鸟教程已上线 300+ 套教程，涵盖前端、后端、数据库、移动开发等多个领域。
------------------------------------------------------------
```

## RAG Agent 的执行流程

对于上面的第三个问题"菜鸟教程一共有多少套教程？"，Agent 的执行流程是：

- 用户提问
- 模型判断需要查询知识库 → 调用 search_knowledge_base("菜鸟教程 教程数量")
- 检索器从向量数据库中搜索语义最相似的文档块
- 将检索结果返回给模型
- 模型基于检索结果生成准确回答

## 添加引用来源

专业的 RAG 系统通常会附带引用来源，让用户知道信息来自哪里：

## 实例
```
from langchain_core.documents import Document

@tool

def search_with_sources(query: str) -> str:

    """在菜鸟教程知识库中搜索，返回带来源标注的结果。

    Args:

        query: 搜索关键词

    """

    docs = retriever.invoke(query)

    if not docs:

        return "未找到相关信息。"

    results = []

    for i, doc in enumerate(docs, 1):

        source = doc.metadata.get("source", "菜鸟教程知识库")

        results.append(f"[来源 {i}: {source}]\n{doc.page_content}")

    return "\n\n".join(results)

# 如需在文档中保留来源信息，可在创建时添加元数据

doc_with_meta = Document(

    page_content="Python3 基础教程共 30 章...",

    metadata={"source": "Python3 基础教程-课程介绍", "url": "https://www.runoob.com/python3/"}

)
```

## 向量存储的持久化

在实际项目中，你不会每次都重建向量索引。Chroma 支持持久化到本地：

## 实例
```
# 创建持久化向量存储（首次运行）

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

vector_store = Chroma.from_documents(

    documents=chunks,

    embedding=embeddings,

    persist_directory="./runoob_vector_db",  # 持久化目录

)

# 后续运行直接加载

loaded_store = Chroma(

    persist_directory="./runoob_vector_db",

    embedding_function=embeddings,

)

retriever = loaded_store.as_retriever()

# 无需重新计算向量！
```

> 向量存储的持久化可以大幅提升启动速度。在文档量大的情况下（成千上万篇），重新计算所有向量的 Embedding 可能花费数十分钟。持久化后只需加载即可。

其他扩展

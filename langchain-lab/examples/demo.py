"""示例：用 langchain-openai 调用 OpenAI 兼容云 API。

前置：
  1. 已复制 .env.example 为 .env，并填入 key（见 run.ps1 透传逻辑）
  2. 运行：.\run.ps1 examples\demo.py
"""

import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# .env 已由 run.ps1 透传为容器环境变量，此处再加一层保险（本目录 .env）
load_dotenv()

model = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "deepseek-chat"),
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE"),
)

resp = model.invoke("用一句话介绍 LangGraph 是什么。")
print(resp.content)
# LangChain 结构化输出

大多数时候，你需要的不是一段自由文本，而是结构化的数据——比如 JSON 对象。

LangChain 结构化输出(Structured Output) 让 Agent 按照你指定的格式返回结果，方便程序直接使用。

## 为什么需要结构化输出

假设你需要从一段用户描述中提取姓名、年龄和职业：

| 方式 | 输出格式 | 后续处理 |
| --- | --- | --- |
| 普通回复 | "张三今年28岁，是一名工程师" | 需要正则或再次调用模型来解析 |
| 结构化输出 | {name: "张三", age: 28, job: "工程师"} | 直接作为 Python 对象使用 |

结构化输出省去了"从文本中解析数据"这一步，让 AI 的输出可以直接被程序使用。

## 最简单的用法——传入 Pydantic 模型

将 Pydantic 模型传给 response_format 参数即可：

## 实例
```
from dotenv import load_dotenv
```

运行结果：

```
课程名: Python3 基础教程
难度: 入门
预计时长: 20 小时
免费: 是
对象类型: <class '__main__.CourseInfo'>
```

> 返回的 structured_response 是 Pydantic 模型实例，而不是普通字典。这意味着你可以使用 .course_name 等属性访问，IDE 也能提供自动补全。

## 与工具共存的 Structured Output

response_format 和 tools 可以同时使用——Agent 在需要时调用工具，最终输出结构化数据：

## 实例
```
from pydantic import BaseModel, Field

from langchain.agents import create_agent

from langchain.chat_models import init_chat_model

from langchain.messages import HumanMessage

from langchain.tools import tool

@tool

def search_course(keyword: str) -> str:

    """在菜鸟教程 RUNOOB 搜索课程信息"""

    courses = {

        "python": "Python3 基础教程 | 入门 | 免费 | 30章 | 约20小时",

        "java": "Java 基础教程 | 入门 | 免费 | 35章 | 约25小时",

        "数据分析": "Python 数据分析 | 进阶 | 会员 | 25章 | 约30小时",

    }

    return courses.get(keyword.lower(), f"未找到 '{keyword}' 相关课程")

class CourseRecommendation(BaseModel):

    """课程推荐结果"""

    course_name: str = Field(description="推荐课程名称")

    reason: str = Field(description="推荐理由")

    difficulty: str = Field(description="难度：入门/进阶/高级")

model = init_chat_model("deepseek:deepseek-v4-flash", temperature=0)

agent = create_agent(

    model=model,

    tools=[search_course],

    response_format=CourseRecommendation,

    system_prompt="你是菜鸟教程 RUNOOB 的课程顾问。先查询课程再给出推荐。",

)

result = agent.invoke({

    "messages": [HumanMessage(content="我想学 Python，有什么推荐？")]

})

rec = result["structured_response"]

print(f"推荐课程: {rec.course_name}")

print(f"推荐理由: {rec.reason}")

print(f"难度: {rec.difficulty}")

# 查看完整过程

print("\n=== 执行过程 ===")

for msg in result["messages"]:

    if msg.type == "tool":

        print(f"  调用 {msg.name}: {msg.content}")
```

运行结果：

```
推荐课程: Python3 基础教程
推荐理由: 该课程免费且适合Python初学者，学习时长约20小时
难度: 入门

=== 执行过程 ===
  调用 search_course: Python3 基础教程 | 入门 | 免费 | 30章 | 约20小时
```

## 复杂嵌套结构

Pydantic 支持嵌套、列表、枚举等复杂结构：

## 实例
```
from pydantic import BaseModel, Field

from typing import Literal

from langchain.agents import create_agent

from langchain.chat_models import init_chat_model

from langchain.messages import HumanMessage

class Topic(BaseModel):

    """知识点"""

    name: str = Field(description="知识点名称")

    order: int = Field(description="学习顺序，从 1 开始")

    minutes: int = Field(description="建议学习分钟数")

class LearningPlan(BaseModel):

    """学习计划"""

    goal: str = Field(description="学习目标概述")

    level: Literal["入门", "进阶", "高级"] = Field(description="难度级别")

    total_hours: float = Field(description="总时长（小时）")

    topics: list[Topic] = Field(description="知识点列表")

model = init_chat_model("deepseek:deepseek-v4-flash", temperature=0)

agent = create_agent(

    model=model,

    response_format=LearningPlan,

    system_prompt="你是菜鸟教程 RUNOOB 的学习规划师。",

)

result = agent.invoke({

    "messages": [HumanMessage(

        content="帮我制定一个 Python 入门学习计划，总时长控制在 10 小时以内"

    )]

})

plan = result["structured_response"]

print(f"目标: {plan.goal}")

print(f"难度: {plan.level}")

print(f"总时长: {plan.total_hours} 小时")

print(f"\n知识点列表 ({len(plan.topics)} 个):")

for topic in plan.topics:

    print(f"  {topic.order}. {topic.name} ({topic.minutes}分钟)")
```

运行结果：

```
目标: 掌握 Python 基础语法，能够独立编写简单的 Python 程序
难度: 入门
总时长: 9.5 小时

知识点列表 (6 个):
  1. 环境搭建与基础语法 (60分钟)
  2. 数据类型与变量 (90分钟)
  3. 条件判断与循环 (120分钟)
  4. 函数与模块 (120分钟)
  5. 列表与字典 (90分钟)
  6. 综合练习 (90分钟)
```

## 从消息中获取结构化输出

如果不需要 Agent 的工具调用能力，只是想从文本中提取结构化信息，可以直接用模型：

## 实例
```
from pydantic import BaseModel, Field

from langchain.chat_models import init_chat_model

class SentimentResult(BaseModel):

    """情感分析结果"""

    sentiment: str = Field(description="积极/消极/中性")

    score: float = Field(description="情感强度 0~1")

    keywords: list[str] = Field(description="关键情感词")

model = init_chat_model("deepseek:deepseek-v4-flash", temperature=0)

# 直接在模型上使用 with_structured_output()

# 不需要 Agent

structured_model = model.with_structured_output(SentimentResult)

texts = [

    "菜鸟教程 RUNOOB 真的太好用了，强烈推荐！",

    "这个教程内容太少了，不太值。",

    "今天天气不错。",

]

for text in texts:

    result = structured_model.invoke(text)

    print(f"文本: {text[:30]}...")

    print(f"  情感: {result.sentiment}, 强度: {result.score}, 关键词: {result.keywords}")
```

运行结果：

```
文本: 菜鸟教程 RUNOOB 真的太好用了，强烈推荐！...
  情感: 积极, 强度: 0.95, 关键词: ['好用', '推荐']
文本: 这个教程内容太少了，不太值。...
  情感: 消极, 强度: 0.7, 关键词: ['内容太少', '不太值']
文本: 今天天气不错。...
  情感: 中性, 强度: 0.1, 关键词: ['不错']
```

> with_structured_output() 是 model 的方法，不需要 Agent 就可以使用。如果你的场景是"信息提取"而非"多步骤推理"，直接用 with_structured_output() 更简洁高效。

其他扩展

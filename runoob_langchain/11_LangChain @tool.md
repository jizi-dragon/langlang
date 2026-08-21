# LangChain @tool 装饰器——定义工具

工具（Tool）是 Agent 与外部世界交互的桥梁。

通过 @tool 装饰器，你可以将任何 Python 函数快速转换为 Agent 可调用的工具。

## @tool 基本语法

@tool 是 LangChain 提供的装饰器，用法极其简单：在函数上加上 @tool 装饰器，函数就变成了一个工具。

## 实例
```
from langchain.tools import tool
```

运行结果：

```
你好，小明！欢迎来到菜鸟教程 RUNOOB。

工具名称: hello_tool
工具描述: 向指定的人打招呼。

    Args:
        name: 要打招呼的人的名字
```

> 函数的文档字符串（docstring）会自动成为工具的描述。Agent 依赖这个描述来判断"这个工具能做什么"和"什么情况下应该调用它"。文档字符串写得越清晰，Agent 使用工具就越准确。在描述中说明参数含义、函数功能和使用场景。

## 使用不同参数类型

@tool 支持多种参数类型，包括 int、float、bool 和枚举值：

## 实例
```
from langchain.tools import tool

from typing import Literal

@tool

def search_courses(

    keyword: str,

    level: Literal["入门", "进阶", "高级"],

    max_results: int = 5,

    free_only: bool = True,

) -> str:

    """在菜鸟教程 RUNOOB 中搜索课程。

    Args:

        keyword: 搜索关键词

        level: 课程难度级别

        max_results: 最多返回多少条结果

        free_only: 是否只显示免费课程

    """

    # 模拟搜索结果

    courses = {

        ("python", "入门"): "Python3 基础教程（免费）",

        ("python", "进阶"): "Python 数据分析实战（免费）",

        ("python", "高级"): "Python 机器学习进阶（会员）",

        ("html", "入门"): "HTML 基础教程（免费）",

    }

    key = (keyword.lower(), level)

    course = courses.get(key, f"未找到 {level} 级别的 {keyword} 课程")

    if free_only and "会员" in course:

        return f"搜索结果：{course} —— 该课程需要会员，已为你过滤"

    return f"搜索结果：{course}"

# 测试不同参数的调用

print(search_course.invoke({

    "keyword": "python",

    "level": "入门",

}))

# 输出：搜索结果：Python3 基础教程（免费）

print(search_course.invoke({

    "keyword": "python",

    "level": "高级",

    "free_only": False,

}))

# 输出：搜索结果：Python 机器学习进阶（会员）
```

## 注册工具到 Agent

将定义好的工具传给 create_agent() 的 tools 参数，Agent 就能使用它了：

## 实例
```
from dotenv import load_dotenv

load_dotenv()

from langchain.tools import tool

from langchain.agents import create_agent

from langchain.chat_models import init_chat_model

from langchain.messages import HumanMessage

@tool

def search_courses(keyword: str) -> str:

    """在菜鸟教程 RUNOOB 中搜索课程。传入关键词返回相关课程列表。

    Args:

        keyword: 搜索关键词，如 python、html、java

    """

    courses = {

        "python": "Python3 基础教程、Python 数据分析、Python 爬虫入门",

        "html": "HTML 基础教程、HTML5 新特性、HTML 表单实战",

        "java": "Java 基础教程、Java 面向对象、Java Spring 框架",

    }

    return courses.get(keyword.lower(), f"未找到与 {keyword} 相关的课程")

@tool

def get_course_detail(course_name: str) -> str:

    """获取指定课程的详细信息，包括章节数和学习时长。

    Args:

        course_name: 课程名称，如 "Python3 基础教程"

    """

    details = {

        "python3 基础教程": "共 30 章，预计学习时长 20 小时，适合零基础入门",

        "html 基础教程": "共 25 章，预计学习时长 15 小时，适合零基础入门",

    }

    return details.get(

        course_name.lower(),

        f"{course_name} 详情：适合初学者，内容丰富，附带实战案例"

    )

# 创建 Agent

model = init_chat_model("deepseek:deepseek-v4-flash", temperature=0)

agent = create_agent(

    model=model,

    tools=[search_courses, get_course_detail],

    system_prompt="你是菜鸟教程 RUNOOB 的学习顾问，帮助用户找到合适的课程。",

)

# 运行 Agent

def ask(question: str):

    result = agent.invoke({"messages": [HumanMessage(content=question)]})

    print(f"用户: {question}")

    print(f"顾问: {result['messages'][-1].content}")

    print("-" * 60)

ask("我想学 Python，有什么课程推荐？")

ask("Python3 基础教程学完需要多久？")
```

运行结果：

```
用户: 我想学 Python，有什么课程推荐？
顾问: 在菜鸟教程 RUNOOB 中有以下 Python 相关课程：
Python3 基础教程、Python 数据分析、Python 爬虫入门。
这些课程很适合 Python 初学者和进阶学习者，您可以根据兴趣选择！
------------------------------------------------------------
用户: Python3 基础教程学完需要多久？
顾问: Python3 基础教程共 30 章，预计学习时长 20 小时，非常适合零基础入门学习。
------------------------------------------------------------
```

## 多个工具协作

一个 Agent 可以注册多个工具，模型会自动判断何时使用哪个工具：

## 实例
```
from langchain.tools import tool

from langchain.agents import create_agent

from langchain.chat_models import init_chat_model

from langchain.messages import HumanMessage

@tool

def get_stock_price(symbol: str) -> str:

    """查询股票当前价格。

    Args:

        symbol: 股票代码，如 AAPL、GOOGL、TSLA

    """

    # 模拟股票数据

    prices = {"AAPL": 185.50, "GOOGL": 142.30, "TSLA": 245.80}

    price = prices.get(symbol.upper())

    if price is None:

        return f"未找到股票代码 {symbol}"

    return f"{symbol.upper()} 当前价格：${price}"

@tool

def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:

    """货币换算。

    Args:

        amount: 金额

        from_currency: 原货币代码，如 USD、CNY

        to_currency: 目标货币代码，如 CNY、USD

    """

    # 模拟汇率

    rates = {

        ("USD", "CNY"): 7.25,

        ("CNY", "USD"): 0.138,

    }

    rate = rates.get((from_currency.upper(), to_currency.upper()))

    if rate is None:

        return f"不支持 {from_currency} → {to_currency} 的换算"

    result = round(amount * rate, 2)

    return f"{amount} {from_currency} = {result} {to_currency}"

model = init_chat_model("deepseek:deepseek-v4-flash", temperature=0)

agent = create_agent(

    model=model,

    tools=[get_stock_price, convert_currency],

    system_prompt="你是一个金融助手，帮助用户查询股价和换算货币。",

)

# Agent 会自动决定调用哪个工具

result = agent.invoke({

    "messages": [HumanMessage(content="苹果股价是多少？换算成人民币是多少？")]

})

for msg in result["messages"]:

    if msg.type == "tool":

        print(f"[调用工具 {msg.name}] {msg.content}")

    elif msg.type == "ai" and msg.content:

        print(f"\n最终回答: {msg.content}")
```

运行结果：

```
[调用工具 get_stock_price] AAPL 当前价格：$185.5
[调用工具 convert_currency] 185.5 USD = 1344.88 CNY

最终回答: 苹果（AAPL）当前股价为 $185.50，按当前汇率换算约为 1344.88 人民币。
```

## 工具的可选参数与默认值

为工具参数设置默认值，可以让工具用起来更灵活：

## 实例
```
from langchain.tools import tool

@tool

def recommend_tutorial(

    language: str,

    level: str = "入门",

    count: int = 3,

) -> str:

    """根据编程语言和难度推荐菜鸟教程 RUNOOB 的课程。

    Args:

        language: 编程语言，如 Python、Java、HTML

        level: 难度级别，可选 "入门"、"进阶"、"高级"。默认 "入门"

        count: 推荐的课程数量，默认 3

    """

    tutorials = {

        "python": ["Python3 基础", "Python 面向对象", "Python 爬虫", "Python 数据分析"],

        "java": ["Java 基础", "Java 面向对象", "Java 集合框架", "Java 多线程"],

    }

    all_tutorials = tutorials.get(language.lower(), [f"{language} 基础教程"])

    selected = all_tutorials[:count]

    return f"推荐 {language} {level} 级别课程：{'、'.join(selected)}"

# 调用时只需要传必填参数

print(recommend_tutorial.invoke({"language": "Python"}))

# 输出：推荐 Python 入门 级别课程：Python3 基础、Python 面向对象、Python 爬虫

# 也可以覆盖默认参数

print(recommend_tutorial.invoke({

    "language": "Java",

    "level": "进阶",

    "count": 2,

}))

# 输出：推荐 Java 进阶 级别课程：Java 基础、Java 面向对象
```

> 默认值让 Agent 在调用工具时不用每次都指定所有参数。但注意：如果某个参数没有默认值且 Agent 没有提供，调用会失败。关键参数不要设默认值。

## 工具的 args_schema——自定义参数校验

对于复杂参数校验需求，可以使用 Pydantic 模型作为 args_schema：

## 实例
```
from pydantic import BaseModel, Field

from langchain.tools import tool

# 定义参数模型（提供更精细的参数控制）

class CourseSearchInput(BaseModel):

    """搜索课程参数"""

    keyword: str = Field(

        description="搜索关键词，支持模糊匹配",

        min_length=1,            # 最少 1 个字符

        max_length=50,           # 最多 50 个字符

    )

    category: str = Field(

        default="all",

        description="课程类别：all（全部）、frontend（前端）、backend（后端）、data（数据科学）",

        pattern=r"^(all|frontend|backend|data)$",  # 限定可选值

    )

    page: int = Field(

        default=1,

        description="页码，从 1 开始",

        ge=1,                    # 大于等于 1

        le=100,                  # 小于等于 100

    )

@tool(args_schema=CourseSearchInput)

def search_course(keyword: str, category: str = "all", page: int = 1) -> str:

    """在菜鸟教程 RUNOOB 中搜索课程"""

    return f"搜索 '{keyword}' (分类: {category}, 第 {page} 页)：共找到 15 条结果"

# 有效调用

print(search_course.invoke({"keyword": "Python", "category": "backend", "page": 1}))

# 无效调用（category 不在允许的值内）

try:

    search_course.invoke({"keyword": "Python", "category": "invalid"})

except Exception as e:

    print(f"参数校验失败: {e}")
```

运行结果：

```
搜索 'Python' (分类: backend, 第 1 页)：共找到 15 条结果
参数校验失败: ...
```

## 工具定义方式对比

| 方式 | 代码量 | 适用场景 | 示例 |
| --- | --- | --- | --- |
| @tool 装饰器 | 最少 | 简单到中等复杂度的工具 | 大多数场景 |
| @tool + args_schema | 中等 | 需要精细参数校验的工具 | API 封装、数据库操作 |
| Pydantic 类作为工具 | 较多 | 复杂业务逻辑的工具 | 内部包含状态的工具 |
| 字典格式 | 最少（但不推荐） | 描述远程/内置工具 | MCP 工具、服务端工具 |

其他扩展

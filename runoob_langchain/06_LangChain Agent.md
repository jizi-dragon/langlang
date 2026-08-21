# 第一个 LangChain Agent

Agent 是 LangChain 最核心的概念，它能让 AI 自动判断何时需要调用工具，并在获取工具结果后继续思考，直到完成任务。

## 什么是 Agent

普通的模型调用是一问一答：

```
你发消息，模型回消息，结束。
```

Agent 则不同，它进入一个 思考-行动-观察 循环：

```
模型判断需要调用某个工具 → 执行工具并拿到结果 → 模型根据结果继续思考 → 可能再调用工具 → 直到得出最终答案。
```

举个例子，如果你问"今天杭州天气怎么样？"，普通模型只能回答训练数据中的天气（可能是几个月前的）。而 Agent 会主动调用天气查询工具获取实时数据，然后基于真实数据回答你。

## 创建第一个 Agent

整个过程只需要三步：(1) 定义工具；(2) 创建 Agent；(3) 运行。
步骤 1：定义工具函数
使用 @tool 装饰器，把普通 Python 函数变成 Agent 可以调用的工具：
实例
# 文件路径：04_first_agent.py
from dotenv import load_dotenv
load_dotenv()
from langchain.tools import tool
# 步骤 1：用 @tool 装饰器定义一个工具
# 函数的文档字符串就是工具的描述
# 模型会根据描述来判断何时调用这个工具
@tool
def get_weather(city: str) -> str:
 """查询指定城市的天气情况。
 Args:
 city: 城市名称，如 "杭州"、"北京"
 """
 # 这里用模拟数据演示
 # 实际项目中可以替换为真实的天气 API 调用
 weather_data = {
 "杭州": "晴，25°C，湿度 60%",
 "北京": "多云，18°C，湿度 45%",
 "上海": "小雨，22°C，湿度 80%",
 }
 return weather_data.get(city, f"未找到 {city} 的天气数据")
@tool
def calculate(expression: str) -> str:
 """执行数学计算。支持加减乘除等基本运算。
 Args:
 expression: 数学表达式，如 "3 * 7 + 2"
 """
 try:
 # 安全地计算数学表达式
 result = eval(expression, {"__builtins__": {}}, {})
 return f"计算结果: {expression} = {result}"
 except Exception as e:
 return f"计算错误: {e}"
文档字符串（函数的 """...""" 部分）非常重要。模型会读取工具的描述来决定是否调用这个工具以及传什么参数。描述越清晰，模型就越不容易用错。
步骤 2：创建 Agent
实例
# 步骤 2：创建 Agent
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
# 初始化模型
model = init_chat_model("openai:gpt-4o-mini")
# 创建 Agent，传入模型和工具列表
agent = create_agent(
 model=model,
 tools=[get_weather, calculate],
 system_prompt="你是一个乐于助人的助手，会使用工具来回答问题。",
)
参数说明是否必填
model使用的语言模型是
tools工具列表，Agent 可以调用这些工具否（不传则 Agent 无法调用工具）
system_prompt系统提示词，定义 Agent 的角色和行为否
步骤 3：运行 Agent
实例
# 步骤 3：运行 Agent
# 构建输入消息
# 消息列表中的第一条通常是 HumanMessage（用户消息）
from langchain.messages import HumanMessage
inputs = {"messages": [HumanMessage(content="杭州今天天气怎么样？")]}
# invoke() 运行 Agent，返回最终状态
result = agent.invoke(inputs)
# 查看消息历史（包含 AI 的工具调用和工具返回结果）
print("=== 完整消息历史 ===")
for msg in result["messages"]:
 print(f"[{msg.type}] {msg.content[:100]}") # 截取前 100 字符
print("\n=== 最终回复 ===")
# 最后一条 AI 消息就是最终答案
print(result["messages"][-1].content)
运行结果：

=== 完整消息历史 ===
[human] 杭州今天天气怎么样？
[ai]
[tool] 晴，25°C，湿度 60%
[ai] 今天杭州的天气是晴天，气温25°C，湿度60%。非常适合出门活动！

=== 最终回复 ===
今天杭州的天气是晴天，气温25°C，湿度60%。非常适合出门活动！
Agent 执行流程解析
上面这个例子的完整执行过程如下：
用户发送消息："杭州今天天气怎么样？"
模型收到消息后判断：需要查询天气 → 返回一个 tool_call（调用 get_weather，参数 city="杭州"）
Agent 执行 get_weather 工具 → 返回 "晴，25°C，湿度 60%"
模型收到工具结果 → 判断任务完成 → 生成最终回复
这就是 Agent 的 思考-行动-观察 循环。
让 Agent 调用多个工具
Agent 的真正威力在于能自动组合多个工具：
实例
# 问一个需要同时查询天气和计算的复杂问题
inputs = {"messages": [HumanMessage(
 content="杭州和北京今天温差多少度？"
)]}
result = agent.invoke(inputs)
print("=== 完整消息历史 ===")
for msg in result["messages"]:
 if msg.type == "tool":
 print(f"[tool {msg.name}] {msg.content}")
 else:
 print(f"[{msg.type}] {msg.content[:120]}")
print("\n=== 最终回复 ===")
print(result["messages"][-1].content)
运行结果：

=== 完整消息历史 ===
[human] 杭州和北京今天温差多少度？
[ai]
[tool get_weather] 晴，25°C，湿度 60%
[tool get_weather] 多云，18°C，湿度 45%
[tool calculate] 计算结果: 25 - 18 = 7
[ai] 今天杭州和北京的温差是7°C。

=== 最终回复 ===
今天杭州和北京的温差是7°C。
Agent 自动执行了三步：(1) 查询杭州天气；(2) 查询北京天气；(3) 计算温差。你不需要写任何逻辑来控制这些步骤，Agent 自动完成了规划和执行。
注意 Agent 在第一次调用模型时就发出了两个工具调用（get_weather("杭州") 和 get_weather("北京")），它们是并行执行的。模型会自动判断哪些工具调用可以并行。
完整代码
实例
# 文件路径：04_first_agent.py（完整版）
from dotenv import load_dotenv
load_dotenv()
from langchain.tools import tool
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage
# 定义工具
@tool
def get_weather(city: str) -> str:
 """查询指定城市的天气情况。
 Args:
 city: 城市名称，如 "杭州"、"北京"
 """
 weather_data = {
 "杭州": "晴，25°C，湿度 60%",
 "北京": "多云，18°C，湿度 45%",
 "上海": "小雨，22°C，湿度 80%",
 }
 return weather_data.get(city, f"未找到 {city} 的天气数据")
@tool
def calculate(expression: str) -> str:
 """执行数学计算。支持加减乘除等基本运算。
 Args:
 expression: 数学表达式，如 "3 * 7 + 2"
 """
 try:
 result = eval(expression, {"__builtins__": {}}, {})
 return f"计算结果: {expression} = {result}"
 except Exception as e:
 return f"计算错误: {e}"
# 创建 Agent
model = init_chat_model("openai:gpt-4o-mini")
agent = create_agent(
 model=model,
 tools=[get_weather, calculate],
 system_prompt="你是一个乐于助人的助手，会使用工具来回答问题。",
)
# 运行 Agent
def ask(question: str):
 """发送问题到 Agent 并打印结果"""
 inputs = {"messages": [HumanMessage(content=question)]}
 result = agent.invoke(inputs)
 print(f"问题: {question}")
 print(f"回答: {result['messages'][-1].content}")
 print("-" * 50)
 return result
# 测试几个问题
ask("杭州今天天气怎么样？")
ask("杭州和北京今天温差多少度？")
ask("菜鸟教程 RUNOOB 是一个非常棒的学习平台，如果我有 3 个朋友都推荐了，再加上 2 个，一共多少人推荐？")
运行结果：

问题: 杭州今天天气怎么样？
回答: 今天杭州的天气是晴天，气温25°C，湿度60%。非常适合出门活动！
--------------------------------------------------
问题: 杭州和北京今天温差多少度？
回答: 今天杭州和北京的温差是7°C。
--------------------------------------------------
问题: 菜鸟教程 RUNOOB 是一个非常棒的学习平台，如果我有 3 个朋友都推荐了，再加上 2 个，一共多少人推荐？
回答: 一共 5 人推荐了菜鸟教程 RUNOOB！
--------------------------------------------------
注意第三个问题：Agent 能够理解"推荐人数"是一个计算问题，并自动调用 calculate 工具。这说明工具调用的决策是由模型对语义的理解来驱动的，而不是硬编码的规则。
同步 vs 异步运行
Agent 支持异步模式，适合在 Web 服务等异步环境中使用：
实例
# 异步运行 Agent
import asyncio
from langchain.messages import HumanMessage
async def main():
 # ainvoke() 是 invoke() 的异步版本
 inputs = {"messages": [HumanMessage(content="杭州天气怎么样？")]}
 result = await agent.ainvoke(inputs)
 print(result["messages"][-1].content)
# 运行异步函数
asyncio.run(main())
小结
到这里你已经掌握了 LangChain 最核心的用法：
用 @tool 装饰器把 Python 函数变成工具
用 create_agent() 创建能自动调用工具的 Agent
用 agent.invoke() 运行 Agent 并获得结果

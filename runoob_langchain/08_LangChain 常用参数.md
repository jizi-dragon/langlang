# LangChain Chat Model 常用参数

上一节我们学习了 init_chat_model() 的基本用法。

本节将详细介绍在调用模型时常用的控制参数，帮助你更好地控制模型的行为。

## temperature——控制创造性与确定性

temperature 是最常用的参数，取值范围 0 到 2。它控制模型输出的随机程度。

## 实例
```
from langchain.chat_models import init_chat_model
```

运行结果：

```
temperature=0 第1次: 菜鸟教程（RUNOOB）是一个为编程初学者提供免费教程的学习平台。
temperature=0 第2次: 菜鸟教程（RUNOOB）是一个为编程初学者提供免费教程的学习平台。
两次结果相同: True

temperature=1.5 第1次: 菜鸟教程（RUNOOB）是一个简单易懂的编程与网络技术入门学习平台。
temperature=1.5 第2次: RUNOOB（菜鸟教程）是深受编程新手喜爱的中文免费在线技术学习平台。
```

| temperature 值 | 效果 | 适用场景 |
| --- | --- | --- |
| 0 ~ 0.3 | 输出稳定、确定，每次结果几乎一致 | 数据提取、分类、代码生成、翻译 |
| 0.5 ~ 0.7 | 适度的创造性，输出自然但不偏离主题 | 日常对话、内容总结 |
| 0.8 ~ 1.2 | 输出多样化，有较多发挥空间 | 创意写作、头脑风暴 |
| 1.3 ~ 2.0 | 输出非常随机，可能出现意外内容 | 探索性生成（不太推荐用于生产） |

> temperature=0 不等于"完全相同"。由于模型内部计算的浮点精度差异，极端情况下仍可能有微小差异。如果需要绝对的确定性，有些模型提供了 seed 参数。

## max_tokens——控制输出长度与成本

max_tokens 限制模型输出的最大 Token 数。一个 Token 大约相当于 0.75 个英文单词或 0.5 个中文字。

## 实例
```
from langchain.chat_models import init_chat_model

model = init_chat_model("deepseek:deepseek-v4-flash", temperature=0)

# max_tokens=30：限制输出在 30 个 Token 以内

response_short = model.invoke(

    "详细介绍一下菜鸟教程 RUNOOB 平台",

    max_tokens=30

)

print(f"限制 30 tokens ({len(response_short.content)} 字符):")

print(response_short.content)

print()

# max_tokens=200：允许更长的输出

response_long = model.invoke(

    "详细介绍一下菜鸟教程 RUNOOB 平台",

    max_tokens=200

)

print(f"限制 200 tokens ({len(response_long.content)} 字符):")

print(response_long.content)
```

运行结果：

```
限制 30 tokens (42 字符):
菜鸟教程（RUNOOB）是一个面向编程初学者的在线学习平台，提供各种编程语言的教程和实例。

限制 200 tokens (306 字符):
菜鸟教程（RUNOOB）是一个面向编程初学者的在线学习平台，提供了丰富的编程教程和参考资料。
该平台涵盖了 HTML、CSS、JavaScript、Python、Java、C、C++、PHP、SQL 等多种编程语言和技术。
菜鸟教程的特点包括：
1. 内容系统化：从基础到进阶，帮助学习者逐步掌握编程知识
2. 实例丰富：每个知识点都配有可运行的代码示例
3. ...
```

> max_tokens 是对输出长度的硬限制。如果设置过低，模型的回答可能在句中突然截断。一般建议根据场景设置在 100-2000 之间。对于"一句话回答"类场景，30-100 就够了；对于"详细解释"类场景，建议 500-2000。

## timeout 与 max_retries——网络可靠性

在生产环境中，网络请求可能因为各种原因失败。这两个参数帮助你控制请求行为。

## 实例
```
from langchain.chat_models import init_chat_model

# 生产环境推荐配置

model = init_chat_model(

    "deepseek:deepseek-v4-flash",

    # 单次请求最多等待 30 秒

    timeout=30,

    # 失败后最多重试 3 次（总共 4 次请求机会）

    max_retries=3,

)

# 模拟正常调用

try:

    response = model.invoke("菜鸟教程 RUNOOB 是什么？")

    print(f"调用成功: {response.content[:50]}...")

except Exception as e:

    print(f"调用失败: {e}")
```

| 参数 | 说明 | 建议值 |
| --- | --- | --- |
| timeout | 单次请求的最大等待时间（秒）。None 表示不限制 | 30~60（太短容易超时，太长用户体验差） |
| max_retries | 失败后的重试次数。0 表示不重试 | 2~3（足够处理偶发网络问题） |

设置 timeout 和 max_retries 的费时分析：

```
假设 timeout=30, max_retries=3：
单次成功: ~2s
第1次失败+重试成功: ~2s + ~2s = ~4s
全部失败: 4次 × 30s = 最多 120s 才抛出异常
```

## base_url——自定义 API 地址

base_url 参数在你需要通过代理、中转服务或私有部署访问模型时非常有用。

## 实例
```
from langchain.chat_models import init_chat_model

# 场景 1：通过代理访问 OpenAI

model = init_chat_model(

    "deepseek:deepseek-v4-flash",

    base_url="https://your-proxy-domain.com/v1",  # 代理地址

)

# 场景 2：使用兼容 OpenAI 接口的第三方服务

# 很多国产模型提供了 OpenAI 兼容接口

model = init_chat_model(

    "deepseek:deepseek-v4-flash",           # provider 写 openai

    base_url="https://api.third-party.com/v1",  # 但实际指向第三方

    api_key="your-third-party-key",  # 第三方 API Key

)

# 场景 3：连接本地模型（如 vLLM、Ollama）

model = init_chat_model(

    "openai:qwen2.5",               # 本地模型名

    base_url="http://localhost:8000/v1",  # 本地服务地址

    api_key="not-needed",           # 本地通常不需要 Key

)
```

> base_url 改变的是 API 端点的地址，但 provider 参数决定了行为模式。比如 provider="openai" 会使用 OpenAI 的消息格式，即使 base_url 指向的是别的服务。确保目标服务兼容你指定的 provider 格式。

## 其他常用参数

### top_p——核采样

## 实例
```
from langchain.chat_models import init_chat_model

# top_p 是另一种控制随机性的方式

# 模型只会从累积概率达到 top_p 的词中采样

# top_p=0.1 表示只从最高概率的 10% 的词中选择

model = init_chat_model(

    "deepseek:deepseek-v4-flash",

    top_p=0.9,       # 只考虑累积概率前 90% 的词

)

response = model.invoke("介绍菜鸟教程 RUNOOB")

print(response.content[:100])
```

> 一般建议只调整 temperature 或 top_p 中的一个，不要同时调节。如果同时设置，模型的行为可能难以预测。

### stop——停止序列

## 实例
```
from langchain.chat_models import init_chat_model

model = init_chat_model("deepseek:deepseek-v4-flash")

# stop 参数指定停止序列，模型遇到这些词时会立即停止生成

response = model.invoke(

    "列出五个编程学习网站，每个一行",

    stop=["\n"]  # 遇到换行就停止，只返回第一个

)

print(f"限制 stop=['\\n']: {response.content}")
```

运行结果：

```
限制 stop=['\n']: 1. 菜鸟教程（RUNOOB）
```

### seed——可重复性（部分模型支持）

## 实例
```
from langchain.chat_models import init_chat_model

# 某些模型支持 seed 参数，用于获得确定性的输出

# 相同的 seed + 相同的输入 = 相同的输出

model = init_chat_model("deepseek:deepseek-v4-flash", seed=42, temperature=0)

resp1 = model.invoke("介绍菜鸟教程")

resp2 = model.invoke("介绍菜鸟教程")

print(f"seed=42, 结果相同: {resp1.content == resp2.content}")
```

## 参数速查表

| 参数 | 类型 | 默认值 | 何时使用 |
| --- | --- | --- | --- |
| temperature | float | 因模型而异 | 任务需要稳定性时设为 0~0.3，需要创造性时设为 0.7~1.0 |
| max_tokens | int | 模型上限 | 输出长度需要控制时 |
| timeout | int/float | None | 生产环境建议始终设置 |
| max_retries | int | 因模型而异 | 网络不稳定时建议 2~3 |
| base_url | str | 官方地址 | 使用代理、中转或本地服务时 |
| top_p | float | 1.0 | 需要核采样控制时（替代 temperature） |
| stop | list[str] | 无 | 需要精确控制输出结尾时 |

其他扩展

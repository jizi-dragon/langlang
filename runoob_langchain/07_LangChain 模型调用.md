# LangChain 模型调用 -- init_chat_model() 函数

LangChain init_chat_model() 是 LangChain 中最常用的函数之一，它让你用统一的方式连接 20 多种模型提供商，不需要记忆每个提供商的类名和参数差异。

### 语法

init_chat_model() 函数语法如下：

```
from langchain.chat_models import init_chat_model

# 完整语法
model = init_chat_model(
    model,                    # str | None：模型名称（provider:model 格式）
    *,
    model_provider=None,      # str | None：单独的模型提供商
    configurable_fields=None, # None | "any" | list[str]：可运行时修改的字段
    config_prefix=None,       # str | None：配置键前缀
    **kwargs,                 # 模型特定参数（temperature、max_tokens 等）
)
```

参数说明：

| 参数 | 类型 | 说明 | 默认值 |
| --- | --- | --- | --- |
| model | str 或 None | 模型名，provider:model 格式。传 None 时可用于创建可配置模型 | 无 |
| model_provider | str 或 None | 单独指定提供商。动态获取或 model 无法推断时使用 | None |
| configurable_fields | "any" 或 list 或 None | 可运行时修改的字段列表。None 表示固定模型 | None |
| config_prefix | str 或 None | 多模型场景下配置键的前缀，避免冲突 | None |
| **kwargs | dict | 传递给底层模型的参数 | 无 |

### model 参数详解

#### provider:model 格式（推荐）

格式为 提供商:模型名，用冒号分隔：

## 实例
```
from langchain.chat_models import init_chat_model
```

#### 自动推断模型提供商

如果不指定提供商前缀，LangChain 会尝试从模型名推断：

## 实例
```
from langchain.chat_models import init_chat_model

# 自动推断提供商（基于模型名前缀）

model = init_chat_model("deepseek-v4-flash")       # → openai

model = init_chat_model("claude-sonnet-4-5") # → anthropic

model = init_chat_model("deepseek-chat")     # → deepseek

model = init_chat_model("grok-3")            # → xai

model = init_chat_model("mistral-large")     # → mistralai
```

| 模型名前缀 | 推断提供商 |
| --- | --- |
| gpt-、o1、o3、chatgpt、text-davinci | openai |
| claude | anthropic |
| gemini | google_vertexai |
| command | cohere |
| deepseek | deepseek |
| mistral、mixtral | mistralai |
| grok | xai |
| sonar | perplexity |
| amazon.、anthropic.、meta. | bedrock |

> 自动推断虽然方便，但不保证 100% 正确。例如 gemini 前缀可能指向 google_vertexai 或 google_genai，未来版本可能改变默认推断结果。生产环境建议始终使用 provider:model 格式。

### model_provider 参数

当 model_provider 单独指定时，效果等价于 provider:model 格式：

## 实例
```
# 下面两种写法完全等价

model = init_chat_model("claude-sonnet-4-5", model_provider="anthropic")

model = init_chat_model("anthropic:claude-sonnet-4-5")
```

使用 model_provider 的场景：

- 从配置文件动态读取提供商名称时
- 提供商名称和模型名需要独立配置时（运行时分别切换）
- 模型名无法被自动推断且不方便拼接字符串时

## 固定模型 vs 可配置模型

init_chat_model() 有两种使用模式：

### 模式 1：固定模型

指定具体的 model 字符串，返回可直接使用的 BaseChatModel 实例：

## 实例
```
from langchain.chat_models import init_chat_model

# 指定了 model，返回固定模型

model = init_chat_model("deepseek:deepseek-v4-flash", temperature=0.7)

response = model.invoke("介绍菜鸟教程 RUNOOB")

print(response.content)
```

> 如果 .env 是在当前目录下，使用以下代码，载入当前路径的配置：
> ```
> import os
> 
> from dotenv import load_dotenv
> 
> # 加载当前目录 .env 文件
> load_dotenv()
> from langchain.chat_models import init_chat_model
> 
> # 指定了 model，返回固定模型
> model = init_chat_model("deepseek:deepseek-v4-flash", temperature=0.7)
> response = model.invoke("介绍菜鸟教程 RUNOOB")
> print(response.content)
> ```

### 模式 2：可配置模型

不指定 model（或设为 None），创建可在运行时动态切换的模型：

## 实例
```
from langchain.chat_models import init_chat_model

# 不指定 model，返回可配置模型

# 可以固定一些参数（如 temperature=0.7），其余运行时指定

configurable_model = init_chat_model(temperature=0.7)

# 运行时通过 config 指定模型

response = configurable_model.invoke(

    "介绍菜鸟教程 RUNOOB",

    config={"configurable": {"model": "deepseek-v4-flash"}}

)

print(response.content)

# 同一个模型实例，可以用不同的模型来执行

response = configurable_model.invoke(

    "介绍菜鸟教程 RUNOOB",

    config={"configurable": {"model": "claude-sonnet-4-5"}}

)

print(response.content)
```

> 可配置模型在 A/B 测试和成本优化中非常有用。你可以在不重启服务的情况下，通过修改配置来切换模型或调整参数。

## 所有支持的模型提供商

以下是 init_chat_model() 内置支持的提供商及其安装包：

| provider 名称 | 安装包 | 代表模型 |
| --- | --- | --- |
| openai | langchain-deepseek | gpt-4o、gpt-4o-mini |
| anthropic | langchain-anthropic | claude-sonnet-4-5、claude-opus-4-7 |
| google_genai | langchain-google-genai | gemini-2.5-flash、gemini-2.5-pro |
| google_vertexai | langchain-google-vertexai | gemini-2.5-flash、gemini-2.5-pro |
| deepseek | langchain-deepseek | deepseek-chat、deepseek-reasoner |
| mistralai | langchain-mistralai | mistral-large、mistral-small |
| groq | langchain-groq | llama-3.3-70b、mixtral-8x7b |
| ollama | langchain-ollama | llama3.2、qwen2.5 |
| fireworks | langchain-fireworks | accounts/fireworks/models/llama-v3p1-70b |
| together | langchain-together | meta-llama/Llama-3.3-70B |
| xai | langchain-xai | grok-3 |
| openrouter | langchain-openrouter | openai/gpt-4o、anthropic/claude-sonnet |
| perplexity | langchain-perplexity | sonar、sonar-pro |
| huggingface | langchain-huggingface | 各类 HuggingFace 模型 |
| cohere | langchain-cohere | command-r-plus |

## 常用 kwargs 参数

kwargs 参数会直接传递给底层模型类，常用的包括：

## 实例
```
from langchain.chat_models import init_chat_model

model = init_chat_model(

    "deepseek:deepseek-v4-flash",

    # 控制输出随机性（0~2），值越小输出越稳定

    temperature=0.3,

    # 限制输出最大 token 数（控制成本）

    max_tokens=200,

    # 请求超时时间（秒）

    timeout=30,

    # 失败重试次数

    max_retries=2,

    # 自定义 API 地址（代理/中转场景）

    # base_url="https://your-proxy.com/v1",

    # 速率限制器（控制请求频率）

    # rate_limiter=MyRateLimiter(requests_per_second=5),

)

response = model.invoke("菜鸟教程 RUNOOB 是什么？")

print(response.content)
```

| 参数 | 类型 | 说明 | 适用提供商 |
| --- | --- | --- | --- |
| temperature | float | 控制随机性，0~2，默认值因模型而异 | 大部分 |
| max_tokens | int | 限制输出最大 Token 数 | 全部 |
| timeout | int 或 float | 请求超时秒数 | 全部 |
| max_retries | int | 请求失败后的重试次数 | 大部分 |
| base_url | str | 自定义 API 端点 | 大部分 |
| rate_limiter | BaseRateLimiter | 速率限制器实例 | 大部分 |
| top_p | float | 核采样参数，0~1 | 大部分 |
| stop | list[str] | 停止序列，模型遇到这些词时停止生成 | 大部分 |

> temperature 和 top_p 通常不同时设置。temperature 控制的是"分布的形状"，top_p 控制的是"候选范围"。对于大多数场景，只调整 temperature 就足够了。

## ConfigurableModel——运行时切换模型

ConfigurableModel 是 init_chat_model() 的高级用法，允许在运行时动态指定模型和参数：

## 实例
```
from langchain.chat_models import init_chat_model

# 创建可配置模型，并设置默认值

model = init_chat_model(

    "deepseek:deepseek-v4-flash",       # 默认模型

    configurable_fields="any",  # 所有参数都可在运行时修改

    config_prefix="my",         # 配置键前缀

    temperature=0.3,            # 默认温度

)

# 使用默认配置运行

response = model.invoke("介绍菜鸟教程")

print(f"默认配置: {response.content[:50]}...")

# 运行时覆盖模型和参数（注意 my_ 前缀）

response = model.invoke(

    "介绍菜鸟教程 RUNOOB",

    config={

        "configurable": {

            "my_model": "deepseek:deepseek-v4-pro",       # 切换模型

            "my_temperature": 0.9,             # 调整温度

        }

    }

)

print(f"覆盖配置: {response.content[:50]}...")
```

configurable_fields 的取值：

| 值 | 含义 |
| --- | --- |
| None | 不可配置，返回普通的 BaseChatModel（固定模型模式） |
| "any" | 所有参数可配置（注意安全：api_key 等也能被修改） |
| ["model", "temperature"] | 只有列表中指定的字段可配置 |

> 使用 configurable_fields="any" 时要注意安全：如果信任了不安全的配置来源，api_key 和 base_url 等敏感字段可能被篡改。生产环境建议显式列出可配置的字段。

其他扩展

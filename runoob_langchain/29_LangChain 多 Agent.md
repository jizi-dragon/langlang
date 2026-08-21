# LangChain 多 Agent

当一个任务太复杂，单个 Agent 难以胜任时，你可以创建多个各司其职的 Agent，让它们像团队一样协作。

## 为什么需要多 Agent

单个 Agent 的问题：

- system_prompt 太长会导致模型注意力分散
- 工具太多会增加模型选择工具的出错概率
- 不同类型的任务需要不同的专业知识和行为风格

多 Agent 的方案：每个 Agent 专注于一个领域，通过协作完成复杂任务。

## 方式 1：子 Agent 作为工具

将 Agent 编译成 CompiledStateGraph，然后作为一个工具注册给父 Agent：

## 实例
```
from dotenv import load_dotenv
```

运行结果：

```
根据天气专家的查询，杭州今天晴天，气温25°C。
换算成华氏度：25 × 9/5 + 32 = 77°F。
所以杭州今天25°C，相当于77°F，天气晴好。
```

## 方式 2：用 name 参数区分 Agent

当你将子 Agent 作为工具嵌入时，设置 name 参数有助于追踪消息来源：

## 实例
```
# name 参数的作用：

# 1. 编译后的图中使用该名称

# 2. 作为子图节点嵌入父图时使用该名称

# 3. 所有 AI 消息被标记为该名称

agent = create_agent(

    model=model,

    tools=[...],

    name="customer_service",  # 给 Agent 命名

)
```

## 方式 3：Middleware 实现 Agent 路由

更复杂的多 Agent 场景可以通过 Middleware 实现动态路由：

## 实例
```
from langchain.agents.middleware import before_model

# 定义不同专家使用的工具集

general_tools = [tool_a, tool_b]

admin_tools = [tool_c, tool_d]

@before_model

def route_by_user_role(state, runtime):

    """根据用户角色动态切换可用工具"""

    context = runtime.context

    if context is None:

        return None

    user_role = context.get("user_role", "user")

    # 不同角色看到不同的工具

    if user_role == "admin":

        available_tools = general_tools + admin_tools

    else:

        available_tools = general_tools

    # 注意：before_model 不能直接修改 tools，

    # 需要配合 wrap_model_call 或 request.override 来实现

    return None
```

## 多 Agent 架构模式

| 模式 | 结构 | 适用场景 |
| --- | --- | --- |
| 协调者模式 | 一个父 Agent → 多个子 Agent 工具 | 任务类型明确可分类 |
| 接力模式 | Agent A 的输出 → Agent B 的输入 | 流水线式处理（生成→审核→润色） |
| 辩论模式 | 多个 Agent 并行输出 → 汇总决策 | 需要多角度分析的问题 |

> 多 Agent 系统增加了复杂度和 Token 消耗。不要为了"多 Agent"而多 Agent——先用单个 Agent + 良好设计的 system_prompt 和 Middleware 解决问题。只有当确实需要领域隔离或独立上下文时，才引入多 Agent。

其他扩展

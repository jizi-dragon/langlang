"""test_06 · 03 结构化输出：直接用 model.with_structured_output() 提取，不套 Agent。

回应用户的疑问——"结构化输出还能直接用 model 获取，这块讲讲"：
核心判断就一句——**只要不需要工具/多步推理，就别上 Agent**。
`model.with_structured_output(Schema)` 是一次调用同时"提取 + 校验成 Pydantic 对象"，
比让 Agent 跑一圈更快、更省、更可控。

场景对照：
- 信息提取（本脚本）：客户反馈 → 工单字段。无工具、单次 → 直接 with_structured_output。
- 多步推理（上一章）：查会员→算折扣→汇总。需要工具循环 → 才用 create_agent(response_format)。

工程注意：DeepSeek 不支持原生 json_schema 结构化（test_05 已踩过坑），
with_structured_output 默认走 function_calling 的 ToolStrategy，天然适配 deepseek。
"""

from langchain.chat_models import init_chat_model
from langchain.pydantic_v1 import BaseModel, Field


class CustomerTicket(BaseModel):
    """从客户原声里提取的工单字段（程序可直接消费，无需解析文本）。"""
    issue: str = Field(description="客户反馈的核心问题一句话总结")
    category: str = Field(description="工单类别：退货/咨询/投诉/技术故障")
    urgency: str = Field(description="紧急度：低/中/高")
    sentiment: str = Field(description="情绪倾向：积极/中性/消极")
    keywords: list[str] = Field(description="关键事实词")


def build_extractor():
    model = init_chat_model(
        "deepseek:deepseek-v4-flash",
        temperature=0,
        extra_body={"thinking": {"type": "disabled"}},
    )
    # 单次调用即返回 CustomerTicket 实例
    return model.with_structured_output(CustomerTicket)


if __name__ == "__main__":
    extractor = build_extractor()

    # 模拟三条真实客户原声（无工具、单轮提取）
    feedback_list = [
        "我在你们平台买了双鞋，穿了两天就开胶了，客服一直不回复，我要投诉！",
        "请问我昨天下的订单今天能发货吗？大概什么时候到？",
        "教程内容很好，但希望能加一个搜索功能，方便我快速找到想看的章节。",
    ]

    for text in feedback_list:
        ticket = extractor.invoke(text)  # 直接得到 Pydantic 对象，可通过 .字段 访问
        print(f"原声: {text[:18]}…")
        print(f"  工单: [{ticket.category}/紧急{ticket.urgency}/情绪{ticket.sentiment}]")
        print(f"  问题: {ticket.issue}")
        print(f"  关键词: {ticket.keywords}\n")
        # 业务侧可直接把 ticket 写入工单系统 / 质检库，无需再 parse 文本
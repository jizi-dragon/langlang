"""test_02：Chat Model 的 with_structured_output 结构化输出。

用 Pydantic 定义嵌套 Schema（菜谱 → 食材 / 步骤），强制模型按结构输出，
避免自由文本解析常见的字段缺失、类型错误、JSON 非法问题。
with_structured_output 是"强制"结构化，模型无法选择不按结构返回。

运行（在 langchain-lab 目录下）：
    .\\dev.ps1 examples/test_02/structured_output.py
"""

from dotenv import load_dotenv

from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field

load_dotenv()


class Ingredient(BaseModel):
    """食材信息"""
    name: str = Field(description="食材名称")
    amount: str = Field(description="用量，如 '200g'、'2个'")


class CookingStep(BaseModel):
    """烹饪步骤"""
    step_number: int = Field(description="步骤编号")
    description: str = Field(description="步骤描述")
    duration_minutes: int = Field(description="此步骤需要的时间（分钟）")


class Recipe(BaseModel):
    """菜谱"""
    dish_name: str = Field(description="菜名")
    difficulty: str = Field(description="难度：简单、中等、困难")
    ingredients: list[Ingredient] = Field(description="食材列表")
    steps: list[CookingStep] = Field(description="烹饪步骤")


def main():
    # DeepSeek 思考模式不接受 tool_choice，而 with_structured_output 默认
    # 以 function_calling 强制 tool_choice=required，会报 400，故关闭思考。
    # 同时思考模式下 temperature 不生效，关闭后 temperature=0 才真正起作用。
    model = init_chat_model(
        "deepseek:deepseek-v4-flash",
        temperature=0,
        extra_body={"thinking": {"type": "disabled"}},
    )
    structured_model = model.with_structured_output(Recipe)

    recipe_text = """
今天来教大家做一道经典的番茄炒蛋，这道菜非常简单。
需要准备：番茄 2 个、鸡蛋 3 个、葱花少许、盐适量、糖少许。
步骤：
1. 先把番茄切块，鸡蛋打散，大概需要 5 分钟
2. 热锅放油，先把鸡蛋炒熟盛出，大概 3 分钟
3. 锅中再放油，炒番茄至出汁，加盐和糖，大概 5 分钟
4. 倒入炒好的鸡蛋，翻炒均匀，撒上葱花，大概 2 分钟
"""

    result = structured_model.invoke(recipe_text)

    print(f"菜名: {result.dish_name}")
    print(f"难度: {result.difficulty}")
    print(f"食材 ({len(result.ingredients)} 种):")
    for ing in result.ingredients:
        print(f"  - {ing.name}: {ing.amount}")
    print(f"步骤 ({len(result.steps)} 步):")
    for step in result.steps:
        print(f"  {step.step_number}. {step.description} ({step.duration_minutes}分钟)")


if __name__ == "__main__":
    main()

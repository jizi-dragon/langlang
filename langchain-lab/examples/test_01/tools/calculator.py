"""安全数学计算工具。

用 AST 白名单实现表达式求值，替代不安全的内置 eval()：
eval 可被注入任意 Python 代码，这里只允许数字与四则运算通过。
"""

import ast
import operator

# 支持的四则运算操作符
_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_UNARYS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

# 允许出现在表达式中的节点类型（白名单，其余节点一律拒绝）
_ALLOWED_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Constant,
    ast.USub,
    ast.UAdd,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.Pow,
)


def _evaluate(node: ast.AST):
    """递归求值，仅接受白名单内的节点类型。"""
    if not isinstance(node, _ALLOWED_NODES):
        raise ValueError(f"表达式中包含不支持的语法：{type(node).__name__}")

    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp):
        op = _BINOPS[type(node.op)]
        return op(_evaluate(node.left), _evaluate(node.right))
    if isinstance(node, ast.UnaryOp):
        op = _UNARYS[type(node.op)]
        return op(_evaluate(node.operand))
    raise ValueError("表达式结构不正确")


def calculate(expression: str) -> str:
    """计算一个数学表达式，如 "3 * 7 + 2"。

    参数：
        expression: 数学表达式，仅支持数字与四则运算
    返回：
        形如 "计算结果: 3 * 7 + 2 = 23" 的字符串
    """
    try:
        tree = ast.parse(expression, mode="eval")
        result = _evaluate(tree.body)
        return f"计算结果: {expression} = {result}"
    except (SyntaxError, ValueError, ZeroDivisionError) as exc:
        return f"计算错误: {exc}"
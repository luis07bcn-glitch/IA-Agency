import ast
import operator

_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
}


def _eval(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Tipo no permitido: {type(node.value).__name__}")
    if isinstance(node, ast.BinOp):
        return _SAFE_OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp):
        return _SAFE_OPS[type(node.op)](_eval(node.operand))
    raise ValueError(f"Operación no permitida: {type(node).__name__}")


def calculate(expression: str) -> dict:
    try:
        tree = ast.parse(expression, mode="eval")
        result = _eval(tree.body)
        return {"expression": expression, "result": result}
    except Exception as e:
        return {"expression": expression, "error": str(e)}

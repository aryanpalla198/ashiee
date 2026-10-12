"""
Calculator Mathematical Core Engine
"""
import ast
import operator as op

OPERATORS = {
    ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
    ast.Div: op.truediv, ast.Pow: op.pow, ast.USub: op.neg, ast.Mod: op.mod
}

def evaluate_expression(expr: str) -> float:
    """Safely evaluates mathematical expressions using Python AST parser."""
    def _eval(node):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            return OPERATORS[type(node.op)](_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp):
            return OPERATORS[type(node.op)](_eval(node.operand))
        raise TypeError(f"Unsupported syntax: {type(node)}")
    return _eval(ast.parse(expr, mode='eval').body)

if __name__ == "__main__":
    print("Testing calculator engine: 12 + 4 * (10 - 2) =", evaluate_expression("12 + 4 * (10 - 2)"))

import ast
import math
import re
from typing import Any

SAFE_FUNCTIONS = {
    "sqrt": math.sqrt,
    "cbrt": lambda x: math.pow(x, 1 / 3) if x >= 0 else -math.pow(-x, 1 / 3),
    "abs": abs,
    "round": round,
    "pow": math.pow,
    "log": math.log,
    "log10": math.log10,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "floor": math.floor,
    "ceil": math.ceil,
}

SAFE_CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
}


class SafeEvaluator(ast.NodeVisitor):
    def visit(self, node: ast.AST) -> Any:
        method = "visit_" + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ast.AST) -> Any:
        raise ValueError(f"Unsupported operation or syntax: {node.__class__.__name__}")

    def visit_Expression(self, node: ast.Expression) -> Any:
        return self.visit(node.body)

    def visit_Constant(self, node: ast.Constant) -> Any:
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported literal value: {node.value}")

    def visit_Name(self, node: ast.Name) -> Any:
        if node.id in SAFE_CONSTANTS:
            return SAFE_CONSTANTS[node.id]
        if node.id in SAFE_FUNCTIONS:
            return SAFE_FUNCTIONS[node.id]
        raise ValueError(f"Unknown variable or identifier: {node.id}")

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.UAdd):
            return +operand
        if isinstance(node.op, ast.USub):
            return -operand
        raise ValueError(f"Unsupported unary operator: {node.op.__class__.__name__}")

    def visit_BinOp(self, node: ast.BinOp) -> Any:
        left = self.visit(node.left)
        right = self.visit(node.right)

        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            if right == 0:
                raise ValueError("Division by zero")
            return left / right
        if isinstance(node.op, ast.FloorDiv):
            if right == 0:
                raise ValueError("Division by zero")
            return left // right
        if isinstance(node.op, ast.Mod):
            if right == 0:
                raise ValueError("Modulo by zero")
            return left % right
        if isinstance(node.op, ast.Pow):
            if abs(right) > 1000:
                raise ValueError("Exponent too large")
            try:
                return left ** right
            except OverflowError:
                raise ValueError("Calculation resulted in numerical overflow")

        raise ValueError(f"Unsupported binary operator: {node.op.__class__.__name__}")

    def visit_Call(self, node: ast.Call) -> Any:
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only standard mathematical function calls are supported")

        func_name = node.func.id
        if func_name not in SAFE_FUNCTIONS:
            raise ValueError(f"Function '{func_name}' is not allowed")

        func = SAFE_FUNCTIONS[func_name]
        args = [self.visit(arg) for arg in node.args]

        if func_name in ("sqrt", "log", "log10") and args and args[0] < 0:
            raise ValueError(f"Cannot calculate {func_name} of a negative number")

        return func(*args)


def sanitize_math_expression(raw_expr: str) -> str:
    cleaned = raw_expr.strip()

    # Strip currency symbols and commas inside numbers
    cleaned = re.sub(r"[₹$€£¥]", "", cleaned)
    cleaned = re.sub(r"(?<=\d),(?=\d)", "", cleaned)

    # Replace common symbols
    cleaned = cleaned.replace("×", "*").replace("÷", "/")
    cleaned = cleaned.replace("^", "**")

    # Replace "X% of Y" with "(X / 100) * Y"
    cleaned = re.sub(
        r"(\d+(?:\.\d+)?)\s*%\s*of\s*",
        r"(\1 / 100) * ",
        cleaned,
        flags=re.IGNORECASE,
    )

    # Replace isolated percentages like "15%" with "(15 / 100)"
    cleaned = re.sub(r"(\d+(?:\.\d+)?)\s*%", r"(\1 / 100)", cleaned)

    return cleaned


def calculate(expression: str) -> dict[str, Any]:
    if not expression or not expression.strip():
        return {
            "success": False,
            "error": "Expression cannot be empty",
            "result": None,
        }

    try:
        sanitized = sanitize_math_expression(expression)
        parsed = ast.parse(sanitized, mode="eval")
        evaluator = SafeEvaluator()
        val = evaluator.visit(parsed)

        # Simplify integer float representation
        if isinstance(val, float) and val.is_integer():
            formatted = int(val)
        elif isinstance(val, float):
            formatted = round(val, 8)
        else:
            formatted = val

        return {
            "success": True,
            "expression": expression,
            "sanitized_expression": sanitized,
            "result": formatted,
            "error": None,
        }
    except SyntaxError:
        return {
            "success": False,
            "expression": expression,
            "error": f"Invalid mathematical syntax in expression: '{expression}'",
            "result": None,
        }
    except Exception as exc:
        return {
            "success": False,
            "expression": expression,
            "error": str(exc),
            "result": None,
        }

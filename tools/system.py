import ast
import datetime as dt
import operator
import re
from zoneinfo import ZoneInfo
OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.Mod: operator.mod, ast.Pow: operator.pow}
UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}
def _eval(node):
    if isinstance(node, ast.Expression): return _eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)): return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in OPS: return OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in UNARY: return UNARY[type(node.op)](_eval(node.operand))
    raise ValueError("unsafe expression")
def calculate(text: str):
    expr = text.lower()
    for prefix in ("calculate", "solve", "what is"):
        expr = expr.replace(prefix, "")
    expr = expr.replace("multiplied by", "*").replace("divided by", "/").replace("plus", "+").replace("minus", "-").replace("times", "*").strip()
    if not re.fullmatch(r"[0-9\s+\-*/().%]+", expr) or not any(c.isdigit() for c in expr): return None
    try: return f"The answer is {_eval(ast.parse(expr, mode='eval'))}."
    except Exception: return None
def local_answer(text: str):
    q = text.lower()
    now = dt.datetime.now(ZoneInfo("Asia/Kolkata"))
    if re.search(r"\b(time now|current time|what time|tell me the time|samayam|ippudu time)\b", q): return f"The current time in India is {now.strftime('%I:%M %p')}."
    if re.search(r"\b(today's date|current date|what is the date|today date|ee roju date)\b", q): return f"Today is {now.strftime('%A, %d %B %Y')}."
    return None

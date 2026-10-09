"""
tools.py — defines the Tool abstraction and the concrete tools the agent uses.

Phase 3 change: web_search and get_weather no longer contain any
provider-specific logic themselves. They just hold a reference to a
SearchProvider / WeatherProvider (interface, not implementation) and call
it. Which concrete provider gets plugged in is decided in ONE place —
main.py — not scattered across the codebase.

Interview-relevant idea:
The LLM never executes code. It only ever predicts text/structured output.
A "tool call" from the model's side is just it saying:
    "I want to call `search` with argument query='capital of France'"
Our code is what actually runs it and feeds the result back in.
"""

from dataclasses import dataclass
from typing import Callable, Any
import ast
import json
import operator

from providers.search_provider import SearchProvider
from providers.weather_provider import WeatherProvider


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    function: Callable[..., Any]

    def run(self, **kwargs) -> str:
        try:
            result = self.function(**kwargs)
            return str(result)
        except Exception as e:
            # Tool failures are returned AS the observation, not raised —
            # the model needs to see failures to recover from them, and one
            # broken tool must not crash the whole agent loop.
            return f"ERROR running tool '{self.name}': {e}"


# ---------------------------------------------------------------------
# Local, deterministic tools — no external API, kept from Phase 1.
# ---------------------------------------------------------------------

_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Pow: operator.pow,
}
_UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}
_MAX_EXPONENT = 1000  # bounds "9**9**9" style inputs that would hang the server


def _eval_arith(node: ast.AST):
    if isinstance(node, ast.Expression):
        return _eval_arith(node.body)
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return node.value
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_eval_arith(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        left, right = _eval_arith(node.left), _eval_arith(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > _MAX_EXPONENT:
            raise ValueError(f"exponent too large (limit {_MAX_EXPONENT})")
        return _BIN_OPS[type(node.op)](left, right)
    raise ValueError("unsupported expression")


def calculator(expression: str) -> str:
    # Same character whitelist and the same results/exceptions as the
    # eval()-based version used for the reported runs (e.g. ZeroDivisionError
    # still surfaces as a tool error), but evaluated by walking the AST so
    # exponentiation can be bounded.
    allowed = "0123456789+-*/(). "
    if not all(c in allowed for c in expression):
        return "Invalid characters in expression."
    return str(_eval_arith(ast.parse(expression.strip(), mode="eval")))


def word_count(text: str) -> str:
    return str(len(text.split()))


CALCULATOR_TOOL = Tool(
    name="calculator",
    description="Evaluate a basic arithmetic expression, e.g. '12 * (3 + 4)'. Use this for any math.",
    parameters={
        "type": "object",
        "properties": {"expression": {"type": "string", "description": "A math expression to evaluate"}},
        "required": ["expression"],
    },
    function=calculator,
)

WORD_COUNT_TOOL = Tool(
    name="word_count",
    description="Count the number of words in a piece of text.",
    parameters={
        "type": "object",
        "properties": {"text": {"type": "string", "description": "The text to count words in"}},
        "required": ["text"],
    },
    function=word_count,
)


# ---------------------------------------------------------------------
# Provider-backed tools — real external data, provider-agnostic.
# These are FACTORY FUNCTIONS: they take a provider instance and return
# a configured Tool. main.py decides which concrete provider to inject.
# ---------------------------------------------------------------------

def make_web_search_tool(provider: SearchProvider) -> Tool:
    def _search(query: str) -> str:
        results = provider.search(query, max_results=5)
        if not results:
            return json.dumps({"query": query, "results": [], "note": "no results found"})
        # Structured JSON output (not prose) — this is the exact schema
        # Phase 4's eval harness will parse to check what a tool actually
        # returned, independent of how the model chose to phrase its answer.
        return json.dumps({
            "query": query,
            "results": [r.to_dict() for r in results],
        })

    return Tool(
        name="web_search",
        description="Search the live web for current information. Returns structured JSON results "
                     "with title, url, snippet, and source for each hit. Use for anything requiring "
                     "up-to-date or factual information you don't already know.",
        parameters={
            "type": "object",
            "properties": {"query": {"type": "string", "description": "The search query"}},
            "required": ["query"],
        },
        function=_search,
    )


def make_weather_tool(provider: WeatherProvider) -> Tool:
    def _weather(city: str) -> str:
        result = provider.get_weather(city)
        if result is None:
            return json.dumps({"city": city, "error": "weather lookup failed"})
        return json.dumps(result.to_dict())

    return Tool(
        name="get_weather",
        description="Get current real-time weather for a city (temperature in Celsius, condition).",
        parameters={
            "type": "object",
            "properties": {"city": {"type": "string", "description": "City name"}},
            "required": ["city"],
        },
        function=_weather,
    )
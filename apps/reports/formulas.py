"""Safe arithmetic evaluator for calculated fields.

The Dynamic Report Builder must never execute arbitrary code.  Calculated
fields therefore use a restricted expression language parsed and evaluated by
this module instead of Python's ``eval``.  Supported syntax:

* numbers (integers and decimals) and string literals in double quotes
* boolean literals ``true`` / ``false``
* arithmetic: ``+ - * / %`` with parentheses and unary ``-``
* comparisons: ``== != < <= > >=`` combined with ``and`` / ``or`` / ``not``
* whitelisted functions: ``sum``, ``avg``, ``count``, ``min``, ``max``,
  ``abs``, ``round`` and ``if``
* variable references to field codes (bare identifiers)

Anything else (attribute access, imports, lambda, indexing, ``eval``-style
built-ins) is rejected at parse time.
"""

from __future__ import annotations

import re
from typing import Any

from .exceptions import InvalidFormulaError

_NUMBER_RE = re.compile(r"^\d+(\.\d+)?$")
_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

WHITELISTED_FUNCTIONS: frozenset[str] = frozenset(
    {"sum", "avg", "count", "min", "max", "abs", "round", "if"}
)

_TOKEN_PATTERN = re.compile(
    r"""
    \s*(?:
        (?P<NUMBER>\d+\.\d+|\d+)
      | (?P<STRING>"(?:\\.|[^"\\])*")
      | (?P<IDENT>[A-Za-z_][A-Za-z0-9_]*)
      | (?P<OP>==|!=|<=|>=|&&|\|\||[+\-*/%(),<>=!])
    )
    """,
    re.VERBOSE,
)

_TWO_CHAR_OPS = {"==", "!=", "<=", ">=", "&&", "||"}


def _tokenize(expression: str) -> list[tuple[str, str]]:
    tokens: list[tuple[str, str]] = []
    position = 0
    length = len(expression)
    while position < length:
        if expression[position].isspace():
            position += 1
            continue
        match = _TOKEN_PATTERN.match(expression, position)
        if not match:
            raise InvalidFormulaError(f"Unexpected character at position {position}.")
        kind = match.lastgroup
        value = match.group()
        if kind == "OP":
            if value == "!":
                raise InvalidFormulaError("'!' is not supported; use 'not'.")
            if value == "=":
                value = "=="
            elif value == "&&":
                value = "and"
            elif value == "||":
                value = "or"
        tokens.append((kind, value))
        position = match.end()
    tokens.append(("EOF", ""))
    return tokens


def extract_field_references(expression: str) -> set[str]:
    """Return the set of field codes referenced by a formula."""
    tokens = _tokenize(expression)
    references: set[str] = set()
    index = 0
    while index < len(tokens):
        kind, value = tokens[index]
        # A bare identifier is a variable reference unless it is a
        # whitelisted function name or a boolean literal.
        if (
            kind == "IDENT"
            and value not in WHITELISTED_FUNCTIONS
            and value not in {"true", "false"}
        ):
            references.add(value)
        index += 1
    return references


class _Parser:
    """Recursive descent parser for the restricted formula language."""

    def __init__(self, expression: str):
        self._tokens = _tokenize(expression)
        self._index = 0

    @property
    def _current(self) -> tuple[str, str]:
        return self._tokens[self._index]

    def _advance(self) -> tuple[str, str]:
        token = self._tokens[self._index]
        if token[0] != "EOF":
            self._index += 1
        return token

    def _match(self, value: str) -> bool:
        if self._current[1] == value:
            self._advance()
            return True
        return False

    def _expect(self, value: str) -> None:
        if not self._match(value):
            raise InvalidFormulaError(f"Expected '{value}'.")

    def parse(self):
        node = self._or_expr()
        if self._current[0] != "EOF":
            raise InvalidFormulaError("Unexpected trailing input.")
        return node

    def _or_expr(self):
        left = self._and_expr()
        while self._match("or"):
            left = ("or", left, self._and_expr())
        return left

    def _and_expr(self):
        left = self._comparison()
        while self._match("and"):
            left = ("and", left, self._comparison())
        return left

    def _comparison(self):
        left = self._additive()
        if self._current[1] in {"==", "!=", "<", "<=", ">", ">="}:
            operator = self._advance()[1]
            right = self._additive()
            return (operator, left, right)
        return left

    def _additive(self):
        left = self._multiplicative()
        while self._current[1] in {"+", "-"}:
            operator = self._advance()[1]
            left = (operator, left, self._multiplicative())
        return left

    def _multiplicative(self):
        left = self._unary()
        while self._current[1] in {"*", "/", "%"}:
            operator = self._advance()[1]
            left = (operator, left, self._unary())
        return left

    def _unary(self):
        if self._match("-"):
            return ("neg", self._unary())
        if self._match("+"):
            return self._unary()
        if self._match("not"):
            return ("not", self._unary())
        return self._primary()

    def _primary(self):
        kind, value = self._current
        if kind == "NUMBER":
            self._advance()
            return ("num", float(value) if "." in value else int(value))
        if kind == "STRING":
            self._advance()
            return ("str", value[1:-1].replace('\\"', '"').replace("\\\\", "\\"))
        if kind == "IDENT":
            self._advance()
            if value == "true":
                return ("bool", True)
            if value == "false":
                return ("bool", False)
            if self._match("("):
                args = self._arg_list()
                self._expect(")")
                if value not in WHITELISTED_FUNCTIONS:
                    raise InvalidFormulaError(f"Unknown function '{value}'.")
                return ("call", value, args)
            return ("var", value)
        if self._match("("):
            node = self._or_expr()
            self._expect(")")
            return node
        raise InvalidFormulaError(f"Unexpected token '{value}'.")

    def _arg_list(self):
        args = []
        if self._current[1] == ")":
            return args
        args.append(self._or_expr())
        while self._match(","):
            args.append(self._or_expr())
        return args


class _Evaluator:
    """Tree-walking evaluator over parser output."""

    def __init__(self, values: dict[str, Any]):
        self._values = values

    def evaluate(self, node):
        kind = node[0]
        if kind == "num":
            return node[1]
        if kind == "str":
            return node[1]
        if kind == "bool":
            return node[1]
        if kind == "var":
            return self._values.get(node[1])
        if kind == "neg":
            return -self._numeric(self.evaluate(node[1]))
        if kind == "not":
            return not self._truthy(self.evaluate(node[1]))
        if kind in {"+", "-", "*", "/", "%"}:
            left = self._numeric(self.evaluate(node[1]))
            right = self._numeric(self.evaluate(node[2]))
            if kind == "+":
                return left + right
            if kind == "-":
                return left - right
            if kind == "*":
                return left * right
            if kind == "/":
                if right == 0:
                    return 0
                return left / right
            if right == 0:
                return 0
            return left % right
        if kind in {"==", "!=", "<", "<=", ">", ">="}:
            left = self.evaluate(node[1])
            right = self.evaluate(node[2])
            return self._compare(kind, left, right)
        if kind == "and":
            return self._truthy(self.evaluate(node[1])) and self._truthy(
                self.evaluate(node[2])
            )
        if kind == "or":
            return self._truthy(self.evaluate(node[1])) or self._truthy(
                self.evaluate(node[2])
            )
        if kind == "call":
            return self._call(node[1], node[2])
        raise InvalidFormulaError("Unsupported expression node.")

    def _call(self, name: str, args):
        if name == "abs":
            return abs(self._numeric(self.evaluate(self._require_arg(name, args, 0))))
        if name == "round":
            if len(args) == 1:
                return round(self._numeric(self.evaluate(self._require_arg(name, args, 0))))
            return round(
                self._numeric(self.evaluate(self._require_arg(name, args, 0))),
                self._numeric(self.evaluate(self._require_arg(name, args, 1, 0))),
            )
        if name == "sum":
            return sum(self._numeric(self.evaluate(arg)) for arg in args)
        if name == "avg":
            if not args:
                raise InvalidFormulaError("avg() requires at least one argument.")
            values = [self._numeric(self.evaluate(arg)) for arg in args]
            return sum(values) / len(values)
        if name == "count":
            return sum(1 for arg in args if not self._is_empty(self.evaluate(arg)))
        if name == "min":
            if not args:
                raise InvalidFormulaError("min() requires at least one argument.")
            return min(self._numeric(self.evaluate(arg)) for arg in args)
        if name == "max":
            if not args:
                raise InvalidFormulaError("max() requires at least one argument.")
            return max(self._numeric(self.evaluate(arg)) for arg in args)
        if name == "if":
            if len(args) != 3:
                raise InvalidFormulaError("if() requires three arguments.")
            condition = self.evaluate(args[0])
            branch = args[1] if self._truthy(condition) else args[2]
            return self.evaluate(branch)
        raise InvalidFormulaError(f"Unknown function '{name}'.")

    @staticmethod
    def _require_arg(name: str, args: list, index: int, default: Any = None):
        if len(args) <= index:
            if default is not None:
                return default
            raise InvalidFormulaError(f"{name}() missing argument {index + 1}.")
        return args[index]

    @staticmethod
    def _compare(operator: str, left: Any, right: Any) -> bool:
        if operator == "==":
            return left == right
        if operator == "!=":
            return left != right
        if left is None or right is None:
            return False
        try:
            left_num = _coerce_number(left)
            right_num = _coerce_number(right)
            numeric = True
        except (TypeError, ValueError):
            numeric = False
        if operator == "<":
            return (left_num < right_num) if numeric else (left < right)
        if operator == "<=":
            return (left_num <= right_num) if numeric else (left <= right)
        if operator == ">":
            return (left_num > right_num) if numeric else (left > right)
        if operator == ">=":
            return (left_num >= right_num) if numeric else (left >= right)
        raise InvalidFormulaError(f"Unknown comparison '{operator}'.")

    def _numeric(self, value: Any) -> float:
        try:
            return float(_coerce_number(value))
        except (TypeError, ValueError) as exc:
            raise InvalidFormulaError(
                f"Non-numeric value '{value!r}' in arithmetic expression."
            ) from exc

    @staticmethod
    def _truthy(value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        return bool(value)

    @staticmethod
    def _is_empty(value: Any) -> bool:
        return value is None or value == "" or value == []


def _coerce_number(value: Any):
    if value is None:
        return 0
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int | float):
        return value
    if isinstance(value, str) and value.strip():
        return float(value)
    raise TypeError(f"Cannot coerce {value!r} to a number.")


def validate_formula(expression: str) -> None:
    """Parse a formula and raise :class:`InvalidFormulaError` when invalid."""
    if not isinstance(expression, str) or not expression.strip():
        raise InvalidFormulaError("Formula must be a non-empty string.")
    _Parser(expression).parse()


def evaluate_formula(expression: str, values: dict[str, Any]) -> Any:
    """Evaluate a formula against a values mapping.

    Raises :class:`InvalidFormulaError` for syntax errors, forbidden
    functions, or runtime coercion failures.
    """
    node = _Parser(expression).parse()
    return _Evaluator(values).evaluate(node)

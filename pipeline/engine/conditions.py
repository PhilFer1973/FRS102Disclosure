"""Trigger-condition evaluator for the checklist engine.

Parses the boolean trigger conditions drafted onto requirements — e.g.
'has_share_capital == true AND is_financial_institution == false',
'NOT presents_separate_income_statement', 'has_accounting_policy_changes' — and
evaluates them against an engagement's fact profile using THREE-VALUED logic
(True / False / Unknown). An unresolved fact yields Unknown, so the engine can
route an undetermined requirement to the question queue rather than guessing.

Pure code (CLAUDE.md: checklist engine is deterministic and idempotent). No
eval(); a small recursive-descent parser over a fixed grammar.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Ternary value: True | False | None(=unknown)
Tern = bool | None

_TOKEN = re.compile(r"""\s*('[^']*'|"[^"]*"|==|!=|&&|\|\||\(|\)|[A-Za-z_][A-Za-z0-9_]*)""")
_KEYWORDS = {"and": "AND", "or": "OR", "not": "NOT",
             "true": "TRUE", "false": "FALSE"}


def _tokenize(s: str) -> list[tuple[str, str]]:
    tokens, pos = [], 0
    while pos < len(s):
        m = _TOKEN.match(s, pos)
        if not m:
            if s[pos:].strip() == "":
                break
            raise ValueError(f"cannot tokenise {s[pos:]!r} in {s!r}")
        pos = m.end()
        raw = m.group(1)
        if raw[:1] in ("'", '"'):
            tokens.append(("STRING", raw[1:-1]))
        elif raw == "&&":
            tokens.append(("AND", raw))
        elif raw == "||":
            tokens.append(("OR", raw))
        elif raw in ("==", "!=", "(", ")"):
            tokens.append((raw, raw))
        else:
            kind = _KEYWORDS.get(raw.lower())
            tokens.append((kind, raw) if kind else ("IDENT", raw))
    tokens.append(("END", ""))
    return tokens


@dataclass
class _Parser:
    tokens: list[tuple[str, str]]
    i: int = 0

    def peek(self) -> str:
        return self.tokens[self.i][0]

    def take(self, kind: str | None = None) -> tuple[str, str]:
        tok = self.tokens[self.i]
        if kind and tok[0] != kind:
            raise ValueError(f"expected {kind}, got {tok}")
        self.i += 1
        return tok

    def parse(self) -> tuple:
        node = self._or()
        self.take("END")
        return node

    def _or(self) -> tuple:
        node = self._and()
        while self.peek() == "OR":
            self.take("OR")
            node = ("or", node, self._and())
        return node

    def _and(self) -> tuple:
        node = self._not()
        while self.peek() == "AND":
            self.take("AND")
            node = ("and", node, self._not())
        return node

    def _not(self) -> tuple:
        if self.peek() == "NOT":
            self.take("NOT")
            return ("not", self._not())
        return self._atom()

    def _atom(self) -> tuple:
        if self.peek() == "(":
            self.take("(")
            node = self._or()
            self.take(")")
            return node
        name = self.take("IDENT")[1]
        if self.peek() in ("==", "!="):
            op = self.take()[0]
            lit = self.take()              # TRUE | FALSE | STRING
            if lit[0] == "TRUE":
                want: bool | str = True
            elif lit[0] == "FALSE":
                want = False
            elif lit[0] == "STRING":
                want = lit[1]
            else:
                raise ValueError(f"expected true/false/string after {op}, got {lit}")
            return ("cmp", name, op, want)
        return ("cmp", name, "==", True)   # bare fact == truthy


def parse(condition: str) -> tuple:
    return _Parser(_tokenize(condition)).parse()


def _eval(node: tuple, facts: dict[str, bool]) -> Tern:
    kind = node[0]
    if kind == "cmp":
        _, name, op, want = node
        if name not in facts:
            return None
        return facts[name] == want if op == "==" else facts[name] != want
    if kind == "not":
        v = _eval(node[1], facts)
        return None if v is None else (not v)
    a = _eval(node[1], facts)
    b = _eval(node[2], facts)
    if kind == "and":
        if a is False or b is False:
            return False
        if a is None or b is None:
            return None
        return True
    if kind == "or":
        if a is True or b is True:
            return True
        if a is None or b is None:
            return None
        return False
    raise ValueError(f"bad node {node!r}")


def evaluate(condition: str, facts: dict[str, bool]) -> Tern:
    """True / False / None(=undetermined) for `condition` given resolved facts."""
    return _eval(parse(condition), facts)


def referenced_facts(condition: str) -> set[str]:
    out: set[str] = set()

    def walk(n: tuple) -> None:
        if n[0] == "cmp":
            out.add(n[1])
        elif n[0] == "not":
            walk(n[1])
        else:
            walk(n[1])
            walk(n[2])

    walk(parse(condition))
    return out

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Union


@dataclass
class Node:
    pass


@dataclass
class Program(Node):
    statements: List[Node]


@dataclass
class Identifier(Node):
    name: str


@dataclass
class NumberLiteral(Node):
    value: int


@dataclass
class StringLiteral(Node):
    value: str


Expr = Union[Identifier, NumberLiteral, StringLiteral]


@dataclass
class Declare(Node):
    name: Identifier
    type_or_size: str
    value: Optional[Expr]
    reserve: bool


@dataclass
class Mov(Node):
    dest: Identifier
    src: Expr


@dataclass
class Add(Node):
    left: Identifier
    right: Identifier


@dataclass
class Sub(Node):
    left: Identifier
    right: Identifier


@dataclass
class Mul(Node):
    left: Identifier
    right: Identifier


@dataclass
class Div(Node):
    left: Identifier
    right: Identifier


@dataclass
class Sqr(Node):
    operand: Identifier


@dataclass
class Pow(Node):
    left: Identifier
    right: Identifier


@dataclass
class Label(Node):
    name: Identifier


@dataclass
class Goto(Node):
    target: Identifier


@dataclass
class Print(Node):
    value: Identifier


@dataclass
class Read(Node):
    target: Identifier


@dataclass
class Tostr(Node):
    target: Identifier


@dataclass
class Toint(Node):
    target: Identifier


@dataclass
class Prtln(Node):
    pass


@dataclass
class If(Node):
    left: Expr
    op: str  # '==', '<', '>'
    right: Expr
    then_body: List[Node]
    else_body: List[Node]


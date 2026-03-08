from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Union


@dataclass
class IRInstr:
    pass


@dataclass
class IRProgram:
    instrs: List[IRInstr]


@dataclass
class IRDeclare(IRInstr):
    reserve: bool
    type_or_size: str
    name: str
    value: Optional[str]  # текст после '=', как в исходнике


@dataclass
class IRMov(IRInstr):
    dest: str
    src: str  # текстовое представление (число, строка в кавычках или имя переменной)


@dataclass
class IRAdd(IRInstr):
    left: str
    right: str


@dataclass
class IRSub(IRInstr):
    left: str
    right: str


@dataclass
class IRMul(IRInstr):
    left: str
    right: str


@dataclass
class IRDiv(IRInstr):
    left: str
    right: str


@dataclass
class IRSqr(IRInstr):
    var: str


@dataclass
class IRPow(IRInstr):
    left: str
    right: str


@dataclass
class IRLabel(IRInstr):
    name: str


@dataclass
class IRGoto(IRInstr):
    target: str


@dataclass
class IRPrint(IRInstr):
    var: str


@dataclass
class IRRead(IRInstr):
    var: str


@dataclass
class IRTostr(IRInstr):
    var: str


@dataclass
class IRToint(IRInstr):
    var: str


@dataclass
class IRPrtln(IRInstr):
    pass


@dataclass
class IRCondJump(IRInstr):
    op: str        # '==', '<', '>'
    left: str
    right: str
    true_label: str
    false_label: str


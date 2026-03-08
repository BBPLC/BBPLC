from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class TokenKind(Enum):
    # базовые
    IDENT = auto()
    NUMBER = auto()
    STRING = auto()
    NEWLINE = auto()
    EOF = auto()

    # ключевые слова / команды
    DECLARE = auto()
    RESERVE = auto()
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    SQR = auto()
    POW = auto()
    IF = auto()
    THEN = auto()
    ELSE = auto()
    ENDIF = auto()
    TOSTR = auto()
    TOINT = auto()
    LABEL = auto()
    GOTO = auto()
    MOV = auto()
    PRINT = auto()
    READ = auto()
    PUSH = auto()
    POP = auto()
    PRTLN = auto()
    ALLOC = auto()
    FREE = auto()

    # операторы
    EQ = auto()       # ==
    LT = auto()       # <
    GT = auto()       # >
    ASSIGN = auto()   # =
    COLON = auto()    # :


KEYWORDS = {
    "DECLARE": TokenKind.DECLARE,
    "RESERVE": TokenKind.RESERVE,
    "ADD": TokenKind.ADD,
    "SUB": TokenKind.SUB,
    "MUL": TokenKind.MUL,
    "DIV": TokenKind.DIV,
    "SQR": TokenKind.SQR,
    "POW": TokenKind.POW,
    "IF": TokenKind.IF,
    "THEN": TokenKind.THEN,
    "ELSE": TokenKind.ELSE,
    "ENDIF": TokenKind.ENDIF,
    "TOSTR": TokenKind.TOSTR,
    "TOINT": TokenKind.TOINT,
    "LABEL": TokenKind.LABEL,
    "GOTO": TokenKind.GOTO,
    "MOV": TokenKind.MOV,
    "PRINT": TokenKind.PRINT,
    "READ": TokenKind.READ,
    "PUSH": TokenKind.PUSH,
    "POP": TokenKind.POP,
    "PRTLN": TokenKind.PRTLN,
    "ALLOC": TokenKind.ALLOC,
    "FREE": TokenKind.FREE,
}


@dataclass
class Token:
    kind: TokenKind
    lexeme: str
    line: int
    column: int


from __future__ import annotations

from typing import List

from .tokens import Token, TokenKind
from .ast_nodes import (
    Program,
    Node,
    Identifier,
    NumberLiteral,
    StringLiteral,
    Expr,
    Declare,
    Mov,
    Add,
    Sub,
    Mul,
    Div,
    Sqr,
    Pow,
    Label,
    Goto,
    Print,
    Read,
    Tostr,
    Toint,
    Prtln,
    If,
)


class Parser:
    """Рекурсивный спускающийся парсер для языка BBPLC."""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    # === низкоуровневые утилиты ===
    def _peek(self, k: int = 0) -> Token:
        idx = self.pos + k
        if idx >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[idx]

    def _match(self, *kinds: TokenKind) -> Token:
        tok = self._peek()
        if tok.kind in kinds:
            self.pos += 1
            return tok
        expected = ", ".join(k.name for k in kinds)
        raise SyntaxError(
            f"Ожидалось {expected}, но получено {tok.kind.name} на строке {tok.line}"
        )

    def _optional(self, kind: TokenKind) -> bool:
        tok = self._peek()
        if tok.kind is kind:
            self.pos += 1
            return True
        return False

    def _consume_newline(self) -> None:
        # допускаем пустые строки: либо NEWLINE, либо EOF
        if self._optional(TokenKind.NEWLINE):
            return
        if self._peek().kind not in (TokenKind.EOF,):
            raise SyntaxError(
                f"Ожидался конец строки, но найдено {self._peek().kind.name}"
            )

    # === выражения ===
    def _identifier(self) -> Identifier:
        tok = self._match(TokenKind.IDENT)
        return Identifier(tok.lexeme)

    def _expr(self) -> Expr:
        tok = self._peek()
        if tok.kind is TokenKind.IDENT:
            return self._identifier()
        if tok.kind is TokenKind.NUMBER:
            self.pos += 1
            return NumberLiteral(int(tok.lexeme))
        if tok.kind is TokenKind.STRING:
            self.pos += 1
            return StringLiteral(tok.lexeme)
        raise SyntaxError(f"Ожидалось выражение, но найдено {tok.kind.name}")

    # === верхний уровень ===
    def parse(self) -> Program:
        statements: List[Node] = []
        while self._peek().kind is not TokenKind.EOF:
            if self._peek().kind is TokenKind.NEWLINE:
                self.pos += 1
                continue
            statements.append(self._statement())
        return Program(statements)

    def _statement(self) -> Node:
        tok = self._peek()
        kind = tok.kind

        if kind is TokenKind.DECLARE:
            return self._declare()
        if kind is TokenKind.MOV:
            return self._mov()
        if kind is TokenKind.ADD:
            return self._binary_stmt(TokenKind.ADD, Add)
        if kind is TokenKind.SUB:
            return self._binary_stmt(TokenKind.SUB, Sub)
        if kind is TokenKind.MUL:
            return self._binary_stmt(TokenKind.MUL, Mul)
        if kind is TokenKind.DIV:
            return self._binary_stmt(TokenKind.DIV, Div)
        if kind is TokenKind.SQR:
            return self._sqr()
        if kind is TokenKind.POW:
            return self._pow()
        if kind is TokenKind.LABEL:
            return self._label()
        if kind is TokenKind.GOTO:
            return self._goto()
        if kind is TokenKind.PRINT:
            return self._print()
        if kind is TokenKind.READ:
            return self._read()
        if kind is TokenKind.TOSTR:
            return self._tostr()
        if kind is TokenKind.TOINT:
            return self._toint()
        if kind is TokenKind.PRTLN:
            return self._prtln()
        if kind is TokenKind.IF:
            return self._if_stmt()

        raise SyntaxError(f"Неожиданное начало оператора: {kind.name}")

    # === конкретные операторы ===
    def _declare(self) -> Declare:
        self._match(TokenKind.DECLARE)
        reserve = self._optional(TokenKind.RESERVE)
        type_tok = self._match(TokenKind.IDENT, TokenKind.NUMBER)
        type_or_size = type_tok.lexeme
        name = self._identifier()
        value = None
        if self._optional(TokenKind.ASSIGN):
            value = self._expr()
        self._consume_newline()
        return Declare(name=name, type_or_size=type_or_size, value=value, reserve=reserve)

    def _mov(self) -> Mov:
        self._match(TokenKind.MOV)
        dest = self._identifier()
        src = self._expr()
        self._consume_newline()
        return Mov(dest=dest, src=src)

    def _binary_stmt(self, op_kind: TokenKind, cls):
        self._match(op_kind)
        left = self._identifier()
        right_expr = self._expr()
        if not isinstance(right_expr, Identifier):
            raise SyntaxError(
                f"{op_kind.name} ожидает идентификатор вторым операндом"
            )
        self._consume_newline()
        return cls(left=left, right=right_expr)

    def _sqr(self) -> Sqr:
        self._match(TokenKind.SQR)
        op = self._identifier()
        self._consume_newline()
        return Sqr(operand=op)

    def _pow(self) -> Pow:
        self._match(TokenKind.POW)
        left = self._identifier()
        right = self._identifier()
        self._consume_newline()
        return Pow(left=left, right=right)

    def _label(self) -> Label:
        self._match(TokenKind.LABEL)
        name = self._identifier()
        self._consume_newline()
        return Label(name=name)

    def _goto(self) -> Goto:
        self._match(TokenKind.GOTO)
        target = self._identifier()
        self._consume_newline()
        return Goto(target=target)

    def _print(self) -> Print:
        self._match(TokenKind.PRINT)
        ident = self._identifier()
        self._consume_newline()
        return Print(value=ident)

    def _read(self) -> Read:
        self._match(TokenKind.READ)
        ident = self._identifier()
        self._consume_newline()
        return Read(target=ident)

    def _tostr(self) -> Tostr:
        self._match(TokenKind.TOSTR)
        ident = self._identifier()
        self._consume_newline()
        return Tostr(target=ident)

    def _toint(self) -> Toint:
        self._match(TokenKind.TOINT)
        ident = self._identifier()
        self._consume_newline()
        return Toint(target=ident)

    def _prtln(self) -> Prtln:
        self._match(TokenKind.PRTLN)
        self._consume_newline()
        return Prtln()

    def _if_stmt(self) -> If:
        # Поддерживаем многострочный IF ... THEN ... [ELSE ...] ENDIF
        self._match(TokenKind.IF)
        left = self._expr()
        op_tok = self._match(TokenKind.EQ, TokenKind.LT, TokenKind.GT)
        op_map = {
            TokenKind.EQ: "==",
            TokenKind.LT: "<",
            TokenKind.GT: ">",
        }
        op = op_map[op_tok.kind]
        right = self._expr()
        self._match(TokenKind.THEN)
        self._consume_newline()

        then_body: List[Node] = []
        else_body: List[Node] = []

        while self._peek().kind not in (
            TokenKind.ELSE,
            TokenKind.ENDIF,
            TokenKind.EOF,
        ):
            then_body.append(self._statement())

        if self._optional(TokenKind.ELSE):
            self._consume_newline()
            while self._peek().kind not in (TokenKind.ENDIF, TokenKind.EOF):
                else_body.append(self._statement())

        self._match(TokenKind.ENDIF)
        self._consume_newline()
        return If(left=left, op=op, right=right, then_body=then_body, else_body=else_body)


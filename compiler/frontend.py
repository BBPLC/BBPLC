from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional, Union


# ===== tokens & lexer =====

class TokenKind(Enum):
    # базовые
    IDENT = auto()
    NUMBER = auto()
    STRING = auto()
    NEWLINE = auto()
    EOF = auto()

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
    MALLOC = auto()
    REALLOC = auto()
    SIZEOF = auto()
    REG = auto()
    LOAD = auto()
    STORE = auto()
    CLEAR = auto()
    INC = auto()
    DEC = auto()
    MACRO = auto()
    ENDMACRO = auto()
    PROC = auto()
    ENDPROC = auto()
    RETURN = auto()
    ELSEIF = auto()  # optional, but for clarity

    # string / file operators
    CONCAT = auto()
    LENGTH = auto()
    SUBSTR = auto()
    INDEX = auto()
    OPEN = auto()
    CLOSE = auto()
    WRITE = auto()
    READFILE = auto()

    # операторы
    EQ = auto()       # ==
    LT = auto()       # <
    GT = auto()       # >
    LT_EQ = auto()    # <=
    GT_EQ = auto()    # >=
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
    "MALLOC": TokenKind.MALLOC,
    "REALLOC": TokenKind.REALLOC,
    "SIZEOF": TokenKind.SIZEOF,
    "REG": TokenKind.REG,
    "LOAD": TokenKind.LOAD,
    "STORE": TokenKind.STORE,
    "CLEAR": TokenKind.CLEAR,
    "INC": TokenKind.INC,
    "DEC": TokenKind.DEC,
    "MACRO": TokenKind.MACRO,
    "ENDMACRO": TokenKind.ENDMACRO,
    "PROC": TokenKind.PROC,
    "ENDPROC": TokenKind.ENDPROC,
    "RETURN": TokenKind.RETURN,
    "CONCAT": TokenKind.CONCAT,
    "LENGTH": TokenKind.LENGTH,
    "SUBSTR": TokenKind.SUBSTR,
    "INDEX": TokenKind.INDEX,
    "OPEN": TokenKind.OPEN,
    "CLOSE": TokenKind.CLOSE,
    "WRITE": TokenKind.WRITE,
    "READFILE": TokenKind.READFILE,
}


@dataclass
class Token:
    kind: TokenKind
    lexeme: str
    line: int
    column: int


class Lexer:
    """Преобразует исходный текст BBPLC в поток токенов."""

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.col = 1
        self.length = len(text)

    def _peek(self, offset: int = 0) -> str:
        idx = self.pos + offset
        if idx >= self.length:
            return "\0"
        return self.text[idx]

    def _advance(self) -> str:
        ch = self._peek()
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def _skip_whitespace_and_comments(self) -> None:
        while True:
            ch = self._peek()
            if ch in " \t\r":
                self._advance()
            elif ch == ";":
                # комментарий до конца строки
                while self._peek() not in ("\n", "\0"):
                    self._advance()
            else:
                break

    def _identifier_or_keyword(self) -> Token:
        start_pos = self.pos
        start_col = self.col
        # identifiers may include alphanumeric, underscore, and dot for "struct" names
        while self._peek().isalnum() or self._peek() in ("_", "."):
            self._advance()
        lex = self.text[start_pos : self.pos]
        kind = KEYWORDS.get(lex.upper(), TokenKind.IDENT)
        return Token(kind, lex, self.line, start_col)

    def _number(self) -> Token:
        start_pos = self.pos
        start_col = self.col
        while self._peek().isdigit():
            self._advance()
        lex = self.text[start_pos : self.pos]
        return Token(TokenKind.NUMBER, lex, self.line, start_col)

    def _string(self) -> Token:
        quote = self._advance()  # открывающая кавычка
        start_col = self.col
        start_pos = self.pos
        while True:
            ch = self._peek()
            if ch == "\0":
                raise SyntaxError(f"Незакрытая строка на строке {self.line}")
            if ch == quote:
                break
            self._advance()
        lex = self.text[start_pos : self.pos]
        self._advance()  # закрывающая кавычка
        return Token(TokenKind.STRING, lex, self.line, start_col)

    def next_token(self) -> Token:
        self._skip_whitespace_and_comments()
        ch = self._peek()

        if ch == "\0":
            return Token(TokenKind.EOF, "", self.line, self.col)

        if ch == "\n":
            self._advance()
            # NEWLINE относится к предыдущей строке
            return Token(TokenKind.NEWLINE, "\\n", self.line - 1, 1)

        if ch.isalpha() or ch == "_":
            return self._identifier_or_keyword()

        if ch.isdigit():
            return self._number()

        if ch in ('"', "'"):
            return self._string()

        # операторы
        if ch == "=" and self._peek(1) == "=":
            self._advance()
            self._advance()
            return Token(TokenKind.EQ, "==", self.line, self.col - 2)

        if ch == "<":
            if self._peek(1) == "=":
                self._advance()
                self._advance()
                return Token(TokenKind.LT_EQ, "<=", self.line, self.col - 2)
            else:
                self._advance()
                return Token(TokenKind.LT, "<", self.line, self.col - 1)

        if ch == ">":
            if self._peek(1) == "=":
                self._advance()
                self._advance()
                return Token(TokenKind.GT_EQ, ">=", self.line, self.col - 2)
            else:
                self._advance()
                return Token(TokenKind.GT, ">", self.line, self.col - 1)

        if ch == "=":
            self._advance()
            return Token(TokenKind.ASSIGN, "=", self.line, self.col - 1)

        if ch == ":":
            self._advance()
            return Token(TokenKind.COLON, ":", self.line, self.col - 1)

        raise SyntaxError(f"Неизвестный символ '{ch}' на строке {self.line}, столбец {self.col}")


def tokenize(text: str) -> List[Token]:
    """Удобный хелпер: весь текст -> список токенов до EOF включительно."""
    lexer = Lexer(text)
    tokens: List[Token] = []
    while True:
        tok = lexer.next_token()
        tokens.append(tok)
        if tok.kind is TokenKind.EOF:
            break
    return tokens


# ===== AST nodes =====

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
    right: Expr


@dataclass
class Sub(Node):
    left: Identifier
    right: Expr


@dataclass
class Mul(Node):
    left: Identifier
    right: Expr


@dataclass
class Div(Node):
    left: Identifier
    right: Expr


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
    else_body: Optional[Union[List[Node], 'If']]


@dataclass
class Push(Node):
    value: Identifier


@dataclass
class Pop(Node):
    target: Identifier


@dataclass
class Malloc(Node):
    target: Identifier
    size: Expr


@dataclass
class Realloc(Node):
    target: Identifier
    new_size: Expr


@dataclass
class Free(Node):
    target: Identifier


@dataclass
class Sizeof(Node):
    target: Identifier
    result: Identifier


@dataclass
class Reg(Node):
    register: str  # 'eax', 'ebx', etc.
    operation: str  # 'load', 'store', 'add', etc.
    variable: Optional[Expr]  # Can be Identifier, NumberLiteral, or None for unary ops

# string/file/struct operations

@dataclass
class Concat(Node):
    dest: Identifier
    src: Expr

@dataclass
class Length(Node):
    src: Identifier
    result: Identifier

@dataclass
class Substr(Node):
    dest: Identifier
    src: Identifier
    start: Expr
    length: Expr

@dataclass
class Index(Node):
    dest: Identifier
    src: Identifier
    index: Expr

@dataclass
class Open(Node):
    filename: Expr
    result: Identifier

@dataclass
class Close(Node):
    handle: Identifier

@dataclass
class Write(Node):
    handle: Identifier
    src: Expr

@dataclass
class ReadFile(Node):
    handle: Identifier
    dest: Identifier
    size: Expr


@dataclass
class Macro(Node):
    name: Identifier
    body: List[Node]


@dataclass
class Proc(Node):
    name: Identifier
    body: List[Node]


@dataclass
class Return(Node):
    value: Optional[Expr]


@dataclass
class Call(Node):
    name: Identifier


# ===== parser =====

class Parser:
    """Рекурсивный спускающийся парсер для языка BBPLC."""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    # === низкоурневые утилиты ===
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
        tok = self._peek()
        if tok.kind is TokenKind.IDENT:
            self.pos += 1
            return Identifier(tok.lexeme)
        # Allow LABEL token to be used as an identifier in contexts where it's not a keyword
        if tok.kind is TokenKind.LABEL:
            self.pos += 1
            return Identifier(tok.lexeme)
        raise SyntaxError(
            f"Ожидалось IDENT, но получено {tok.kind.name} на строке {tok.line}"
        )

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
        # skip any empty lines
        while self._peek().kind is TokenKind.NEWLINE:
            self.pos += 1
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
        if kind is TokenKind.PUSH:
            return self._push()
        if kind is TokenKind.POP:
            return self._pop()
        if kind is TokenKind.MALLOC:
            return self._malloc()
        if kind is TokenKind.REALLOC:
            return self._realloc()
        if kind is TokenKind.FREE:
            return self._free()
        if kind is TokenKind.SIZEOF:
            return self._sizeof()
        if kind is TokenKind.REG:
            return self._reg()
        if kind is TokenKind.CONCAT:
            return self._concat()
        if kind is TokenKind.LENGTH:
            return self._length()
        if kind is TokenKind.SUBSTR:
            return self._substr()
        if kind is TokenKind.INDEX:
            return self._index()
        if kind is TokenKind.OPEN:
            return self._open()
        if kind is TokenKind.CLOSE:
            return self._close()
        if kind is TokenKind.WRITE:
            return self._write()
        if kind is TokenKind.READFILE:
            return self._readfile()
        if kind is TokenKind.MACRO:
            return self._macro()
        if kind is TokenKind.PROC:
            return self._proc()
        if kind is TokenKind.RETURN:
            return self._return()

        raise SyntaxError(f"Неожиданное начало оператора: {kind.name}")

    # === конкретные операторы ===
    def _declare(self) -> Declare:
        self._match(TokenKind.DECLARE)
        reserve = self._optional(TokenKind.RESERVE)
        type_tok = self._match(TokenKind.IDENT, TokenKind.NUMBER)
        type_or_size = type_tok.lexeme
        name = self._identifier()
        value = None
        # For RESERVE declarations, allow size as a number without '='
        if reserve and self._peek().kind is TokenKind.NUMBER:
            value = NumberLiteral(int(self._peek().lexeme))
            self.pos += 1
        elif self._optional(TokenKind.ASSIGN):
            value = self._expr()
        self._consume_newline()
        return Declare(name=name, type_or_size=type_or_size, value=value, reserve=reserve)

    def _mov(self) -> Mov:
        self._match(TokenKind.MOV)
        dest = self._identifier()
        src = self._expr()
        self._consume_newline()
        return Mov(dest=dest, src=src)

    def _binary_stmt(self, tok_kind: TokenKind, cls):
        self._match(tok_kind)
        left = self._identifier()
        # right operand may be an identifier, number, or string literal
        right_expr = self._expr()
        self._consume_newline()
        return cls(left=left, right=right_expr)

    def _sqr(self) -> Sqr:
        self._match(TokenKind.SQR)
        operand = self._identifier()
        self._consume_newline()
        return Sqr(operand=operand)

    def _pow(self) -> Pow:
        self._match(TokenKind.POW)
        left = self._identifier()
        right = self._identifier()
        self._consume_newline()
        return Pow(left=left, right=right)

    def _label(self) -> Label:
        # Consume the keyword and the actual label identifier following it
        self._match(TokenKind.LABEL)
        name_tok = self._match(TokenKind.IDENT)
        name = Identifier(name_tok.lexeme)
        self._consume_newline()
        return Label(name=name)

    def _goto(self) -> Goto:
        self._match(TokenKind.GOTO)
        target = self._identifier()
        self._consume_newline()
        return Goto(target=target)

    def _print(self) -> Print:
        self._match(TokenKind.PRINT)
        value = self._identifier()
        self._consume_newline()
        return Print(value=value)

    def _read(self) -> Read:
        self._match(TokenKind.READ)
        target = self._identifier()
        self._consume_newline()
        return Read(target=target)

    def _tostr(self) -> Tostr:
        self._match(TokenKind.TOSTR)
        target = self._identifier()
        self._consume_newline()
        return Tostr(target=target)

    def _toint(self) -> Toint:
        self._match(TokenKind.TOINT)
        target = self._identifier()
        self._consume_newline()
        return Toint(target=target)

    def _prtln(self) -> Prtln:
        self._match(TokenKind.PRTLN)
        self._consume_newline()
        return Prtln()

    def _if_stmt(self, consume_endif: bool = True) -> If:
        """Parse an IF statement, optionally consuming the terminating ENDIF.

        ``consume_endif`` should be set to False by callers in an "else if"
        chain so that only the outermost invocation swallows the final ENDIF
        token from the source.
        """
        self._match(TokenKind.IF)
        left = self._expr()
        op_token = self._match(TokenKind.EQ, TokenKind.LT, TokenKind.GT, TokenKind.LT_EQ, TokenKind.GT_EQ)
        op_map = {TokenKind.EQ: "==", TokenKind.LT: "<", TokenKind.GT: ">", TokenKind.LT_EQ: "<=", TokenKind.GT_EQ: ">="}
        op = op_map[op_token.kind]
        right = self._expr()

        # allow optional newline before THEN (users sometimes put it on next line)
        while self._optional(TokenKind.NEWLINE):
            pass
        self._match(TokenKind.THEN)
        self._consume_newline()

        then_body: List[Node] = []
        else_body: Optional[Union[List[Node], If]] = None

        # collect then-body
        while self._peek().kind not in (TokenKind.ELSE, TokenKind.ELSEIF, TokenKind.ENDIF):
            while self._peek().kind is TokenKind.NEWLINE:
                self.pos += 1
            if self._peek().kind in (TokenKind.ELSE, TokenKind.ELSEIF, TokenKind.ENDIF):
                break
            then_body.append(self._statement())

        # handle else / elif sequences
        if self._optional(TokenKind.ELSE):
            if self._peek().kind is TokenKind.IF:
                # ELSE IF chain, parse nested if without consuming final ENDIF
                else_body = self._if_stmt(consume_endif=False)
            else:
                self._consume_newline()
                else_body = []
                while self._peek().kind not in (TokenKind.ENDIF,):
                    while self._peek().kind is TokenKind.NEWLINE:
                        self.pos += 1
                    if self._peek().kind is TokenKind.ENDIF:
                        break
                    else_body.append(self._statement())
        elif self._optional(TokenKind.ELSEIF):
            else_body = self._if_stmt(consume_endif=False)

        # consume the closing ENDIF if requested
        if consume_endif:
            self._match(TokenKind.ENDIF)
            self._consume_newline()

        return If(left=left, op=op, right=right, then_body=then_body, else_body=else_body)

    def _push(self) -> Push:
        self._match(TokenKind.PUSH)
        value = self._identifier()
        self._consume_newline()
        return Push(value=value)

    def _pop(self) -> Pop:
        self._match(TokenKind.POP)
        target = self._identifier()
        self._consume_newline()
        return Pop(target=target)

    def _malloc(self) -> Malloc:
        self._match(TokenKind.MALLOC)
        target = self._identifier()
        size = self._expr()
        self._consume_newline()
        return Malloc(target=target, size=size)

    def _realloc(self) -> Realloc:
        self._match(TokenKind.REALLOC)
        target = self._identifier()
        new_size = self._expr()
        self._consume_newline()
        return Realloc(target=target, new_size=new_size)

    def _free(self) -> Free:
        self._match(TokenKind.FREE)
        target = self._identifier()
        self._consume_newline()
        return Free(target=target)

    def _sizeof(self) -> Sizeof:
        self._match(TokenKind.SIZEOF)
        target = self._identifier()
        result = self._identifier()
        self._consume_newline()
        return Sizeof(target=target, result=result)

    def _reg(self) -> Reg:
        self._match(TokenKind.REG)
        register = self._match(TokenKind.IDENT).lexeme
        # operation may be a keyword token (LOAD, STORE, ADD, etc.) or any identifier
        op_tok = self._peek()
        if op_tok.kind in (
            TokenKind.IDENT, TokenKind.LOAD, TokenKind.STORE, TokenKind.ADD,
            TokenKind.SUB, TokenKind.MUL, TokenKind.DIV, TokenKind.CLEAR,
            TokenKind.INC, TokenKind.DEC
        ):
            self.pos += 1
            operation = op_tok.lexeme
        else:
            raise SyntaxError(f"Ожидалось имя операции REG, но получено {op_tok.kind.name} на строке {op_tok.line}")
        variable: Optional[Expr] = None
        if self._peek().kind in (TokenKind.IDENT, TokenKind.NUMBER, TokenKind.STRING):
            variable = self._expr()
        self._consume_newline()
        return Reg(register=register, operation=operation, variable=variable)

    def _macro(self) -> Macro:
        self._match(TokenKind.MACRO)
        name = self._identifier()
        body: List[Node] = []
        self._consume_newline()
        while self._peek().kind is not TokenKind.ENDMACRO:
            body.append(self._statement())
        self._match(TokenKind.ENDMACRO)
        self._consume_newline()
        return Macro(name=name, body=body)

    def _proc(self) -> Proc:
        self._match(TokenKind.PROC)
        name = self._identifier()
        body: List[Node] = []
        self._consume_newline()
        while self._peek().kind is not TokenKind.ENDPROC:
            body.append(self._statement())
        self._match(TokenKind.ENDPROC)
        self._consume_newline()
        return Proc(name=name, body=body)

    def _return(self) -> Return:
        self._match(TokenKind.RETURN)
        value: Optional[Expr] = None
        if self._peek().kind in (TokenKind.IDENT, TokenKind.NUMBER):
            value = self._expr()
        self._consume_newline()
        return Return(value=value)

    # --- new statement implementations ---

    def _concat(self) -> Concat:
        self._match(TokenKind.CONCAT)
        dest = self._identifier()
        src = self._expr()
        self._consume_newline()
        return Concat(dest=dest, src=src)

    def _length(self) -> Length:
        self._match(TokenKind.LENGTH)
        src = self._identifier()
        result = self._identifier()
        self._consume_newline()
        return Length(src=src, result=result)

    def _substr(self) -> Substr:
        self._match(TokenKind.SUBSTR)
        dest = self._identifier()
        src = self._identifier()
        start = self._expr()
        length = self._expr()
        self._consume_newline()
        return Substr(dest=dest, src=src, start=start, length=length)

    def _index(self) -> Index:
        self._match(TokenKind.INDEX)
        dest = self._identifier()
        src = self._identifier()
        index = self._expr()
        self._consume_newline()
        return Index(dest=dest, src=src, index=index)

    def _open(self) -> Open:
        self._match(TokenKind.OPEN)
        filename = self._expr()
        result = self._identifier()
        self._consume_newline()
        return Open(filename=filename, result=result)

    def _close(self) -> Close:
        self._match(TokenKind.CLOSE)
        handle = self._identifier()
        self._consume_newline()
        return Close(handle=handle)

    def _write(self) -> Write:
        self._match(TokenKind.WRITE)
        handle = self._identifier()
        src = self._expr()
        self._consume_newline()
        return Write(handle=handle, src=src)

    def _readfile(self) -> ReadFile:
        self._match(TokenKind.READFILE)
        handle = self._identifier()
        dest = self._identifier()
        size = self._expr()
        self._consume_newline()
        return ReadFile(handle=handle, dest=dest, size=size)


# ===== IR definitions =====

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


@dataclass
class IRPush(IRInstr):
    var: str


@dataclass
class IRPop(IRInstr):
    var: str


@dataclass
class IRMalloc(IRInstr):
    target: str
    size: str


@dataclass
class IRRealloc(IRInstr):
    target: str
    new_size: str


@dataclass
class IRFree(IRInstr):
    var: str


@dataclass
class IRSizeof(IRInstr):
    target: str
    result: str


@dataclass
class IRReg(IRInstr):
    register: str
    operation: str
    variable: str

@dataclass
class IRConcat(IRInstr):
    dest: str
    src: str

@dataclass
class IRLength(IRInstr):
    src: str
    result: str

@dataclass
class IRSubstr(IRInstr):
    dest: str
    src: str
    start: str
    length: str

@dataclass
class IRIndex(IRInstr):
    dest: str
    src: str
    index: str

@dataclass
class IROpen(IRInstr):
    filename: str
    result: str

@dataclass
class IRClose(IRInstr):
    handle: str

@dataclass
class IRWrite(IRInstr):
    handle: str
    src: str

@dataclass
class IRReadFile(IRInstr):
    handle: str
    dest: str
    size: str


# ===== IR builder =====

class IRBuilder:
    """AST → простое промежуточное представление BBPLC."""

    def __init__(self):
        self.decl_instrs: List[IRInstr] = []
        self.code_instrs: List[IRInstr] = []
        self._label_counter = 0

    def _new_label(self, prefix: str = "L") -> str:
        name = f"{prefix}{self._label_counter}"
        self._label_counter += 1
        return name

    def build(self, program: Program) -> IRProgram:
        for stmt in program.statements:
            self._emit_stmt(stmt)
        # Все DECLARE идут первыми, как в старой версии компилятора
        return IRProgram(instrs=self.decl_instrs + self.code_instrs)

    def _emit(self, instr: IRInstr, is_decl: bool = False) -> None:
        if is_decl:
            self.decl_instrs.append(instr)
        else:
            self.code_instrs.append(instr)

    # === AST → IR по операторам ===
    def _emit_stmt(self, node: Node) -> None:
        if isinstance(node, Declare):
            self._emit(self._decl_to_ir(node), is_decl=True)
        elif isinstance(node, Mov):
            self._emit(self._mov_to_ir(node))
        elif isinstance(node, Add):
            right_text = self._expr_to_literal_text(node.right)
            self._emit(IRAdd(left=node.left.name, right=right_text))
        elif isinstance(node, Sub):
            right_text = self._expr_to_literal_text(node.right)
            self._emit(IRSub(left=node.left.name, right=right_text))
        elif isinstance(node, Mul):
            right_text = self._expr_to_literal_text(node.right)
            self._emit(IRMul(left=node.left.name, right=right_text))
        elif isinstance(node, Div):
            right_text = self._expr_to_literal_text(node.right)
            self._emit(IRDiv(left=node.left.name, right=right_text))
        elif isinstance(node, Sqr):
            self._emit(IRSqr(var=node.operand.name))
        elif isinstance(node, Pow):
            self._emit(IRPow(left=node.left.name, right=node.right.name))
        elif isinstance(node, Label):
            self._emit(IRLabel(name=node.name.name))
        elif isinstance(node, Goto):
            self._emit(IRGoto(target=node.target.name))
        elif isinstance(node, Print):
            self._emit(IRPrint(var=node.value.name))
        elif isinstance(node, Read):
            self._emit(IRRead(var=node.target.name))
        elif isinstance(node, Tostr):
            self._emit(IRTostr(var=node.target.name))
        elif isinstance(node, Toint):
            self._emit(IRToint(var=node.target.name))
        elif isinstance(node, Prtln):
            self._emit(IRPrtln())
        elif isinstance(node, If):
            self._emit_if(node)
        elif isinstance(node, Push):
            self._emit(IRPush(var=node.value.name))
        elif isinstance(node, Pop):
            self._emit(IRPop(var=node.target.name))
        elif isinstance(node, Malloc):
            size_text = self._expr_to_literal_text(node.size)
            self._emit(IRMalloc(target=node.target.name, size=size_text))
        elif isinstance(node, Realloc):
            new_size_text = self._expr_to_literal_text(node.new_size)
            self._emit(IRRealloc(target=node.target.name, new_size=new_size_text))
        elif isinstance(node, Free):
            self._emit(IRFree(var=node.target.name))
        elif isinstance(node, Sizeof):
            self._emit(IRSizeof(target=node.target.name, result=node.result.name))
        elif isinstance(node, Reg):
            if node.variable is not None:
                var_text = self._expr_to_literal_text(node.variable)
            else:
                var_text = ""
            self._emit(IRReg(register=node.register, operation=node.operation, variable=var_text))
        elif isinstance(node, Concat):
            src_text = self._expr_to_literal_text(node.src)
            self._emit(IRConcat(dest=node.dest.name, src=src_text))
        elif isinstance(node, Length):
            self._emit(IRLength(src=node.src.name, result=node.result.name))
        elif isinstance(node, Substr):
            start_text = self._expr_to_literal_text(node.start)
            length_text = self._expr_to_literal_text(node.length)
            self._emit(IRSubstr(dest=node.dest.name, src=node.src.name, start=start_text, length=length_text))
        elif isinstance(node, Index):
            index_text = self._expr_to_literal_text(node.index)
            self._emit(IRIndex(dest=node.dest.name, src=node.src.name, index=index_text))
        elif isinstance(node, Open):
            fname = self._expr_to_literal_text(node.filename)
            self._emit(IROpen(filename=fname, result=node.result.name))
        elif isinstance(node, Close):
            self._emit(IRClose(handle=node.handle.name))
        elif isinstance(node, Write):
            src_text = self._expr_to_literal_text(node.src)
            self._emit(IRWrite(handle=node.handle.name, src=src_text))
        elif isinstance(node, ReadFile):
            size_text = self._expr_to_literal_text(node.size)
            self._emit(IRReadFile(handle=node.handle.name, dest=node.dest.name, size=size_text))
        elif isinstance(node, Macro):
            # For now, just emit the body (macros are expanded inline)
            for stmt in node.body:
                self._emit_stmt(stmt)
        elif isinstance(node, Proc):
            # Procedures are like labels with body
            self._emit(IRLabel(name=node.name.name))
            for stmt in node.body:
                self._emit_stmt(stmt)
        elif isinstance(node, Return):
            # For now, just a goto to end of proc, but since no stack, maybe just ignore or add later
            pass  # TODO: implement return
        elif isinstance(node, Call):
            # Macro calls - expand the macro body inline (lookup from defined macros)
            # For now, treat as a label jump since procedures are labels
            self._emit(IRGoto(target=node.name.name))
        else:
            raise NotImplementedError(f"IR для {type(node).__name__} не реализован")

    def _expr_to_literal_text(self, expr: Expr) -> str:
        """Преобразует простое выражение в текст, совместимый с parse_declare/mov."""
        if isinstance(expr, Identifier):
            return expr.name
        if isinstance(expr, NumberLiteral):
            return str(expr.value)
        if isinstance(expr, StringLiteral):
            # оборачиваем в кавычки, как в исходнике
            return f"\"{expr.value}\""
        raise NotImplementedError(f"Неподдерживаемое выражение {expr!r}")

    def _decl_to_ir(self, node: Declare) -> IRDeclare:
        value_text = None
        if node.value is not None:
            value_text = self._expr_to_literal_text(node.value)
        return IRDeclare(
            reserve=node.reserve,
            type_or_size=node.type_or_size,
            name=node.name.name,
            value=value_text,
        )

    def _mov_to_ir(self, node: Mov) -> IRMov:
        src_text = self._expr_to_literal_text(node.src)
        return IRMov(dest=node.dest.name, src=src_text)

    def _expr_to_var(self, expr: Expr) -> str:
        if isinstance(expr, Identifier):
            return expr.name
        # Для констант можно создать временную переменную через DECLARE+MOV
        if isinstance(expr, NumberLiteral):
            tmp = self._new_label("tmp_")
            # Declare the temporary variable first (32‑bit integer)
            self._emit(IRDeclare(reserve=False, type_or_size="DD", name=tmp, value="0"), is_decl=True)
            self._emit(IRMov(dest=tmp, src=str(expr.value)))
            return tmp
        if isinstance(expr, StringLiteral):
            tmp = self._new_label("tmpstr_")
            # Declare a byte array initialized with the string
            quoted = f'"{expr.value}"'
            self._emit(IRDeclare(reserve=False, type_or_size="DB", name=tmp, value=quoted), is_decl=True)
            return tmp
        raise NotImplementedError(f"Неподдерживаемое выражение {expr!r}")

    def _emit_if(self, node: If) -> None:
        true_label = self._new_label("L_true_")
        false_label = self._new_label("L_false_")
        end_label = self._new_label("L_end_")

        left_name = self._expr_to_var(node.left)
        right_name = self._expr_to_var(node.right)

        self._emit(
            IRCondJump(
                op=node.op,
                left=left_name,
                right=right_name,
                true_label=true_label,
                false_label=false_label,
            )
        )
        # THEN
        self._emit(IRLabel(name=true_label))
        for stmt in node.then_body:
            self._emit_stmt(stmt)
        self._emit(IRGoto(target=end_label))

        # ELSE
        self._emit(IRLabel(name=false_label))
        if isinstance(node.else_body, list):
            for stmt in node.else_body:
                self._emit_stmt(stmt)
        elif isinstance(node.else_body, If):
            self._emit_if(node.else_body)
        # If None, do nothing

        # ENDIF
        self._emit(IRLabel(name=end_label))

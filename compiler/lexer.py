from __future__ import annotations

from typing import List

from .tokens import Token, TokenKind, KEYWORDS


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
        while self._peek().isalnum() or self._peek() == "_":
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


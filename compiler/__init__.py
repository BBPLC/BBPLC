"""
Compiler package for BBPLC language.

Contains the following stages:
- lexer:   source text -> tokens
- parser:  tokens -> AST
- ir:      AST -> intermediate representation
- codegen: IR -> x86-32 Linux assembly
"""


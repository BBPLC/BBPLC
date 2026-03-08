from __future__ import annotations

import sys

from compiler.lexer import tokenize
from compiler.parser import Parser
from compiler.ir_builder import IRBuilder
from compiler.codegen_x86 import CodegenX86


def main() -> None:
    src_file = sys.argv[1] if len(sys.argv) > 1 else "code.bbplc"

    with open(src_file, "r", encoding="utf-8") as f:
        text = f.read()

    # Лексер: текст -> токены
    tokens = tokenize(text)

    # Парсер: токены -> AST
    parser = Parser(tokens)
    ast_program = parser.parse()

    # AST -> IR
    ir_builder = IRBuilder()
    ir_program = ir_builder.build(ast_program)

    # IR -> x86-32 ASM (Linux) через существующий runtime
    codegen = CodegenX86()
    asm_text = codegen.generate(ir_program)

    with open("output.asm", "w", encoding="utf-8") as f:
        f.write(asm_text)

    print("ASM code generated in output.asm")


if __name__ == "__main__":
    main()

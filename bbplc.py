#!/usr/bin/env python3
from __future__ import annotations
import sys
import subprocess
import os
import argparse

from compiler.frontend import tokenize, Parser, IRBuilder
from compiler.linux_x86_32 import get_backend, available_backends

def run(cmd: list[str]) -> None:
    """Запускает команду в терминале и завершает при ошибке"""
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print("Command failed:", " ".join(cmd))
        sys.exit(result.returncode)

def default_output_name(src: str) -> str:
    """Имя файла без расширения"""
    return os.path.splitext(os.path.basename(src))[0]

def make_executable(path: str) -> None:
    os.chmod(path, 0o755)

def main() -> None:
    parser = argparse.ArgumentParser(description="BBPLC compiler")
    parser.add_argument("source", help="Source file (.bbplc)")
    parser.add_argument("-b", "--backend", default="x86", choices=available_backends(),
                        help="Backend to use")
    parser.add_argument("-t", "--target", nargs=2, metavar=("TYPE", "NAME"),
                        help="Output target: bin or so, optional name")
    parser.add_argument("--run", action="store_true", help="Compile and run program")
    args = parser.parse_args()

    src_file = args.source
    backend_name = args.backend
    target_type = "bin"
    output_name = default_output_name(src_file)

    if args.target:
        target_type, output_name = args.target
        if target_type not in ("bin", "so"):
            print("Unknown target type:", target_type)
            sys.exit(1)

    # ---------- read source ----------
    with open(src_file, "r", encoding="utf-8") as f:
        text = f.read()

    tokens = tokenize(text)
    ast_program = Parser(tokens).parse()
    ir_program = IRBuilder().build(ast_program)

    try:
        Backend = get_backend(backend_name)
    except KeyError:
        print(f"Backend '{backend_name}' not found. Available:", ", ".join(available_backends()))
        sys.exit(1)

    asm_text = Backend().generate(ir_program)
    asm_file = output_name + ".asm"
    with open(asm_file, "w", encoding="utf-8") as f:
        f.write(asm_text)
    print("ASM generated:", asm_file)

    # ---------- compile ----------
    if target_type == "bin":
        print("Compiling binary via FASM...")
        run(["fasm", asm_file, output_name])
        make_executable(output_name)
        print("Binary created:", output_name)
        if args.run:
            run(["./" + output_name])
    else:  # shared library
        obj_file = output_name + ".o"
        so_file = output_name + ".so"
        print("Compiling object via FASM...")
        run(["fasm", asm_file, obj_file])
        print("Linking shared library...")
        run(["ld", "-shared", "-o", so_file, obj_file])
        print("Shared library created:", so_file)

if __name__ == "__main__":
    main()
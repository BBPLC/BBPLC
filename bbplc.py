from __future__ import annotations

import sys
import subprocess
import os

from compiler.frontend import tokenize, Parser, IRBuilder
from compiler.codegen import get_backend, available_backends


def run(cmd: list[str]) -> None:
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print("Command failed:", " ".join(cmd))
        sys.exit(result.returncode)


def default_output_name(src: str) -> str:
    return os.path.splitext(os.path.basename(src))[0]


def make_executable(path: str) -> None:
    os.chmod(path, 0o755)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        prog="bbplc",
        description="BBPLC compiler",
        epilog="""
Examples:

compile binary:
  bbplc program.bbplc --target bin

compile binary with custom name:
  bbplc program.bbplc --target bin myprogram

compile shared library:
  bbplc program.bbplc --target so mylib

compile and run:
  bbplc program.bbplc --run
""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "source",
        help="source file (.bbplc)"
    )

    backends_list = ", ".join(available_backends())

    parser.add_argument(
        "-b",
        "--backend",
        default="x86",
        help=f"backend to use ({backends_list})"
    )

    parser.add_argument(
        "--target",
        nargs="+",
        metavar=("TYPE", "NAME"),
        help="output target: bin or so (optional name)"
    )

    parser.add_argument(
        "--run",
        action="store_true",
        help="compile and run program"
    )

    args = parser.parse_args()

    src_file = args.source
    backend_name = args.backend

    # ---------- target parsing ----------

    target_type = "bin"
    output_name = None

    if args.target:
        target_type = args.target[0]

        if target_type not in ("bin", "so"):
            print("Unknown target:", target_type)
            sys.exit(1)

        if len(args.target) > 1:
            output_name = args.target[1]

    if output_name is None:
        output_name = default_output_name(src_file)

    # ---------- read source ----------

    with open(src_file, "r", encoding="utf-8") as f:
        text = f.read()

    tokens = tokenize(text)

    parser_obj = Parser(tokens)
    ast_program = parser_obj.parse()

    ir_builder = IRBuilder()
    ir_program = ir_builder.build(ast_program)

    try:
        Backend = get_backend(backend_name)
    except KeyError:
        print(f"backend '{backend_name}' not found")
        print("Available:", ", ".join(available_backends()))
        sys.exit(1)

    codegen = Backend()
    asm_text = codegen.generate(ir_program)

    asm_file = output_name + ".asm"

    with open(asm_file, "w", encoding="utf-8") as f:
        f.write(asm_text)

    print("ASM generated:", asm_file)

    # ---------- compile ----------

    if target_type == "bin":

        print("Compiling binary via FASM")

        run(["fasm", asm_file, output_name])

        make_executable(output_name)

        print("Binary created:", output_name)

        if args.run:
            print("Running program...\n")
            run(["./" + output_name])

    elif target_type == "so":

        obj_file = output_name + ".o"
        so_file = output_name + ".so"

        print("Compiling object via FASM")

        run(["fasm", asm_file, obj_file])

        print("Linking shared library")

        run([
            "ld",
            "-shared",
            "-o",
            so_file,
            obj_file
        ])

        print("Shared library created:", so_file)


if __name__ == "__main__":
    main()

from __future__ import annotations

from typing import Optional

from modules import context_manager
from modules.io import print_var, read_var, prtln
from modules.math import add, sub, mul, div, sqr, pow
from modules.bbplctypes import (
    parse_declare,
    declare,
    tostr,
    toint,
    get_var_size,
)

from .ir import (
    IRProgram,
    IRInstr,
    IRDeclare,
    IRMov,
    IRAdd,
    IRSub,
    IRMul,
    IRDiv,
    IRSqr,
    IRPow,
    IRLabel,
    IRGoto,
    IRPrint,
    IRRead,
    IRTostr,
    IRToint,
    IRPrtln,
    IRCondJump,
)


class CodegenX86:
    """
    Преобразует IR-программу в ассемблер x86-32 под Linux.

    Внутри использует существующие модули:
    - modules.bbplctypes: DECLARE, TOSTR, TOINT, MOV и работу с типами
    - modules.math: арифметические операции
    - modules.io: PRINT / READ / PRTLN
    - modules.context_manager: хранение declares / asm_lines
    """

    def generate(self, ir: IRProgram) -> str:
        self._reset_context()

        for instr in ir.instrs:
            self._emit_instr(instr)

        self._emit_program_epilogue()
        self._emit_program_preamble()

        return "\n".join(context_manager.asm_lines)

    def _reset_context(self) -> None:
        context_manager.variables.clear()
        context_manager.var_types.clear()
        context_manager.declares.clear()
        context_manager.buffers_created.clear()
        context_manager.tostr_counter.clear()
        context_manager.asm_lines.clear()

    # === генерация по IR-инструкциям ===
    def _emit_instr(self, instr: IRInstr) -> None:
        if isinstance(instr, IRDeclare):
            self._emit_declare(instr)
        elif isinstance(instr, IRMov):
            from modules.bbplctypes import mov

            mov(instr.dest, instr.src)
        elif isinstance(instr, IRAdd):
            add(instr.left, instr.right)
        elif isinstance(instr, IRSub):
            sub(instr.left, instr.right)
        elif isinstance(instr, IRMul):
            mul(instr.left, instr.right)
        elif isinstance(instr, IRDiv):
            div(instr.left, instr.right)
        elif isinstance(instr, IRSqr):
            sqr(instr.var)
        elif isinstance(instr, IRPow):
            pow(instr.left, instr.right)
        elif isinstance(instr, IRLabel):
            context_manager.asm_lines.append(f"{instr.name}:")
        elif isinstance(instr, IRGoto):
            context_manager.asm_lines.append(f"jmp {instr.target}")
        elif isinstance(instr, IRPrint):
            print_var(instr.var)
        elif isinstance(instr, IRRead):
            read_var(instr.var)
        elif isinstance(instr, IRTostr):
            tostr(instr.var)
        elif isinstance(instr, IRToint):
            toint(instr.var)
        elif isinstance(instr, IRPrtln):
            prtln()
        elif isinstance(instr, IRCondJump):
            self._emit_cond_jump(instr)
        else:
            raise NotImplementedError(f"Codegen для {type(instr).__name__} не реализован")

    def _emit_declare(self, instr: IRDeclare) -> None:
        # Восстанавливаем строку DECLARE максимально блико к исходнику и
        # передаём в существующий parse_declare/declare.
        parts = ["DECLARE"]
        if instr.reserve:
            parts.append("RESERVE")
        parts.append(instr.type_or_size)
        parts.append(instr.name)
        line = " ".join(parts)
        if instr.value is not None:
            line = f"{line} = {instr.value}"

        var_type, var_name, var_value, reserve_flag = parse_declare(line)
        if var_type:
            declare(var_type, var_name, var_value, reserve_flag)

    def _emit_cond_jump(self, instr: IRCondJump) -> None:
        op1 = instr.left
        op2 = instr.right
        label_true = instr.true_label
        label_false = instr.false_label

        size1, _ = get_var_size(op1)
        size2, _ = get_var_size(op2)

        if size1 <= 2 and size2 <= 2:
            reg = "ax" if size1 == 2 else "al"
            context_manager.asm_lines.append(f"mov {reg}, [{op1}]")
            context_manager.asm_lines.append(f"cmp {reg}, [{op2}]")
        else:
            context_manager.asm_lines.append(f"mov eax, [{op1}]")
            context_manager.asm_lines.append(f"cmp eax, [{op2}]")

        if instr.op == "==":
            context_manager.asm_lines.append(f"je {label_true}")
        elif instr.op == ">":
            context_manager.asm_lines.append(f"jg {label_true}")
        elif instr.op == "<":
            context_manager.asm_lines.append(f"jl {label_true}")
        else:
            raise ValueError(f"Неподдерживаемый оператор сравнения {instr.op}")

        context_manager.asm_lines.append(f"jmp {label_false}")

    # === обёртка вокруг старого пролога/эпилога ===
    def _emit_program_epilogue(self) -> None:
        # нормальное завершение процесса
        context_manager.asm_lines.append("mov eax, 1")
        context_manager.asm_lines.append("xor ebx, ebx")
        context_manager.asm_lines.append("int 0x80")

        # обработчик переполнения, который уже использует math.py
        context_manager.asm_lines.append(".overflow:")
        context_manager.asm_lines.append("; simple overflow trap")
        context_manager.asm_lines.append("mov eax, 1")
        context_manager.asm_lines.append("mov ebx, 1")
        context_manager.asm_lines.append("int 0x80")

    def _emit_program_preamble(self) -> None:
        prologue = [
            "format ELF executable 4",
            "entry start",
            "",
        ] + context_manager.declares + ["start:"]

        context_manager.asm_lines[:0] = prologue


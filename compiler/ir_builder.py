from __future__ import annotations

from typing import List

from . import ast_nodes as ast
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
    IRPush,
    IRPop,
    IRMalloc,
    IRRealloc,
    IRFree,
    IRSizeof,
    IRReg,
)


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

    def build(self, program: ast.Program) -> IRProgram:
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
    def _emit_stmt(self, node: ast.Node) -> None:
        if isinstance(node, ast.Declare):
            self._emit(self._decl_to_ir(node), is_decl=True)
        elif isinstance(node, ast.Mov):
            self._emit(self._mov_to_ir(node))
        elif isinstance(node, ast.Add):
            right_text = self._expr_to_literal_text(node.right)
            self._emit(IRAdd(left=node.left.name, right=right_text))
        elif isinstance(node, ast.Sub):
            right_text = self._expr_to_literal_text(node.right)
            self._emit(IRSub(left=node.left.name, right=right_text))
        elif isinstance(node, ast.Mul):
            right_text = self._expr_to_literal_text(node.right)
            self._emit(IRMul(left=node.left.name, right=right_text))
        elif isinstance(node, ast.Div):
            right_text = self._expr_to_literal_text(node.right)
            self._emit(IRDiv(left=node.left.name, right=right_text))
        elif isinstance(node, ast.Sqr):
            self._emit(IRSqr(var=node.operand.name))
        elif isinstance(node, ast.Pow):
            self._emit(IRPow(left=node.left.name, right=node.right.name))
        elif isinstance(node, ast.Label):
            self._emit(IRLabel(name=node.name.name))
        elif isinstance(node, ast.Goto):
            self._emit(IRGoto(target=node.target.name))
        elif isinstance(node, ast.Print):
            self._emit(IRPrint(var=node.value.name))
        elif isinstance(node, ast.Read):
            self._emit(IRRead(var=node.target.name))
        elif isinstance(node, ast.Tostr):
            self._emit(IRTostr(var=node.target.name))
        elif isinstance(node, ast.Toint):
            self._emit(IRToint(var=node.target.name))
        elif isinstance(node, ast.Prtln):
            self._emit(IRPrtln())
        elif isinstance(node, ast.If):
            self._emit_if(node)
        elif isinstance(node, ast.Push):
            self._emit(IRPush(var=node.value.name))
        elif isinstance(node, ast.Pop):
            self._emit(IRPop(var=node.target.name))
        elif isinstance(node, ast.Malloc):
            size_text = self._expr_to_literal_text(node.size)
            self._emit(IRMalloc(target=node.target.name, size=size_text))
        elif isinstance(node, ast.Realloc):
            new_size_text = self._expr_to_literal_text(node.new_size)
            self._emit(IRRealloc(target=node.target.name, new_size=new_size_text))
        elif isinstance(node, ast.Free):
            self._emit(IRFree(var=node.target.name))
        elif isinstance(node, ast.Sizeof):
            self._emit(IRSizeof(target=node.target.name, result=node.result.name))
        elif isinstance(node, ast.Reg):
            if node.variable is not None:
                var_text = self._expr_to_literal_text(node.variable)
            else:
                var_text = ""
            self._emit(IRReg(register=node.register, operation=node.operation, variable=var_text))
        elif isinstance(node, ast.Macro):
            # For now, just emit the body (macros are expanded inline)
            for stmt in node.body:
                self._emit_stmt(stmt)
        elif isinstance(node, ast.Proc):
            # Procedures are like labels with body
            self._emit(IRLabel(name=node.name.name))
            for stmt in node.body:
                self._emit_stmt(stmt)
        elif isinstance(node, ast.Return):
            # For now, just a goto to end of proc, but since no stack, maybe just ignore or add later
            pass  # TODO: implement return
        elif isinstance(node, ast.Call):
            # Macro calls - expand the macro body inline (lookup from defined macros)
            # For now, treat as a label jump since procedures are labels
            self._emit(IRGoto(target=node.name.name))
        else:
            raise NotImplementedError(f"IR для {type(node).__name__} не реализован")

    def _expr_to_literal_text(self, expr: ast.Expr) -> str:
        """Преобразует простое выражение в текст, совместимый с parse_declare/mov."""
        if isinstance(expr, ast.Identifier):
            return expr.name
        if isinstance(expr, ast.NumberLiteral):
            return str(expr.value)
        if isinstance(expr, ast.StringLiteral):
            # оборачиваем в кавычки, как в исходнике
            return f"\"{expr.value}\""
        raise NotImplementedError(f"Неподдерживаемое выражение {expr!r}")

    def _decl_to_ir(self, node: ast.Declare) -> IRDeclare:
        value_text = None
        if node.value is not None:
            value_text = self._expr_to_literal_text(node.value)
        return IRDeclare(
            reserve=node.reserve,
            type_or_size=node.type_or_size,
            name=node.name.name,
            value=value_text,
        )

    def _mov_to_ir(self, node: ast.Mov) -> IRMov:
        src_text = self._expr_to_literal_text(node.src)
        return IRMov(dest=node.dest.name, src=src_text)

    def _expr_to_var(self, expr: ast.Expr) -> str:
        if isinstance(expr, ast.Identifier):
            return expr.name
        # Для констант можно создать временную переменную через MOV
        if isinstance(expr, ast.NumberLiteral):
            tmp = self._new_label("tmp_")
            # Declare the temporary variable first
            self._emit(IRDeclare(reserve=False, type_or_size="DD", name=tmp, value="0"), is_decl=True)
            self._emit(IRMov(dest=tmp, src=str(expr.value)))
            return tmp
        raise NotImplementedError("Строковые константы в условиях пока не поддержаны")

    def _emit_if(self, node: ast.If) -> None:
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
        elif isinstance(node.else_body, ast.If):
            self._emit_if(node.else_body)
        # If None, do nothing

        # ENDIF
        self._emit(IRLabel(name=end_label))


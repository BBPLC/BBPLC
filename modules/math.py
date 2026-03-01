from modules.bbplctypes import safe_name, get_var_size
from modules.context_manager import variables, declares, buffers_created, tostr_counter, asm_lines

def add(op1, op2):
    size, _ = get_var_size(op1)
    if size == 1:
        asm_lines.append(f"mov al, [{op1}]")
        asm_lines.append(f"add al, [{op2}]")
        asm_lines.append(f"mov [{op1}], al")
    elif size == 2:
        asm_lines.append(f"mov ax, [{op1}]")
        asm_lines.append(f"add ax, [{op2}]")
        asm_lines.append(f"mov [{op1}], ax")
    else:
        asm_lines.append(f"mov eax, [{op1}]")
        asm_lines.append(f"add eax, [{op2}]")
        asm_lines.append(f"mov [{op1}], eax")

def sub(op1, op2):
    size1, _ = get_var_size(op1)
    size2, _ = get_var_size(op2)

    if size1 == 1:
        asm_lines.append(f"mov al, [{op1}]")
        asm_lines.append(f"sub al, [{op2}]")
        asm_lines.append(f"mov [{op1}], al")
    elif size1 == 2:
        asm_lines.append(f"mov ax, [{op1}]")
        asm_lines.append(f"sub ax, [{op2}]")
        asm_lines.append(f"mov [{op1}], ax")
    else:
        asm_lines.append(f"mov eax, [{op1}]")
        asm_lines.append(f"sub eax, [{op2}]")
        asm_lines.append(f"mov [{op1}], eax")

def mul(op1, op2):
    size1, _ = get_var_size(op1)
    if size1 <= 2:
        reg = "ax" if size1 == 2 else "al"
        asm_lines.append(f"mov {reg}, [{op1}]")
        asm_lines.append(f"imul {reg}, [{op2}]")
        asm_lines.append(f"mov [{op1}], {reg}")
    else:
        asm_lines.append(f"mov eax, [{op1}]")
        asm_lines.append(f"imul eax, [{op2}]")
        asm_lines.append(f"mov [{op1}], eax")

def div(op1, op2):
    size1, _ = get_var_size(op1)
    if size1 <= 2:
        reg = "ax" if size1 == 2 else "al"
        asm_lines.append(f"mov {reg}, [{op1}]")
        asm_lines.append(f"cwd" if size1==2 else "cbw")
        asm_lines.append(f"idiv [{op2}]")
        asm_lines.append(f"mov [{op1}], {reg}")
    else:
        asm_lines.append(f"mov eax, [{op1}]")
        asm_lines.append(f"cdq")
        asm_lines.append(f"idiv dword [{op2}]")
        asm_lines.append(f"mov [{op1}], eax")

def sqr(op1):
    size1, _ = get_var_size(op1)
    if size1 <= 2:
        reg = "ax" if size1 == 2 else "al"
        asm_lines.append(f"mov {reg}, [{op1}]")
        asm_lines.append(f"imul {reg}, {reg}")
        asm_lines.append(f"mov [{op1}], {reg}")
    else:
        asm_lines.append(f"mov eax, [{op1}]")
        asm_lines.append(f"imul eax, eax")
        asm_lines.append(f"mov [{op1}], eax")

def pow(op1, op2):
    size1, _ = get_var_size(op1)
    if size1 <= 2:
        reg = "ax" if size1 == 2 else "al"
        asm_lines.append(f"mov {reg}, [{op1}]")
        asm_lines.append(f"mov cx, [{op2}]")
        asm_lines.append(f"mov bx, {reg}")
        asm_lines.append(f"cmp cx, 0")
        asm_lines.append(f"je .pow_done_{op1}")
        asm_lines.append(f"dec cx")
        asm_lines.append(f".pow_loop_{op1}:")
        asm_lines.append(f"imul {reg}, bx")
        asm_lines.append(f"dec cx")
        asm_lines.append(f"jnz .pow_loop_{op1}")
        asm_lines.append(f".pow_done_{op1}:")
        asm_lines.append(f"mov [{op1}], {reg}")
    else:
        asm_lines.append(f"mov eax, [{op1}]")
        asm_lines.append(f"mov ecx, [{op2}]")
        asm_lines.append(f"mov ebx, eax")
        asm_lines.append(f"cmp ecx, 0")
        asm_lines.append(f"je .pow_done_{op1}")
        asm_lines.append(f"dec ecx")
        asm_lines.append(f".pow_loop_{op1}:")
        asm_lines.append(f"imul eax, ebx")
        asm_lines.append(f"dec ecx")
        asm_lines.append(f"jnz .pow_loop_{op1}")
        asm_lines.append(f".pow_done_{op1}:")
        asm_lines.append(f"mov [{op1}], eax")
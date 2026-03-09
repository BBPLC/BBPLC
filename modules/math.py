from modules.bbplctypes import safe_name, get_var_size
from modules.context_manager import variables, declares, buffers_created, tostr_counter, asm_lines

def add(op1, op2):
    op1_safe = safe_name(op1)
    # Check if op2 is a number literal
    is_literal = isinstance(op2, str) and op2.isdigit()
    op2_safe = op2 if is_literal else safe_name(op2)
    size1, _ = get_var_size(op1)
    if not is_literal:
        size2, _ = get_var_size(op2)
    else:
        size2 = 4
    from modules.context_manager import var_types as _types
    if _types.get(op1_safe, {}).get('reserved'):
        print(f"Warning: ADD using reserved variable {op1}")
    if not is_literal and _types.get(op2_safe, {}).get('reserved'):
        print(f"Warning: ADD using reserved variable {op2}")
    if size1 != size2:
        print(f"Warning: ADD operand size mismatch {op1}({size1}) vs {op2}({size2})")
    size = max(size1, size2)

    if size == 1:
        asm_lines.append(f"mov al, [{op1_safe}]")
        if is_literal:
            asm_lines.append(f"add al, {op2_safe}")
        else:
            asm_lines.append(f"add al, [{op2_safe}]")
        asm_lines.append("jo overflow_handler")
        asm_lines.append(f"mov [{op1_safe}], al")
    elif size == 2:
        asm_lines.append(f"mov ax, [{op1_safe}]")
        if is_literal:
            asm_lines.append(f"add ax, {op2_safe}")
        else:
            asm_lines.append(f"add ax, [{op2_safe}]")
        asm_lines.append("jo overflow_handler")
        asm_lines.append(f"mov [{op1_safe}], ax")
    else:
        asm_lines.append(f"mov eax, [{op1_safe}]")
        if is_literal:
            asm_lines.append(f"add eax, {op2_safe}")
        else:
            asm_lines.append(f"add eax, [{op2_safe}]")
        asm_lines.append("jo overflow_handler")
        asm_lines.append(f"mov [{op1_safe}], eax")

def sub(op1, op2):
    op1_safe = safe_name(op1)
    # Check if op2 is a number literal
    is_literal = isinstance(op2, str) and op2.isdigit()
    op2_safe = op2 if is_literal else safe_name(op2)
    size1, _ = get_var_size(op1)
    if not is_literal:
        size2, _ = get_var_size(op2)
    else:
        size2 = 4
    from modules.context_manager import var_types as _types
    if _types.get(op1_safe, {}).get('reserved'):
        print(f"Warning: SUB using reserved variable {op1}")
    if not is_literal and _types.get(op2_safe, {}).get('reserved'):
        print(f"Warning: SUB using reserved variable {op2}")
    if size1 != size2:
        print(f"Warning: SUB operand size mismatch {op1}({size1}) vs {op2}({size2})")
    size = max(size1, size2)

    if size == 1:
        asm_lines.append(f"mov al, [{op1_safe}]")
        if is_literal:
            asm_lines.append(f"sub al, {op2_safe}")
        else:
            asm_lines.append(f"sub al, [{op2_safe}]")
        asm_lines.append("jo overflow_handler")
        asm_lines.append(f"mov [{op1_safe}], al")
    elif size == 2:
        asm_lines.append(f"mov ax, [{op1_safe}]")
        if is_literal:
            asm_lines.append(f"sub ax, {op2_safe}")
        else:
            asm_lines.append(f"sub ax, [{op2_safe}]")
        asm_lines.append("jo overflow_handler")
        asm_lines.append(f"mov [{op1_safe}], ax")
    else:
        asm_lines.append(f"mov eax, [{op1_safe}]")
        if is_literal:
            asm_lines.append(f"sub eax, {op2_safe}")
        else:
            asm_lines.append(f"sub eax, [{op2_safe}]")
        asm_lines.append("jo overflow_handler")
        asm_lines.append(f"mov [{op1_safe}], eax")

def mul(op1, op2):
    op1_safe = safe_name(op1)
    # Check if op2 is a number literal
    is_literal = isinstance(op2, str) and op2.isdigit()
    op2_safe = op2 if is_literal else safe_name(op2)
    size1, _ = get_var_size(op1)
    if not is_literal:
        size2, _ = get_var_size(op2)
    else:
        size2 = 4
    from modules.context_manager import var_types as _types
    if _types.get(op1_safe, {}).get('reserved'):
        print(f"Warning: MUL using reserved variable {op1}")
    if not is_literal and _types.get(op2_safe, {}).get('reserved'):
        print(f"Warning: MUL using reserved variable {op2}")
    if size1 != size2:
        print(f"Warning: MUL operand size mismatch {op1}({size1}) vs {op2}({size2})")
    size = max(size1, size2)
    if size <= 2:
        reg = "ax" if size == 2 else "al"
        asm_lines.append(f"mov {reg}, [{op1_safe}]")
        if is_literal:
            asm_lines.append(f"imul {reg}, {op2_safe}")
        else:
            asm_lines.append(f"imul {reg}, [{op2_safe}]")
        asm_lines.append("jo overflow_handler")
        asm_lines.append(f"mov [{op1_safe}], {reg}")
    else:
        asm_lines.append(f"mov eax, [{op1_safe}]")
        if is_literal:
            asm_lines.append(f"imul eax, {op2_safe}")
        else:
            asm_lines.append(f"imul eax, [{op2_safe}]")
        asm_lines.append("jo overflow_handler")
        asm_lines.append(f"mov [{op1_safe}], eax")

def div(op1, op2):
    op1_safe = safe_name(op1)
    # Check if op2 is a number literal
    is_literal = isinstance(op2, str) and op2.isdigit()
    op2_safe = op2 if is_literal else safe_name(op2)
    size1, _ = get_var_size(op1)
    if not is_literal:
        size2, _ = get_var_size(op2)
    else:
        size2 = 4
    from modules.context_manager import var_types as _types
    if _types.get(op1_safe, {}).get('reserved'):
        print(f"Warning: DIV using reserved variable {op1}")
    if not is_literal and _types.get(op2_safe, {}).get('reserved'):
        print(f"Warning: DIV using reserved variable {op2}")
    if size1 != size2:
        print(f"Warning: DIV operand size mismatch {op1}({size1}) vs {op2}({size2})")
    if size1 <= 2:
        reg = "ax" if size1 == 2 else "al"
        asm_lines.append(f"mov {reg}, [{op1_safe}]")
        asm_lines.append(f"cwd" if size1==2 else "cbw")
        if is_literal:
            # idiv cannot take immediate, load into register first
            asm_lines.append(f"mov bx, {op2_safe}")
            asm_lines.append(f"idiv bx")
        else:
            asm_lines.append(f"idiv [{op2_safe}]")
        asm_lines.append("jo overflow_handler")
        asm_lines.append(f"mov [{op1_safe}], {reg}")
    else:
        asm_lines.append(f"mov eax, [{op1_safe}]")
        asm_lines.append(f"cdq")
        if is_literal:
            # idiv cannot take immediate, load into register first
            asm_lines.append(f"mov ebx, {op2_safe}")
            asm_lines.append(f"idiv ebx")
        else:
            asm_lines.append(f"idiv dword [{op2_safe}]")
        asm_lines.append("jo overflow_handler")
        asm_lines.append(f"mov [{op1_safe}], eax")

def sqr(op1):
    op_safe = safe_name(op1)
    size1, _ = get_var_size(op1)
    from modules.context_manager import var_types as _types
    if _types.get(op_safe, {}).get('reserved'):
        print(f"Warning: SQR using reserved variable {op1}")
    if size1 <= 2:
        reg = "ax" if size1 == 2 else "al"
        asm_lines.append(f"mov {reg}, [{op_safe}]")
        asm_lines.append(f"imul {reg}, {reg}")
        asm_lines.append("jo overflow_handler")
        asm_lines.append(f"mov [{op_safe}], {reg}")
    else:
        asm_lines.append(f"mov eax, [{op_safe}]")
        asm_lines.append(f"imul eax, eax")
        asm_lines.append("jo overflow_handler")
        asm_lines.append(f"mov [{op_safe}], eax")

def pow(op1, op2):
    op1_safe = safe_name(op1)
    op2_safe = safe_name(op2)
    size1, _ = get_var_size(op1)
    size2, _ = get_var_size(op2)
    from modules.context_manager import var_types as _types
    if _types.get(op1_safe, {}).get('reserved'):
        print(f"Warning: POW using reserved variable {op1}")
    if _types.get(op2_safe, {}).get('reserved'):
        print(f"Warning: POW using reserved variable {op2}")
    if size1 != size2:
        print(f"Warning: POW operand size mismatch {op1}({size1}) vs {op2}({size2})")
    if size1 <= 2:
        reg = "ax" if size1 == 2 else "al"
        asm_lines.append(f"mov {reg}, [{op1_safe}]")
        asm_lines.append(f"mov cx, [{op2_safe}]")
        asm_lines.append(f"mov bx, {reg}")
        asm_lines.append(f"cmp cx, 0")
        asm_lines.append(f"je .pow_done_{op1_safe}")
        asm_lines.append(f"dec cx")
        asm_lines.append(f".pow_loop_{op1_safe}:")
        asm_lines.append(f"imul {reg}, bx")
        asm_lines.append("jo overflow_handler")
        asm_lines.append(f"dec cx")
        asm_lines.append(f"jnz .pow_loop_{op1_safe}")
        asm_lines.append(f".pow_done_{op1_safe}:")
        asm_lines.append(f"mov [{op1_safe}], {reg}")
    else:
        asm_lines.append(f"mov eax, [{op1_safe}]")
        asm_lines.append(f"mov ecx, [{op2_safe}]")
        asm_lines.append(f"mov ebx, eax")
        asm_lines.append(f"cmp ecx, 0")
        asm_lines.append(f"je .pow_done_{op1_safe}")
        asm_lines.append(f"dec ecx")
        asm_lines.append(f".pow_loop_{op1_safe}:")
        asm_lines.append(f"imul eax, ebx")
        asm_lines.append("jo overflow_handler")
        asm_lines.append(f"dec ecx")
        asm_lines.append(f"jnz .pow_loop_{op1_safe}")
        asm_lines.append(f".pow_done_{op1_safe}:")
        asm_lines.append(f"mov [{op1_safe}], eax")

def sin():
    pass

def cos():
    pass

def tan():
    pass

def ctan():
    pass

def asin():
    pass

def acos():
    pass

def factorial():
    pass

def log():
    pass

def log10():
    pass
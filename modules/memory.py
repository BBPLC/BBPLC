"""
Memory management operations for BBPLC.
Provides high-level memory operations: PUSH, POP, MALLOC, REALLOC, FREE, SIZEOF.
"""

from modules.context_manager import variables, var_types, declares, buffers_created, tostr_counter, asm_lines
from modules.bbplctypes import safe_name, get_var_size


def push_value(var_name):
    """Push variable value onto the stack."""
    safe_var = safe_name(var_name)
    size, _ = get_var_size(var_name)

    asm_lines.append(f"; --- PUSH {var_name} ({size} bytes) ---")

    if size == 1:
        asm_lines.append(f"mov al, [{safe_var}]")
        asm_lines.append("push ax")  # push word for byte alignment
    elif size == 2:
        asm_lines.append(f"mov ax, [{safe_var}]")
        asm_lines.append("push ax")
    else:
        asm_lines.append(f"mov eax, [{safe_var}]")
        asm_lines.append("push eax")


def pop_value(var_name):
    """Pop value from stack into variable."""
    safe_var = safe_name(var_name)
    size, _ = get_var_size(var_name)

    asm_lines.append(f"; --- POP {var_name} ({size} bytes) ---")

    if size == 1:
        asm_lines.append("pop ax")  # pop word
        asm_lines.append(f"mov [{safe_var}], al")
    elif size == 2:
        asm_lines.append("pop ax")
        asm_lines.append(f"mov [{safe_var}], ax")
    else:
        asm_lines.append("pop eax")
        asm_lines.append(f"mov [{safe_var}], eax")


def malloc_memory(target_var, size_expr):
    """Allocate memory dynamically."""
    safe_target = safe_name(target_var)

    asm_lines.append(f"; --- MALLOC {target_var}, size={size_expr} ---")

    # For simplicity, we'll use a simple heap simulation
    # In real implementation, this would call system malloc
    try:
        size = int(size_expr)
    except ValueError:
        # If size is a variable, load it
        size_var = safe_name(size_expr)
        asm_lines.append(f"mov eax, [{size_var}]")
        asm_lines.append("push eax")
        asm_lines.append("call malloc")
        asm_lines.append("add esp, 4")
    else:
        # If size is a constant
        asm_lines.append(f"push {size}")
        asm_lines.append("call malloc")
        asm_lines.append("add esp, 4")

    asm_lines.append(f"mov [{safe_target}], eax")

    # Update variable tracking
    if safe_target not in variables:
        variables[safe_target] = None
        declares.append(f"{safe_target}: dd 0")
        var_types[safe_target] = {'size': 4, 'define': 'dd', 'reserved': False}


def realloc_memory(target_var, new_size_expr):
    """Reallocate memory block."""
    safe_target = safe_name(target_var)

    asm_lines.append(f"; --- REALLOC {target_var}, new_size={new_size_expr} ---")

    # Load current pointer
    asm_lines.append(f"push dword [{safe_target}]")

    try:
        new_size = int(new_size_expr)
        asm_lines.append(f"push {new_size}")
    except ValueError:
        size_var = safe_name(new_size_expr)
        asm_lines.append(f"push dword [{size_var}]")

    asm_lines.append("call realloc")
    asm_lines.append("add esp, 8")
    asm_lines.append(f"mov [{safe_target}], eax")


def free_memory(var_name):
    """Free dynamically allocated memory."""
    safe_var = safe_name(var_name)

    asm_lines.append(f"; --- FREE {var_name} ---")

    asm_lines.append(f"push dword [{safe_var}]")
    asm_lines.append("call free")
    asm_lines.append("add esp, 4")

    # Clear the pointer
    asm_lines.append(f"mov dword [{safe_var}], 0")


def get_sizeof(target_var, result_var):
    """Get the size of a variable in bytes."""
    safe_target = safe_name(target_var)
    safe_result = safe_name(result_var)

    size, _ = get_var_size(target_var)

    asm_lines.append(f"; --- SIZEOF {target_var} -> {result_var} ---")
    asm_lines.append(f"mov dword [{safe_result}], {size}")

    # Update result variable tracking
    if safe_result not in variables:
        variables[safe_result] = size
        declares.append(f"{safe_result}: dd {size}")
        var_types[safe_result] = {'size': 4, 'define': 'dd', 'reserved': False}
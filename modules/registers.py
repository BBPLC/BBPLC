"""
Register operations for BBPLC.
Provides high-level register manipulation: LOAD, STORE, ADD, etc.
"""

from modules.context_manager import variables, var_types, declares, buffers_created, tostr_counter, asm_lines
from modules.bbplctypes import safe_name, get_var_size


def reg_operation(register, operation, variable):
    """Perform operation on register with variable, immediate value, or no operand."""
    reg = register.lower()

    # Validate register
    valid_regs = ['eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'esp', 'ebp']
    if reg not in valid_regs:
        print(f"Warning: Invalid register '{register}', using eax")
        reg = 'eax'

    # Check if variable is provided and if it's a number (immediate value)
    if variable and variable.strip():
        try:
            immediate_value = int(variable)
            is_immediate = True
        except ValueError:
            is_immediate = False
        has_operand = True
    else:
        has_operand = False
        is_immediate = False

    asm_lines.append(f"; --- REG {register} {operation} {variable} ---")

    if operation.lower() == 'load':
        if not has_operand:
            print(f"Warning: LOAD operation requires an operand")
            return
        if is_immediate:
            # Load immediate value into register
            asm_lines.append(f"mov {reg}, {immediate_value}")
        else:
            # Load variable value into register
            safe_var = safe_name(variable)
            size, _ = get_var_size(variable)
            if size == 1:
                asm_lines.append(f"mov {reg}, 0")  # Clear register
                asm_lines.append(f"mov {reg[-1]}l, [{safe_var}]")  # Load byte
            elif size == 2:
                asm_lines.append(f"mov {reg}, 0")  # Clear register
                asm_lines.append(f"mov {reg[-1]}x, [{safe_var}]")  # Load word
            else:
                asm_lines.append(f"mov {reg}, [{safe_var}]")  # Load dword

    elif operation.lower() == 'store':
        if not has_operand:
            print(f"Warning: STORE operation requires an operand")
            return
        if is_immediate:
            print(f"Warning: Cannot STORE immediate value {immediate_value}")
            return
        # Store register value to variable
        safe_var = safe_name(variable)
        size, _ = get_var_size(variable)
        if size == 1:
            asm_lines.append(f"mov [{safe_var}], {reg[-1]}l")  # Store byte
        elif size == 2:
            asm_lines.append(f"mov [{safe_var}], {reg[-1]}x")  # Store word
        else:
            asm_lines.append(f"mov [{safe_var}], {reg}")  # Store dword

    elif operation.lower() == 'add':
        if not has_operand:
            print(f"Warning: ADD operation requires an operand")
            return
        if is_immediate:
            # Add immediate value to register
            asm_lines.append(f"add {reg}, {immediate_value}")
        else:
            # Add variable to register
            safe_var = safe_name(variable)
            size, _ = get_var_size(variable)
            if size == 1:
                asm_lines.append(f"add {reg[-1]}l, [{safe_var}]")
            elif size == 2:
                asm_lines.append(f"add {reg[-1]}x, [{safe_var}]")
            else:
                asm_lines.append(f"add {reg}, [{safe_var}]")

    elif operation.lower() == 'sub':
        if not has_operand:
            print(f"Warning: SUB operation requires an operand")
            return
        if is_immediate:
            # Subtract immediate value from register
            asm_lines.append(f"sub {reg}, {immediate_value}")
        else:
            # Subtract variable from register
            safe_var = safe_name(variable)
            size, _ = get_var_size(variable)
            if size == 1:
                asm_lines.append(f"sub {reg[-1]}l, [{safe_var}]")
            elif size == 2:
                asm_lines.append(f"sub {reg[-1]}x, [{safe_var}]")
            else:
                asm_lines.append(f"sub {reg}, [{safe_var}]")

    elif operation.lower() == 'mul':
        if not has_operand:
            print(f"Warning: MUL operation requires an operand")
            return
        if is_immediate:
            # Multiply register by immediate value
            asm_lines.append(f"imul {reg}, {immediate_value}")
        else:
            # Multiply register by variable
            safe_var = safe_name(variable)
            size, _ = get_var_size(variable)
            if size == 1:
                asm_lines.append(f"mov al, {reg[-1]}l")
                asm_lines.append(f"mul byte [{safe_var}]")
                asm_lines.append(f"mov {reg[-1]}l, al")
            elif size == 2:
                asm_lines.append(f"mov ax, {reg[-1]}x")
                asm_lines.append(f"mul word [{safe_var}]")
                asm_lines.append(f"mov {reg[-1]}x, ax")
            else:
                asm_lines.append(f"mul dword [{safe_var}]")

    elif operation.lower() == 'div':
        if not has_operand:
            print(f"Warning: DIV operation requires an operand")
            return
        if is_immediate:
            # Divide register by immediate value
            asm_lines.append(f"mov ecx, {immediate_value}")
            asm_lines.append(f"mov eax, {reg}")
            asm_lines.append("xor edx, edx")
            asm_lines.append("div ecx")
            asm_lines.append(f"mov {reg}, eax")
        else:
            # Divide register by variable
            safe_var = safe_name(variable)
            size, _ = get_var_size(variable)
            if size == 1:
                asm_lines.append(f"mov al, {reg[-1]}l")
                asm_lines.append("xor ah, ah")
                asm_lines.append(f"div byte [{safe_var}]")
                asm_lines.append(f"mov {reg[-1]}l, al")
            elif size == 2:
                asm_lines.append(f"mov ax, {reg[-1]}x")
                asm_lines.append("xor dx, dx")
                asm_lines.append(f"div word [{safe_var}]")
                asm_lines.append(f"mov {reg[-1]}x, ax")
            else:
                asm_lines.append(f"mov eax, {reg}")
                asm_lines.append("xor edx, edx")
                asm_lines.append(f"div dword [{safe_var}]")
                asm_lines.append(f"mov {reg}, eax")

    elif operation.lower() == 'clear':
        # Clear register
        asm_lines.append(f"xor {reg}, {reg}")

    elif operation.lower() == 'inc':
        # Increment register
        asm_lines.append(f"inc {reg}")

    elif operation.lower() == 'dec':
        # Decrement register
        asm_lines.append(f"dec {reg}")

    else:
        print(f"Warning: Unknown register operation '{operation}'")
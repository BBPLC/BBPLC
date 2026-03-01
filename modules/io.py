from modules.context_manager import variables, var_types, declares, buffers_created, tostr_counter, asm_lines
from modules.bbplctypes import safe_name, get_var_size, toint

def print_var(name):
    original_name = name
    safe_name_var = safe_name(name)
    asm_lines.append(f"; --- PRINT {original_name} ---")
    
    if original_name in tostr_counter and tostr_counter[original_name] > 0:
        count = tostr_counter[original_name] - 1
        buf = safe_name(f"{original_name}_str_{count}")
        length_var = safe_name(f"{buf}_len")
        ptr_var = safe_name(f"{buf}_ptr")
        
        asm_lines.append("mov eax, 4")
        asm_lines.append("mov ebx, 1")
        asm_lines.append(f"mov ecx, [{ptr_var}]")
        asm_lines.append(f"mov edx, [{length_var}]")
        asm_lines.append("int 0x80")
    else:
        meta = var_types.get(safe_name_var, {})
        is_reserved = meta.get('reserved', False)
        size = meta.get('size', 1)
        
        if is_reserved:
            asm_lines.append(f"lea esi, [{safe_name_var}]")
            asm_lines.append("xor ecx, ecx")
            asm_lines.append(f".print_len_{safe_name_var}:")
            asm_lines.append(f"cmp byte [esi + ecx], 0")
            asm_lines.append(f"je .print_done_{safe_name_var}")
            asm_lines.append(f"inc ecx")
            asm_lines.append(f"cmp ecx, {size}")
            asm_lines.append(f"je .print_done_{safe_name_var}")
            asm_lines.append(f"jmp .print_len_{safe_name_var}")
            asm_lines.append(f".print_done_{safe_name_var}:")
            asm_lines.append("mov edx, ecx")
            asm_lines.append("mov eax, 4")
            asm_lines.append("mov ebx, 1")
            asm_lines.append(f"lea ecx, [{safe_name_var}]")
            asm_lines.append("int 0x80")
        else:
            value = variables.get(safe_name_var)
            is_string = isinstance(value, str)

            if is_string:
                if ',' in value:
                    bytes_list = [b.strip() for b in value.split(',') if b.strip()]
                    if bytes_list and bytes_list[-1] == '0':
                        length = len(bytes_list) - 1
                    else:
                        length = len(bytes_list)
                else:
                    length = len(value)
                asm_lines.append("mov eax, 4")
                asm_lines.append("mov ebx, 1")
                asm_lines.append(f"lea ecx, [{safe_name_var}]")
                asm_lines.append(f"mov edx, {length}")
                asm_lines.append("int 0x80")
            else:
                print(f"Warning: PRINT of non-string variable '{original_name}' -- use TOSTR to convert")
                asm_lines.append(f"; skip PRINT of {original_name} (not a string)")

def read_var(name):
    original_name = name
    safe_name_var = safe_name(name)

    size, define = get_var_size(name)

    if safe_name_var not in variables:
        if size == 4:
            size = 256
            define = 'db'
        variables[safe_name_var] = None
        declares.append(f"{safe_name_var} rb {size}")
        var_types[safe_name_var] = {'size': size, 'define': define, 'reserved': True}

    asm_lines.append(f"; --- READ {original_name} ({size} bytes) ---")
    asm_lines.append("mov eax, 3")
    asm_lines.append("mov ebx, 0")
    asm_lines.append(f"lea ecx, [{safe_name_var}]")
    asm_lines.append(f"mov edx, {size}")
    asm_lines.append("int 0x80")

    asm_lines.append(f"; null‑terminate the input")
    asm_lines.append("cmp eax, 0")
    asm_lines.append(f"jle .read_done_{safe_name_var}")
    asm_lines.append(f"mov byte [{safe_name_var} + eax], 0")
    asm_lines.append(f".read_done_{safe_name_var}:")

    meta = var_types.get(safe_name_var, {})
    if not meta.get('reserved', False):
        asm_lines.append(f"; parse decimal string in {original_name} → integer")
        asm_lines.append(f"lea esi, [{safe_name_var}]")
        asm_lines.append("xor eax, eax")
        asm_lines.append("xor ecx, ecx")
        asm_lines.append(f".read_to_int_loop_{safe_name_var}:")
        asm_lines.append("mov bl, [esi + ecx]")
        asm_lines.append("cmp bl, 0")
        asm_lines.append(f"je .read_to_int_done_{safe_name_var}")
        asm_lines.append("sub bl, '0'")
        asm_lines.append("cmp bl, 9")
        asm_lines.append(f"ja .read_to_int_done_{safe_name_var}")
        asm_lines.append("imul eax, eax, 10")
        asm_lines.append("add eax, ebx")
        asm_lines.append("inc ecx")
        asm_lines.append(f"jmp .read_to_int_loop_{safe_name_var}")
        asm_lines.append(f".read_to_int_done_{safe_name_var}:")
        size = meta.get('size', 4)
        if size == 1:
            asm_lines.append(f"mov [{safe_name_var}], al")
        elif size == 2:
            asm_lines.append(f"mov [{safe_name_var}], ax")
        else:
            asm_lines.append(f"mov [{safe_name_var}], eax")

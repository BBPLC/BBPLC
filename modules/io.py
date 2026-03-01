from modules.context_manager import variables, declares, buffers_created, tostr_counter, asm_lines
from modules.bbplctypes import safe_name, get_var_size

def print_var(name):
    original_name = name
    safe_name_var = safe_name(name)
    asm_lines.append(f"; --- PRINT {original_name} ---")
    value = variables.get(safe_name_var)
    is_string = isinstance(value, str) and ',' in value
    
    if is_string:
        bytes_list = [b.strip() for b in value.split(',') if b.strip()]
        length = len(bytes_list)
        asm_lines.append("mov eax, 4")
        asm_lines.append("mov ebx, 1")
        asm_lines.append(f"lea ecx, [{safe_name_var}]")
        asm_lines.append(f"mov edx, {length}")
        asm_lines.append("int 0x80")
    else:
        if original_name in tostr_counter and tostr_counter[original_name] > 0:
            count = tostr_counter[original_name] - 1
        else:
            count = 0
        
        buf = safe_name(f"{original_name}_str_{count}")
        length_var = safe_name(f"{buf}_len")
        ptr_var = safe_name(f"{buf}_ptr")
        
        asm_lines.append("mov eax, 4")
        asm_lines.append("mov ebx, 1")
        asm_lines.append(f"mov ecx, [{ptr_var}]")
        asm_lines.append(f"mov edx, [{length_var}]")
        asm_lines.append("int 0x80")

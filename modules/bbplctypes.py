import re
from modules.context_manager import variables, declares, buffers_created, tostr_counter, asm_lines

DATA_DEFINE = {1:"db", 2:"dw", 4:"dd", 6:"dp", 8:"dq", 10:"dt"}
DATA_RESERVE = {1:"rb", 2:"rw", 4:"rd", 6:"rf", 8:"rq", 10:"rt"}
RESERVED_NAMES = {"str", "eax", "ebx", "ecx", "edx", "esi", "edi"}

def safe_name(name):
    return f"var_{name}" if name in RESERVED_NAMES else name

def get_var_size(name):
    value = variables.get(name)
    if isinstance(value, int):
        size = 4
    elif isinstance(value, str) and ',' in value:
        size = len([b for b in value.split(',') if b.strip()])
    else:
        size = 4
    define = DATA_DEFINE.get(size, "dd")
    return size, define

def parse_declare(line):
    m = re.match(r'DECLARE\s+(\w+)\s+(\w+)\s*=\s*(.+)', line)
    if not m:
        return None, None, None
    var_type, var_name, var_value = m.groups()
    var_value = var_value.strip()
    if var_value.startswith("'") and var_value.endswith("'"):
        var_value = var_value[1:-1]
        var_value = ', '.join(str(ord(c)) for c in var_value) + ", 0"
        var_type = "DB"
    return var_type, var_name, var_value

def declare(type_or_size, name, value=None, reserve=False):
    name = safe_name(name)
    if isinstance(type_or_size, int):
        size = type_or_size
        type_define = DATA_RESERVE[size] if reserve else DATA_DEFINE[size]
    else:
        type_define = type_or_size.upper()
    variables[name] = value if value is not None else 0
    if reserve or value is None:
        declares.append(f"{name}: {type_define} {10 if type_define.startswith('r') else ''} dup(0) ; reserved")
    else:
        declares.append(f"{name}: {type_define} {value}")

def tostr(name):
    size, define = get_var_size(name)
    count = tostr_counter.get(name, 0)
    tostr_counter[name] = count + 1

    buf = safe_name(f"{name}_str_{count}")
    len_var = safe_name(f"{buf}_len")
    ptr_var = safe_name(f"{buf}_ptr")

    if buf not in variables:
        declares.append(f"{buf}: times 20 db 0 ; buffer for {name}")
        declares.append(f"{len_var}: dd 0 ; length of {buf}")
        declares.append(f"{ptr_var}: dd 0 ; pointer to start of {buf}")
        variables[buf] = "tostr_buffer"
        variables[len_var] = 0
        variables[ptr_var] = 0

    buffers_created.setdefault(name, []).append(count)

    asm_lines.append(f"; --- TOSTR {name} ({define}) → {buf} ---")
    if size == 1:
        asm_lines.append(f"movzx eax, byte [{safe_name(name)}]")
    elif size == 2:
        asm_lines.append(f"movzx eax, word [{safe_name(name)}]")
    else:
        asm_lines.append(f"mov eax, [{safe_name(name)}]")

    asm_lines.append(f"lea edi, [{buf} + 19]")
    asm_lines.append(f"mov byte [edi], 0")
    asm_lines.append(f"xor ecx, ecx")
    asm_lines.append(f".tostr_loop_{name}_{count}:")
    asm_lines.append(f"xor edx, edx")
    asm_lines.append(f"mov ebx, 10")
    asm_lines.append(f"div ebx")
    asm_lines.append(f"add dl, '0'")
    asm_lines.append(f"dec edi")
    asm_lines.append(f"mov [edi], dl")
    asm_lines.append(f"inc ecx")
    asm_lines.append(f"test eax, eax")
    asm_lines.append(f"jnz .tostr_loop_{name}_{count}")
    asm_lines.append(f"mov [{len_var}], ecx")
    asm_lines.append(f"mov [{ptr_var}], edi")

def toint(name):
    if name not in buffers_created or not buffers_created[name]:
        print(f"Warning: TOINT {name} без TOSTR — используем {name}_str_0")
        count = 0
    else:
        count = max(buffers_created[name])

    buf = safe_name(f"{name}_str_{count}")
    ptr_var = safe_name(f"{buf}_ptr")
    len_var = safe_name(f"{buf}_len")
    size, _ = get_var_size(name)

    asm_lines.append(f"; --- TOINT {name} ({size*8}bit) ← {buf} ---")
    
    asm_lines.append(f"cmp dword [{len_var}], 0")
    asm_lines.append(f"je .toint_skip_{name}_{count}")

    asm_lines.append(f"mov esi, [{ptr_var}]")
    asm_lines.append("xor eax, eax")
    asm_lines.append("xor ecx, ecx")

    asm_lines.append(f".toint_loop_{name}_{count}:")
    asm_lines.append("movzx ebx, byte [esi]")
    asm_lines.append("cmp bl, 0")
    asm_lines.append(f"je .toint_done_{name}_{count}")
    asm_lines.append("sub bl, '0'")
    asm_lines.append("cmp bl, 9")
    asm_lines.append(f"ja .toint_done_{name}_{count}")
    asm_lines.append("imul eax, eax, 10")
    asm_lines.append("add eax, ebx")
    asm_lines.append("inc esi")
    asm_lines.append("inc ecx")
    asm_lines.append(f"jmp .toint_loop_{name}_{count}")

    asm_lines.append(f".toint_done_{name}_{count}:")
    if size == 1:
        asm_lines.append(f"mov [{safe_name(name)}], al")
    elif size == 2:
        asm_lines.append(f"mov [{safe_name(name)}], ax")
    else:
        asm_lines.append(f"mov [{safe_name(name)}], eax")

    asm_lines.append(f".toint_skip_{name}_{count}:")


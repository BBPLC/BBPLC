import re
from modules.context_manager import variables, var_types, declares, buffers_created, tostr_counter, asm_lines

DATA_DEFINE = {1:"db", 2:"dw", 4:"dd", 6:"dp", 8:"dq", 10:"dt"}
DATA_RESERVE = {1:"rb", 2:"rw", 4:"rd", 6:"rf", 8:"rq", 10:"rt"}
RESERVED_NAMES = {"str", "eax", "ebx", "ecx", "edx", "esi", "edi"}

def safe_name(name):
    return f"var_{name}" if name in RESERVED_NAMES else name

def get_var_size(name):
    key = safe_name(name)
    meta = var_types.get(key)
    if meta:
        size = meta.get('size', 4)
        define = meta.get('define', DATA_DEFINE.get(size, "dd"))
        return size, define

    value = variables.get(key)
    if value is None:
        print(f"Warning: variable '{name}' used before declaration, assuming 32-bit")
        size = 4
    elif isinstance(value, int):
        size = 4
    elif isinstance(value, str) and ',' in value:
        size = len([b for b in value.split(',') if b.strip()])
    else:
        size = 4
    define = DATA_DEFINE.get(size, "dd")
    return size, define

def parse_declare(line):
    m = re.match(r'DECLARE\s+(RESERVE\s+)?(\w+)\s+(\w+)(?:\s*=\s*(.+))?', line)
    if not m:
        return None, None, None, False
    reserve_flag = bool(m.group(1))
    var_type = m.group(2)
    var_name = m.group(3)
    var_value = m.group(4)
    if var_value is not None:
        var_value = var_value.strip()
        if (var_value.startswith("'") and var_value.endswith("'")) or \
           (var_value.startswith('"') and var_value.endswith('"')):
            var_value = var_value[1:-1]
            var_value = ', '.join(str(ord(c)) for c in var_value) + ", 0"
            var_type = "DB"
    return var_type, var_name, var_value, reserve_flag

def declare(type_or_size, name, value=None, reserve=False):
    name = safe_name(name)
    if isinstance(type_or_size, int):
        base_size = type_or_size
        base_define = DATA_RESERVE[base_size] if reserve else DATA_DEFINE[base_size]
    else:
        base_define = type_or_size.upper()
        base_size = next((s for s,d in DATA_RESERVE.items() if d == base_define.lower()), None)
        if base_size is None:
            base_size = next((s for s,d in DATA_DEFINE.items() if d == base_define.lower()), 4)
    reserve_flag = reserve or base_define.lower().startswith('r')

    size = base_size
    if reserve_flag and value is None:
        size = 4
    elif reserve_flag and value is not None:
        try:
            cnt = int(value)
            size = cnt
        except ValueError:
            pass

    if isinstance(value, str) and ',' in value and not reserve_flag:
        count = len([b for b in value.split(',') if b.strip()])
        size = count
        base_define = DATA_DEFINE.get(size, DATA_DEFINE.get(1))
    type_define = base_define

    var_types[name] = {'size': size, 'define': type_define, 'reserved': reserve_flag}
    variables[name] = value if value is not None else 0

    if value is not None:
        if isinstance(value, int):
            bits = size * 8
            maxv = (1 << (bits - 1)) - 1
            minv = -(1 << (bits - 1))
            if not (minv <= value <= maxv):
                print(f"Warning: initial value {value} does not fit in {bits}-bit type {type_define}")
        elif isinstance(value, str) and ',' in value:
            count = len([b for b in value.split(',') if b.strip()])
            if count > size:
                print(f"Warning: string initializer for {name} too long ({count} bytes) for {size}-byte type")

    if reserve_flag or value is None:
        if reserve_flag and value is not None and not isinstance(value, str):
            pass
        if reserve_flag and value is not None and not isinstance(value, str):
            pass
        if reserve_flag and value is not None and isinstance(value, str) and not value.isdigit():
            print(f"Warning: initial value for reserved variable {name} ignored")
        reserve_def = DATA_RESERVE.get(base_size)
        count = size
        if reserve_def:
            declares.append(f"{name}: {reserve_def} {count}")
        else:
            declares.append(f"{name}: db {count} ; reserved")
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
    safe = safe_name(name)

    asm_lines.append(f"mov eax, [{safe}]")
    asm_lines.append(f"lea edi, [{buf}+19]")
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
    asm_lines.append(f"xor eax, eax")
    asm_lines.append(f"xor ecx, ecx")

    asm_lines.append(f".toint_loop_{name}_{count}:")
    asm_lines.append(f"movzx ebx, byte [esi]")
    asm_lines.append(f"cmp bl, 0")
    asm_lines.append(f"je .toint_done_{name}_{count}")
    asm_lines.append(f"sub bl, '0'")
    asm_lines.append(f"cmp bl, 9")
    asm_lines.append(f"ja .toint_done_{name}_{count}")
    asm_lines.append(f"imul eax, eax, 10")
    asm_lines.append(f"add eax, ebx")
    asm_lines.append(f"inc esi")
    asm_lines.append(f"inc ecx")
    asm_lines.append(f"jmp .toint_loop_{name}_{count}")

    asm_lines.append(f".toint_done_{name}_{count}:")
    if size == 1:
        asm_lines.append(f"mov [{safe_name(name)}], al")
    elif size == 2:
        asm_lines.append(f"mov [{safe_name(name)}], ax")
    else:
        asm_lines.append(f"mov [{safe_name(name)}], eax")

    asm_lines.append(f".toint_skip_{name}_{count}:")

def mov(dest, src):
    dest_name = safe_name(dest)

    try:
        value = int(src)
        asm_lines.append(f"mov dword [{dest_name}], {value}")
        return
    except ValueError:
        pass

    if (src.startswith('"') and src.endswith('"')) or (src.startswith("'") and src.endswith("'")):
        string_literal = src[1:-1]
        count = tostr_counter.get(string_literal, 0)
        var_name = f"{safe_name('str')}_{count}"
        tostr_counter[string_literal] = count + 1

        declares.append(f"{var_name}: db {', '.join(str(ord(c)) for c in string_literal)}, 0")
        asm_lines.append(f"lea eax, [{var_name}]")
        asm_lines.append(f"mov [{dest_name}], eax")
        return

    src_name = safe_name(src)
    if src_name not in variables:
        print(f"Warning: переменная '{src}' не объявлена, создаем как 0")
        declare(4, src_name, 0)
    asm_lines.append(f"mov eax, [{src_name}]")
    asm_lines.append(f"mov [{dest_name}], eax")

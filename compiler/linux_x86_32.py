from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Type, List, Optional

# ---------------------------------------------------------------------------
# runtime support state and helpers previously split across modules; now all
# live here so the backend is self-contained.  These globals are reset at the
# start of each code generation run.
# ---------------------------------------------------------------------------

variables: Dict[str, Optional[object]] = {}
var_types: Dict[str, Dict[str, object]] = {}
declares: List[str] = []
buffers_created: Dict[str, List[int]] = {}
tostr_counter: Dict[str, int] = {}
asm_lines: List[str] = []


# *** type handling / declaration helpers ***

DATA_DEFINE = {1: "db", 2: "dw", 4: "dd", 6: "dp", 8: "dq", 10: "dt"}
DATA_RESERVE = {1: "rb", 2: "rw", 4: "rd", 6: "rf", 8: "rq", 10: "rt"}
RESERVED_NAMES = {"str", "eax", "ebx", "ecx", "edx", "esi", "edi", "label"}


def safe_name(name: str) -> str:
    # convert dots used for struct-like fields to underscores
    clean = name.replace('.', '_')
    return f"var_{clean}" if clean in RESERVED_NAMES else clean


def get_var_size(name: str):
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


def parse_declare(line: str):
    import re

    # allow dotted variable names (e.g. person.age)
    m = re.match(r'DECLARE\s+(RESERVE\s+)?(\w+)\s+([\w\.]+)(?:\s*=\s*(.+))?', line)
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


def declare(type_or_size, name: str, value=None, reserve=False):
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
        # Keep using 'db' for string data, don't re-map based on size
        if base_define.lower() in ('db', 'dw', 'dd', 'dp', 'dq', 'dt'):
            # String data should always use 'db', not remap to other sizes
            base_define = 'db'
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


# helper previously in bbplctypes; moved here so codegen is self-contained

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


def tostr(name: str):
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
    lbl = f"tostr_loop_{safe}_{count}"

    asm_lines.append(f"mov eax, [{safe}]")
    asm_lines.append(f"lea edi, [{buf}+19]")
    asm_lines.append(f"mov byte [edi], 0")
    asm_lines.append(f"xor ecx, ecx")

    asm_lines.append(f".{lbl}:")
    asm_lines.append(f"xor edx, edx")
    asm_lines.append(f"mov ebx, 10")
    asm_lines.append(f"div ebx")
    asm_lines.append(f"add dl, '0'")
    asm_lines.append(f"dec edi")
    asm_lines.append(f"mov [edi], dl")
    asm_lines.append(f"inc ecx")
    asm_lines.append(f"test eax, eax")
    asm_lines.append(f"jnz .{lbl}")
    asm_lines.append(f"mov [{len_var}], ecx")
    asm_lines.append(f"mov [{ptr_var}], edi")


def toint(name: str):
    if name not in buffers_created or not buffers_created[name]:
        print(f"Warning: TOINT {name} без TOSTР — используем {name}_str_0")
        count = 0
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
    else:
        count = max(buffers_created[name])

    buf = safe_name(f"{name}_str_{count}")
    ptr_var = safe_name(f"{buf}_ptr")
    len_var = safe_name(f"{buf}_len")
    size, _ = get_var_size(name)

    asm_lines.append(f"; --- TOINT {name} ({size*8}bit) ← {buf} ---")
    skip_lbl = f"toint_skip_{safe_name(name)}_{count}"
    asm_lines.append(f"cmp dword [{len_var}], 0")
    asm_lines.append(f"je .{skip_lbl}")

    asm_lines.append(f"mov esi, [{ptr_var}]")
    asm_lines.append(f"xor eax, eax")
    asm_lines.append(f"xor ecx, ecx")

    lbl = f"toint_loop_{safe_name(name)}_{count}"
    done_lbl = lbl.replace('loop','done')
    asm_lines.append(f".{lbl}:")
    asm_lines.append(f"movzx ebx, byte [esi]")
    asm_lines.append(f"cmp bl, 0")
    asm_lines.append(f"je .{done_lbl}")
    asm_lines.append(f"sub bl, '0'")
    asm_lines.append(f"cmp bl, 9")
    asm_lines.append(f"ja .{done_lbl}")
    asm_lines.append(f"imul eax, eax, 10")
    asm_lines.append(f"add eax, ebx")
    asm_lines.append(f"inc esi")
    asm_lines.append(f"inc ecx")
    asm_lines.append(f"jmp .{lbl}")

    asm_lines.append(f".{done_lbl}:")
    if size == 1:
        asm_lines.append(f"mov [{safe_name(name)}], al")
    elif size == 2:
        asm_lines.append(f"mov [{safe_name(name)}], ax")
    else:
        asm_lines.append(f"mov [{safe_name(name)}], eax")
    asm_lines.append(f".{skip_lbl}:")


# *** arithmetic helpers ***

def add(left, right):
    safe_left = safe_name(left)
    asm_lines.append(f"; --- ADD {left} {right} ---")
    try:
        imm = int(right)
        asm_lines.append(f"add dword [{safe_left}], {imm}")
    except ValueError:
        safe_right = safe_name(right)
        asm_lines.append(f"mov eax, [{safe_right}]")
        asm_lines.append(f"add [{safe_left}], eax")


def sub(left, right):
    safe_left = safe_name(left)
    asm_lines.append(f"; --- SUB {left} {right} ---")
    try:
        imm = int(right)
        asm_lines.append(f"sub dword [{safe_left}], {imm}")
    except ValueError:
        safe_right = safe_name(right)
        asm_lines.append(f"mov eax, [{safe_right}]")
        asm_lines.append(f"sub [{safe_left}], eax")


def mul(left, right):
    safe_left = safe_name(left)
    asm_lines.append(f"; --- MUL {left} {right} ---")
    try:
        imm = int(right)
        asm_lines.append(f"mov eax, [{safe_left}]")
        asm_lines.append(f"imul eax, {imm}")
        asm_lines.append(f"mov [{safe_left}], eax")
    except ValueError:
        safe_right = safe_name(right)
        asm_lines.append(f"mov eax, [{safe_left}]")
        asm_lines.append(f"imul eax, [{safe_right}]")
        asm_lines.append(f"mov [{safe_left}], eax")


def div(left, right):
    safe_left = safe_name(left)
    asm_lines.append(f"; --- DIV {left} {right} ---")
    try:
        imm = int(right)
        asm_lines.append(f"mov eax, [{safe_left}]")
        asm_lines.append(f"cdq")
        asm_lines.append(f"idiv {imm}")
        asm_lines.append(f"mov [{safe_left}], eax")
    except ValueError:
        safe_right = safe_name(right)
        asm_lines.append(f"mov eax, [{safe_left}]")
        asm_lines.append(f"cdq")
        asm_lines.append(f"idiv dword [{safe_right}]")
        asm_lines.append(f"mov [{safe_left}], eax")


def sqr(var):
    safe = safe_name(var)
    asm_lines.append(f"; --- SQR {var} ---")
    asm_lines.append(f"mov eax, [{safe}]")
    asm_lines.append(f"imul eax, eax")
    asm_lines.append(f"mov [{safe}], eax")


def pow(left, right):
    safe_left = safe_name(left)
    asm_lines.append(f"; --- POW {left} {right} ---")
    # compute left = left ** right by repeated multiplication
    asm_lines.append(f"mov eax, [{safe_left}]")
    asm_lines.append(f"mov ebx, eax        ; base")
    # load exponent into ecx
    try:
        exp = int(right)
        asm_lines.append(f"mov ecx, {exp}")
    except ValueError:
        safe_right = safe_name(right)
        asm_lines.append(f"mov ecx, [{safe_right}]")
    asm_lines.append(f"mov edx, 1          ; result")
    asm_lines.append(f".pow_loop_{safe_left}:")
    asm_lines.append(f"cmp ecx, 0")
    asm_lines.append(f"je .pow_done_{safe_left}")
    asm_lines.append(f"imul edx, eax")
    asm_lines.append(f"dec ecx")
    asm_lines.append(f"jmp .pow_loop_{safe_left}")
    asm_lines.append(f".pow_done_{safe_left}:")
    asm_lines.append(f"mov [{safe_left}], edx")


def print_var(var):
    safe = safe_name(var)
    size, define = get_var_size(var)
    asm_lines.append(f"; --- PRINT {var} ---")
    # if this looks like a byte string (define db), print as characters
    if define.lower() == 'db':
        # iterate until zero
        asm_lines.append(f"mov esi, {safe}")
        asm_lines.append(f".print_loop_{safe}:")
        asm_lines.append(f"mov al, [esi]")
        asm_lines.append(f"cmp al, 0")
        asm_lines.append(f"je .print_done_{safe}")
        asm_lines.append(f"mov eax, 4")
        asm_lines.append(f"mov ebx, 1")
        asm_lines.append(f"mov ecx, esi")
        asm_lines.append(f"mov edx, 1")
        asm_lines.append(f"int 0x80")
        asm_lines.append(f"inc esi")
        asm_lines.append(f"jmp .print_loop_{safe}")
        asm_lines.append(f".print_done_{safe}:")
    else:
        # treat as integer, convert and print
        tostr(var)
        count = max(buffers_created.get(var, [0]))
        buf = safe_name(f"{var}_str_{count}")
        len_var = safe_name(f"{buf}_len")
        ptr_var = safe_name(f"{buf}_ptr")
        asm_lines.append(f"mov ecx, [{ptr_var}]")
        asm_lines.append(f"mov edx, [{len_var}]")
        asm_lines.append(f"mov ebx, 1")
        asm_lines.append(f"mov eax, 4")
        asm_lines.append(f"int 0x80")


def read_var(var):
    safe = safe_name(var)
    size, _ = get_var_size(var)
    asm_lines.append(f"; --- READ {var} ---")
    asm_lines.append(f"mov eax, 3")
    asm_lines.append(f"mov ebx, 0")
    asm_lines.append(f"lea ecx, [{safe}]")
    asm_lines.append(f"mov edx, {size}")
    asm_lines.append(f"int 0x80")


def prtln():
    asm_lines.append("; --- PRTLN ---")
    # ensure newline constant exists
    if 'newline_char' not in variables:
        declares.append("newline_char: db 10")
        variables['newline_char'] = None
    # simple newline via syscall
    asm_lines.append("mov eax, 4")
    asm_lines.append("mov ebx, 1")
    asm_lines.append("mov ecx, newline_char")
    asm_lines.append("mov edx, 1")
    asm_lines.append("int 0x80")


def push_value(var):
    asm_lines.append(f"; --- PUSH {var} ---")
    asm_lines.append(f"push dword [{safe_name(var)}]")


def pop_value(var):
    asm_lines.append(f"; --- POP {var} ---")
    asm_lines.append(f"pop dword [{safe_name(var)}]")

# --- string helpers ---

def str_concat(dest, src):
    """Append src string to dest buffer (null-terminated)."""
    safe_dest = safe_name(dest)
    try:
        # src may be literal like "..."
        if src.startswith('"') or src.startswith("'"):
            literal = src[1:-1]
            count = len(literal)
            asm_lines.append(f"; --- CONCAT {dest} += {literal} ---")
            # find end of dest
            asm_lines.append(f"mov esi, {safe_dest}")
            asm_lines.append(f".concat_find_{safe_dest}:")
            asm_lines.append(f"cmp byte [esi], 0")
            asm_lines.append(f"je .concat_copy_{safe_dest}")
            asm_lines.append(f"inc esi")
            asm_lines.append(f"jmp .concat_find_{safe_dest}")
            asm_lines.append(f".concat_copy_{safe_dest}:")
            for ch in literal:
                asm_lines.append(f"mov byte [esi], '{ch}'")
                asm_lines.append("inc esi")
            asm_lines.append("mov byte [esi], 0")
            return
    except Exception:
        pass
    # else src is variable name
    safe_src = safe_name(src)
    asm_lines.append(f"; --- CONCAT {dest} += {src} ---")
    # compute end of dest
    asm_lines.append(f"mov esi, {safe_dest}")
    asm_lines.append(f".concat_find_{safe_dest}:")
    asm_lines.append(f"cmp byte [esi], 0")
    asm_lines.append(f"je .concat_copy_{safe_dest}")
    asm_lines.append(f"inc esi")
    asm_lines.append(f"jmp .concat_find_{safe_dest}")
    asm_lines.append(f".concat_copy_{safe_dest}:")
    # copy from src until null
    asm_lines.append(f"mov edi, {safe_src}")
    asm_lines.append(f".concat_loop_{safe_dest}:")
    asm_lines.append(f"mov al, [edi]")
    asm_lines.append(f"cmp al, 0")
    asm_lines.append(f"je .concat_done_{safe_dest}")
    asm_lines.append(f"mov [esi], al")
    asm_lines.append(f"inc esi")
    asm_lines.append(f"inc edi")
    asm_lines.append(f"jmp .concat_loop_{safe_dest}")
    asm_lines.append(f".concat_done_{safe_dest}:")
    asm_lines.append(f"mov byte [esi], 0")


def str_length(src, result):
    safe_src = safe_name(src)
    safe_res = safe_name(result)
    asm_lines.append(f"; --- LENGTH {src} -> {result} ---")
    asm_lines.append(f"mov ecx, 0")
    asm_lines.append(f"mov esi, {safe_src}")
    asm_lines.append(f".len_loop_{safe_src}:")
    asm_lines.append(f"cmp byte [esi], 0")
    asm_lines.append(f"je .len_done_{safe_src}")
    asm_lines.append(f"inc esi")
    asm_lines.append(f"inc ecx")
    asm_lines.append(f"jmp .len_loop_{safe_src}")
    asm_lines.append(f".len_done_{safe_src}:")
    asm_lines.append(f"mov [{safe_res}], ecx")


def str_substr(dest, src, start, length):
    safe_dest = safe_name(dest)
    safe_src = safe_name(src)
    asm_lines.append(f"; --- SUBSTR {dest} = {src}[{start}:{length}] ---")
    # only support numeric start/length (immediate or variable)
    # for simplicity we'll implement naive loop
    # move src pointer to start
    asm_lines.append(f"mov esi, {safe_src}")
    try:
        istart = int(start)
        asm_lines.append(f"add esi, {istart}")
    except ValueError:
        asm_lines.append(f"mov eax, [{safe_name(start)}]")
        asm_lines.append(f"add esi, eax")
    # copy length chars
    asm_lines.append(f"mov ecx, 0")
    try:
        ilen = int(length)
        asm_lines.append(f"mov ecx, {ilen}")
    except ValueError:
        asm_lines.append(f"mov ecx, [{safe_name(length)}]")
    asm_lines.append(f"mov edi, {safe_dest}")
    asm_lines.append(f".substr_loop_{safe_dest}:")
    asm_lines.append(f"cmp ecx, 0")
    asm_lines.append(f"je .substr_done_{safe_dest}")
    asm_lines.append(f"mov al, [esi]")
    asm_lines.append(f"mov [edi], al")
    asm_lines.append(f"inc esi")
    asm_lines.append(f"inc edi")
    asm_lines.append(f"dec ecx")
    asm_lines.append(f"jmp .substr_loop_{safe_dest}")
    asm_lines.append(f".substr_done_{safe_dest}:")
    asm_lines.append(f"mov byte [edi], 0")


def str_index(dest, src, index):
    safe_dest = safe_name(dest)
    safe_src = safe_name(src)
    asm_lines.append(f"; --- INDEX {dest} = {src}[{index}] ---")
    asm_lines.append(f"mov esi, {safe_src}")
    # advance to index
    try:
        idx = int(index)
        asm_lines.append(f"add esi, {idx}")
    except ValueError:
        asm_lines.append(f"mov eax, [{safe_name(index)}]")
        asm_lines.append(f"add esi, eax")
    asm_lines.append(f"mov al, [esi]")
    asm_lines.append(f"mov [{safe_dest}], eax")

# --- file helpers ---

def open_file(filename_expr, result_var):
    safe_res = safe_name(result_var)
    asm_lines.append(f"; --- OPEN {filename_expr} -> {result_var} ---")
    # filename_expr may be literal or variable
    if filename_expr.startswith('"') or filename_expr.startswith("'"):
        # create temp variable for filename
        tmp = f"_fname_{len(declares)}"
        declares.append(f"{tmp}: db {', '.join(str(ord(c)) for c in filename_expr[1:-1])},0")
        asm_lines.append(f"lea ebx, [{tmp}]")
    else:
        asm_lines.append(f"lea ebx, [{safe_name(filename_expr)}]")
    asm_lines.append("mov eax, 5")
    asm_lines.append("mov ecx, 0")
    asm_lines.append("mov edx, 0")
    asm_lines.append("int 0x80")
    asm_lines.append(f"mov [{safe_res}], eax")


def close_file(handle_var):
    safe = safe_name(handle_var)
    asm_lines.append(f"; --- CLOSE {handle_var} ---")
    asm_lines.append(f"mov ebx, [{safe}]")
    asm_lines.append("mov eax, 6")
    asm_lines.append("int 0x80")


def write_file(handle_var, src):
    safe_handle = safe_name(handle_var)
    asm_lines.append(f"; --- WRITE {handle_var} {src} ---")
    # treat src similar to print_var: if literal, write directly; if var, assume null terminated or length variable
    if (src.startswith('"') or src.startswith("'")):
        content = src[1:-1]
        tmp = f"_writestr_{len(declares)}"
        declares.append(f"{tmp}: db {', '.join(str(ord(c)) for c in content)},0")
        asm_lines.append(f"lea ecx, [{tmp}]")
        asm_lines.append(f"mov edx, {len(content)}")
    else:
        safe_src = safe_name(src)
        # compute length
        asm_lines.append(f"mov ecx, {safe_src}")
        # simple loop to measure length
        asm_lines.append(f"xor edx, edx")
        asm_lines.append(f".wlen_{safe_src}:")
        asm_lines.append(f"cmp byte [ecx+edx], 0")
        asm_lines.append(f"je .wlen_done_{safe_src}")
        asm_lines.append(f"inc edx")
        asm_lines.append(f"jmp .wlen_{safe_src}")
        asm_lines.append(f".wlen_done_{safe_src}:")
        asm_lines.append(f"mov ecx, {safe_src}")
    asm_lines.append(f"mov ebx, [{safe_handle}]")
    asm_lines.append("mov eax, 4")
    asm_lines.append("int 0x80")


def read_file(handle_var, dest_var, size_expr):
    safe_dest = safe_name(dest_var)
    safe_handle = safe_name(handle_var)
    asm_lines.append(f"; --- READFILE {handle_var} -> {dest_var} size={size_expr} ---")
    asm_lines.append(f"mov eax, 3")
    asm_lines.append(f"mov ebx, [{safe_handle}]")
    asm_lines.append(f"lea ecx, [{safe_dest}]")
    try:
        size = int(size_expr)
        asm_lines.append(f"mov edx, {size}")
    except ValueError:
        asm_lines.append(f"mov edx, [{safe_name(size_expr)}]")
    asm_lines.append("int 0x80")

# *** memory helpers ***

# *** memory helpers ***

def malloc_memory(target_var, size_expr):
    """Allocate memory dynamically."""
    safe_target = safe_name(target_var)

    asm_lines.append(f"; --- MALLOC {target_var}, size={size_expr} ---")

    try:
        size = int(size_expr)
    except ValueError:
        size_var = safe_name(size_expr)
        asm_lines.append(f"mov eax, [{size_var}]")
        asm_lines.append("push eax")
        asm_lines.append("call malloc")
        asm_lines.append("add esp, 4")
    else:
        asm_lines.append(f"push {size}")
        asm_lines.append("call malloc")
        asm_lines.append("add esp, 4")

    asm_lines.append(f"mov [{safe_target}], eax")

    if safe_target not in variables:
        variables[safe_target] = None
        declares.append(f"{safe_target}: dd 0")
        var_types[safe_target] = {'size': 4, 'define': 'dd', 'reserved': False}


def realloc_memory(target_var, new_size_expr):
    """Reallocate memory block."""
    safe_target = safe_name(target_var)

    asm_lines.append(f"; --- REALLOC {target_var}, new_size={new_size_expr} ---")

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


def free_memory(var_name: str):
    """Free dynamically allocated memory."""
    safe_var = safe_name(var_name)

    asm_lines.append(f"; --- FREE {var_name} ---")

    asm_lines.append(f"push dword [{safe_var}]")
    asm_lines.append("call free")
    asm_lines.append("add esp, 4")

    asm_lines.append(f"mov dword [{safe_var}], 0")


def get_sizeof(target_var, result_var):
    """Get the size of a variable in bytes."""
    safe_target = safe_name(target_var)
    safe_result = safe_name(result_var)

    size, _ = get_var_size(target_var)

    asm_lines.append(f"; --- SIZEOF {target_var} -> {result_var} ---")
    asm_lines.append(f"mov dword [{safe_result}], {size}")

    if safe_result not in variables:
        variables[safe_result] = size
        declares.append(f"{safe_result}: dd {size}")
        var_types[safe_result] = {'size': 4, 'define': 'dd', 'reserved': False}


# *** register helpers ***

def reg_operation(register, operation, variable):
    reg = register.lower()
    valid_regs = ['eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'esp', 'ebp']
    if reg not in valid_regs:
        print(f"Warning: Invalid register '{register}', using eax")
        reg = 'eax'

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
            asm_lines.append(f"mov {reg}, {immediate_value}")
        else:
            safe_var = safe_name(variable)
            size, _ = get_var_size(variable)
            if size == 1:
                asm_lines.append(f"mov {reg}, 0")
                asm_lines.append(f"mov {reg[-1]}l, [{safe_var}]")
            elif size == 2:
                asm_lines.append(f"mov {reg}, 0")
                asm_lines.append(f"mov {reg[-1]}x, [{safe_var}]")
            else:
                asm_lines.append(f"mov {reg}, [{safe_var}]")

    elif operation.lower() == 'store':
        if not has_operand:
            print(f"Warning: STORE operation requires an operand")
            return
        if is_immediate:
            print(f"Warning: Cannot STORE immediate value {immediate_value}")
            return
        safe_var = safe_name(variable)
        size, _ = get_var_size(variable)
        if size == 1:
            asm_lines.append(f"mov [{safe_var}], {reg[-1]}l")
        elif size == 2:
            asm_lines.append(f"mov [{safe_var}], {reg[-1]}x")
        else:
            asm_lines.append(f"mov [{safe_var}], {reg}")

    elif operation.lower() == 'add':
        if not has_operand:
            print(f"Warning: ADD operation requires an operand")
            return
        if is_immediate:
            asm_lines.append(f"add {reg}, {immediate_value}")
        else:
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
            asm_lines.append(f"sub {reg}, {immediate_value}")
        else:
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
            asm_lines.append(f"imul {reg}, {immediate_value}")
        else:
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
            asm_lines.append(f"mov ecx, {immediate_value}")
            asm_lines.append(f"mov eax, {reg}")
            asm_lines.append("xor edx, edx")
            asm_lines.append("div ecx")
            asm_lines.append(f"mov {reg}, eax")
        else:
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
        asm_lines.append(f"xor {reg}, {reg}")

    elif operation.lower() == 'inc':
        asm_lines.append(f"inc {reg}")

    elif operation.lower() == 'dec':
        asm_lines.append(f"dec {reg}")

    else:
        print(f"Warning: Unknown register operation '{operation}'")


# ---------------------------------------------------------------------------
# backend framework (registry, base class, built-in backends)
# ---------------------------------------------------------------------------

class Codegen(ABC):
    """Base class for code generation.

    Subclasses implement :meth:`generate` which accepts an IRProgram and
    returns the target-source text.
    """

    @abstractmethod
    def generate(self, ir):
        raise NotImplementedError


_backend_registry: Dict[str, Type[Codegen]] = {}


def register_backend(name: str):
    def decorator(cls: Type[Codegen]) -> Type[Codegen]:
        if name in _backend_registry:
            raise ValueError(f"backend {name!r} already registered")
        _backend_registry[name] = cls
        return cls
    return decorator


def get_backend(name: str) -> Type[Codegen]:
    return _backend_registry[name]


def available_backends() -> List[str]:
    return list(_backend_registry.keys())


# ---------------------------------------------------------------------------
# x86 backend implementation
# ---------------------------------------------------------------------------

@register_backend("x86")
class CodegenX86(Codegen):
    """Emit x86-32 assembly for Linux from IR."""

    def generate(self, ir) -> str:
        self._reset_context()
        for instr in ir.instrs:
            self._emit_instr(instr)
        self._emit_program_epilogue()
        self._emit_program_preamble()
        return "\n".join(asm_lines)

    def _reset_context(self) -> None:
        variables.clear()
        var_types.clear()
        declares.clear()
        buffers_created.clear()
        tostr_counter.clear()
        asm_lines.clear()

    def _emit_instr(self, instr):
        from compiler.frontend import (
            IRDeclare, IRMov, IRAdd, IRSub, IRMul, IRDiv, IRSqr, IRPow,
            IRLabel, IRGoto, IRPrint, IRRead, IRTostr, IRToint, IRPrtln,
            IRCondJump, IRPush, IRPop, IRMalloc, IRRealloc, IRFree,
            IRSizeof, IRReg,
            IRConcat, IRLength, IRSubstr, IRIndex,
            IROpen, IRClose, IRWrite, IRReadFile
        )
        if isinstance(instr, IRDeclare):
            self._emit_declare(instr)
        elif isinstance(instr, IRMov):
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
            asm_lines.append(f"{instr.name}:")
        elif isinstance(instr, IRGoto):
            asm_lines.append(f"jmp {instr.target}")
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
        elif isinstance(instr, IRPush):
            push_value(instr.var)
        elif isinstance(instr, IRPop):
            pop_value(instr.var)
        elif isinstance(instr, IRMalloc):
            malloc_memory(instr.target, instr.size)
        elif isinstance(instr, IRRealloc):
            realloc_memory(instr.target, instr.new_size)
        elif isinstance(instr, IRFree):
            free_memory(instr.var)
        elif isinstance(instr, IRSizeof):
            get_sizeof(instr.target, instr.result)
        elif isinstance(instr, IRConcat):
            str_concat(instr.dest, instr.src)
        elif isinstance(instr, IRLength):
            str_length(instr.src, instr.result)
        elif isinstance(instr, IRSubstr):
            str_substr(instr.dest, instr.src, instr.start, instr.length)
        elif isinstance(instr, IRIndex):
            str_index(instr.dest, instr.src, instr.index)
        elif isinstance(instr, IROpen):
            open_file(instr.filename, instr.result)
        elif isinstance(instr, IRClose):
            close_file(instr.handle)
        elif isinstance(instr, IRWrite):
            write_file(instr.handle, instr.src)
        elif isinstance(instr, IRReadFile):
            read_file(instr.handle, instr.dest, instr.size)
        elif isinstance(instr, IRReg):
            reg_operation(instr.register, instr.operation, instr.variable)
        else:
            raise NotImplementedError(f"Codegen для {type(instr).__name__} не реализован")

    def _emit_declare(self, instr):
        # reconstruct DECLARE line and use existing helpers
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

    def _emit_cond_jump(self, instr):
        op1 = instr.left
        op2 = instr.right
        label_true = instr.true_label
        label_false = instr.false_label

        size1, _ = get_var_size(op1)
        size2, _ = get_var_size(op2)

        if size1 <= 2 and size2 <= 2:
            reg = "ax" if size1 == 2 else "al"
            asm_lines.append(f"mov {reg}, [{op1}]")
            asm_lines.append(f"cmp {reg}, [{op2}]")
        else:
            asm_lines.append(f"mov eax, [{op1}]")
            asm_lines.append(f"cmp eax, [{op2}]")

        if instr.op == "==":
            asm_lines.append(f"je {label_true}")
        elif instr.op == ">":
            asm_lines.append(f"jg {label_true}")
        elif instr.op == "<":
            asm_lines.append(f"jl {label_true}")
        elif instr.op == ">=":
            asm_lines.append(f"jge {label_true}")
        elif instr.op == "<=":
            asm_lines.append(f"jle {label_true}")
        else:
            raise ValueError(f"Неподдерживаемый оператор сравнения {instr.op}")

        asm_lines.append(f"jmp {label_false}")

    def _emit_push(self, instr):
        push_value(instr.var)

    def _emit_pop(self, instr):
        pop_value(instr.var)

    def _emit_malloc(self, instr):
        malloc_memory(instr.target, instr.size)

    def _emit_realloc(self, instr):
        realloc_memory(instr.target, instr.new_size)

    def _emit_free(self, instr):
        free_memory(instr.var)

    def _emit_sizeof(self, instr):
        get_sizeof(instr.target, instr.result)

    def _emit_reg(self, instr):
        reg_operation(instr.register, instr.operation, instr.variable)

    # === program prologue/epilogue ===
    def _emit_program_epilogue(self) -> None:
        asm_lines.append("mov eax, 1")
        asm_lines.append("xor ebx, ebx")
        asm_lines.append("int 0x80")

        asm_lines.append("overflow_handler:")
        asm_lines.append("; simple overflow trap")
        asm_lines.append("mov eax, 1")
        asm_lines.append("mov ebx, 1")
        asm_lines.append("int 0x80")

    def _emit_program_preamble(self) -> None:
        prologue = [
            "format ELF executable 4",
            "entry start",
            "",
            "; dynamic memory management with brk syscall",
            "malloc:",
            "; eax = size (passed in eax)",
            "push ebx",
            "push ecx",
            "mov ecx, eax",  # save requested size
            "xor eax, eax",  # brk(0) - get current heap end
            "int 0x80",
            "mov ebx, eax",  # current heap end in ebx
            "add eax, ecx",  # eax = current_end + size",
            "int 0x80",      # brk(new_end)",
            "mov eax, ebx",  # return old heap end as pointer",
            "pop ecx",
            "pop ebx",
            "ret",
            "",
            "free:",
            "; simple free - do nothing (no deallocation)",
            "ret",
            "",
            "realloc:",
            "; simple realloc - just malloc new block",
            "; (ignores old pointer, allocates new memory)",
            "jmp malloc",
            "",
        ] + declares + ["start:"]

        asm_lines[:0] = prologue


# ---------------------------------------------------------------------------
# dummy backend for testing
# ---------------------------------------------------------------------------

@register_backend("dummy")
class DummyCodegen(Codegen):
    def generate(self, ir):
        lines = ["; dummy backend output"]
        for instr in ir.instrs:
            lines.append(repr(instr))
        return "\n".join(lines)

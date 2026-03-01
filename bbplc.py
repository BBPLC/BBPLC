from modules.io import print_var
from modules.math import add, sub, mul, div, sqr, pow
from modules.bbplctypes import DATA_DEFINE, DATA_RESERVE, parse_declare, declare, toint, tostr, safe_name, get_var_size
from modules import context_manager

grammar = ["DECLARE", "PRINT", "ADD", "SUB", "MUL","DIV","SQR","POW", "IF", "THEN", "ELSE", 
            "ENDIF", "TOSTR", "TOINT", "LABEL", "GOTO", "MOV", "READ", "PUSH", "POP"]
dataTypes = ["DB", "DW", "DD", "DP", "DQ", "DT"]

def label(name):
    context_manager.asm_lines.append(f"{name}:")

def goto(name):
    context_manager.asm_lines.append(f"jmp {name}")

def if_eq(op1, op2, label_true, label_false):
    size1, _ = get_var_size(op1)
    size2, _ = get_var_size(op2)
    
    if size1 <= 2 and size2 <= 2:
        reg = "ax" if size1 == 2 else "al"
        context_manager.asm_lines.append(f"mov {reg}, [{op1}]")
        context_manager.asm_lines.append(f"cmp {reg}, [{op2}]")
    else:
        context_manager.asm_lines.append(f"mov eax, [{op1}]")
        context_manager.asm_lines.append(f"cmp eax, [{op2}]")
    
    context_manager.asm_lines.append(f"je {label_true}")
    context_manager.asm_lines.append(f"jmp {label_false}")

def if_gt(op1, op2, label_true, label_false):
    size1, _ = get_var_size(op1)
    size2, _ = get_var_size(op2)
    
    if size1 <= 2 and size2 <= 2:
        reg = "ax" if size1 == 2 else "al"
        context_manager.asm_lines.append(f"mov {reg}, [{op1}]")
        context_manager.asm_lines.append(f"cmp {reg}, [{op2}]")
    else:
        context_manager.asm_lines.append(f"mov eax, [{op1}]")
        context_manager.asm_lines.append(f"cmp eax, [{op2}]")
    
    context_manager.asm_lines.append(f"jg {label_true}")
    context_manager.asm_lines.append(f"jmp {label_false}")

def if_lt(op1, op2, label_true, label_false):
    size1, _ = get_var_size(op1)
    size2, _ = get_var_size(op2)
    
    if size1 <= 2 and size2 <= 2:
        reg = "ax" if size1 == 2 else "al"
        context_manager.asm_lines.append(f"mov {reg}, [{op1}]")
        context_manager.asm_lines.append(f"cmp {reg}, [{op2}]")
    else:
        context_manager.asm_lines.append(f"mov eax, [{op1}]")
        context_manager.asm_lines.append(f"cmp eax, [{op2}]")
    
    context_manager.asm_lines.append(f"jl {label_true}")
    context_manager.asm_lines.append(f"jmp {label_false}")


with open('code.bbplc') as f:
    lines = f.readlines()

code = [line.strip() for line in lines if line.strip()]

label_counter = 0
for line in code:
    words = line.split()
    cmd = words[0]
    if cmd == "DECLARE":
        var_type, var_name, var_value = parse_declare(line)
        if var_type:
            declare(var_type, var_name, var_value)

for line in code:
    words = line.split()
    if not words:
        continue

    cmd = words[0]
    if cmd in ("TOSTR", "TOINT"):
        name = words[1]

        if name not in context_manager.buffers_created:
            buf_index = 0
            context_manager.buffers_created[name] = [buf_index]
        else:
            buf_index = max(context_manager.buffers_created[name]) + 1
            context_manager.buffers_created[name].append(buf_index)

        buf_name = safe_name(f"{name}_str_{buf_index}")
        len_name = safe_name(f"{buf_name}_len")
        ptr_name = safe_name(f"{buf_name}_ptr")

        if buf_name not in context_manager.variables:
            context_manager.declares.append(f"{buf_name}: times 20 db 0 ; buffer for {name}")
            context_manager.declares.append(f"{len_name}: dd 0 ; length of {buf_name}")
            context_manager.declares.append(f"{ptr_name}: dd 0 ; pointer to start of {buf_name}")

            context_manager.variables[buf_name] = "tostr_buffer"
            context_manager.variables[len_name] = 0
            context_manager.variables[ptr_name] = 0

context_manager.asm_lines[:0] = ["format ELF executable 4", "entry start", ""] + context_manager.declares
context_manager.asm_lines.append("start:")

for line in code:
    words = line.split()
    cmd = words[0]
    if cmd == "DECLARE":
        continue
    elif cmd == "ADD":
        add(words[1], words[2])
    elif cmd == "SUB":
        sub(words[1], words[2])
    elif cmd == "MUL":
        mul(words[1], words[2])
    elif cmd == "DIV":
        div(words[1], words[2])
    elif cmd == "SQR":
        sqr(words[1])
    elif cmd == "POW":
        pow(words[1], words[2])
    elif cmd == "TOSTR":
        tostr(words[1])
    elif cmd == "TOINT":
        toint(words[1])
    elif cmd == "PRINT":
        name = words[1]
        print_var(name)
    elif cmd == "LABEL":
        label(words[1])
    elif cmd == "GOTO":
        goto(words[1])
    elif cmd == "IF":
        op1 = words[1]
        op = words[2]
        op2 = words[3]
        label_true = f"L_true_{label_counter}"
        label_false = f"L_false_{label_counter}"
        label_counter += 1
        if op == "==":
            if_eq(op1, op2, label_true, label_false)
        elif op == ">":
            if_gt(op1, op2, label_true, label_false)
        elif op == "<":
            if_lt(op1, op2, label_true, label_false)
        context_manager.asm_lines.append(f"{label_true}: ; THEN branch")
        context_manager.asm_lines.append(f"{label_false}: ; ELSE branch")

context_manager.asm_lines.append("mov eax, 1")
context_manager.asm_lines.append("xor ebx, ebx")
context_manager.asm_lines.append("int 0x80")

with open("output.asm", "w") as f:
    f.write("\n".join(context_manager.asm_lines))

print("ASM code generated in output.asm")
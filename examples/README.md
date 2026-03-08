# BBPLC - Code Examples

A comprehensive set of examples demonstrating all features of the BBPLC language.

## Example Structure

### Basic Examples
- **01_basic_hello.bbplc** - Simple text output (DECLARE, PRINT)
- **02_multiple_types.bbplc** - Different data types (DB, DW, DD)
- **03_arithmetic.bbplc** - Arithmetic operations (ADD, SUB, MUL, DIV)
- **04_power_square.bbplc** - Power and square operations (SQR, POW)

### Input and Output
- **05_input_output.bbplc** - Reading and writing data (READ, PRINT, PRTLN)
- **08_string_conversion.bbplc** - String and number conversion (TOSTR, TOINT)
- **09_reserved_memory.bbplc** - Reserved memory buffers (DECLARE RESERVE)

### Control Flow
- **06_conditionals.bbplc** - Conditional statements (IF, THEN, ELSE, ENDIF)
- **07_loops_goto.bbplc** - Loops with LABEL and GOTO
- **11_comparison_branching.bbplc** - Different comparison operators

### Memory Management
- **16_stack_operations.bbplc** - Stack operations (PUSH, POP)
- **17_dynamic_memory.bbplc** - Dynamic memory allocation (MALLOC, FREE, SIZEOF)
- **18_register_operations.bbplc** - Register manipulation (REG operations)
- **19_advanced_memory.bbplc** - Advanced memory and register operations

## Running Examples

```bash
python3 bbplc.py examples/01_basic_hello.bbplc
```

The result will be compiled to `output.asm`.

## Main Language Constructs

### Variable Declaration
```bbplc
DECLARE DB text = "Hello"
DECLARE DD number = 42
DECLARE RESERVE RB buffer 64
```

### Arithmetic
```bbplc
ADD a b
SUB a b
MUL a b
DIV a b
SQR a
POW a b
MOV a b
```

### Input/Output
```bbplc
PRINT name
READ variable
PRTLN
TOSTR number
TOINT variable
```

### Control Flow
```bbplc
LABEL my_label
GOTO my_label

IF x == 5
THEN
    PRINT msg
ELSE
    PRINT other_msg
ENDIF
```

### Memory Management
```bbplc
PUSH variable      ; Push to stack
POP variable       ; Pop from stack

MALLOC ptr size    ; Allocate memory
REALLOC ptr new_size ; Reallocate memory
FREE ptr           ; Free memory

SIZEOF var result  ; Get variable size
```

### Register Operations
```bbplc
REG EAX LOAD variable   ; Load variable into register
REG EBX STORE variable  ; Store register to variable
REG ECX ADD variable    ; Add variable to register
REG EDX SUB variable    ; Subtract from register
REG ESI MUL variable    ; Multiply register by variable
REG EDI DIV variable    ; Divide register by variable
REG ESP CLEAR           ; Clear register
REG EBP INC             ; Increment register
```

## Data Types

| Type | Size | Usage |
|------|------|-------|
| DB   | 1 byte | Strings, bytes |
| DW   | 2 bytes | Words |
| DD   | 4 bytes | Double words (numbers) |
| DP   | 6 bytes | Pointers |
| DQ   | 8 bytes | Quad words |
| DT   | 10 bytes | Ten bytes |

For reserved memory use: RB, RW, RD, RP, RQ, RT

## Comments

All examples include detailed comments explaining the code. Comments start with `;` and continue to the end of the line:

```bbplc
; This is a comment
DECLARE DB msg = "Hello"  ; Inline comment
```

## Memory Management

BBPLC provides high-level memory management operations:

### Stack Operations
- **PUSH**: Push variable value onto the stack
- **POP**: Pop value from stack into variable

### Dynamic Memory
- **MALLOC**: Allocate memory block of specified size
- **REALLOC**: Resize previously allocated memory block
- **FREE**: Release allocated memory

### Size Information
- **SIZEOF**: Get the size of a variable in bytes

## Register Operations

Direct register manipulation for performance-critical code:

- **LOAD**: Load variable value into register
- **STORE**: Store register value to variable
- **ADD/SUB/MUL/DIV**: Arithmetic operations with registers
- **CLEAR**: Zero out register
- **INC/DEC**: Increment/decrement register

Supported registers: EAX, EBX, ECX, EDX, ESI, EDI, ESP, EBP
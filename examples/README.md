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

### Advanced Programs
- **10_complex_program.bbplc** - Simple calculator (all features)
- **12_countdown.bbplc** - Countdown loop
- **13_factorial.bbplc** - Factorial calculation
- **14_even_odd_checker.bbplc** - Even/odd number checker
- **15_sum_series.bbplc** - Sum of series from 1 to N

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

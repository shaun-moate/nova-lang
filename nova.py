#!/usr/bin/env python3
## TODO: implement tox/poetry to manage virtual environment for python
## TODO: consider migration to go-lang support implementation of static typing
## TODO: add capability to "include" libraries (ie. include "std:nova:core")

import sys
import subprocess
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Union

iota_counter = 0

def uncons(xs):
    return (xs[0], xs[1:])

## TODO: Add OP_ASSERT to support testing framework - enabling us to ensure we can assert() the expected correct result
## TODO: add `%` for mod suport
## TODO: add `/` for division support
class OperandId(Enum):
    PUSH_INT  = auto()
    PUSH_STR  = auto()
    OVER      = auto()
    SWAP      = auto()
    DUP       = auto()
    DUP2      = auto()
    DROP      = auto()
    DUMP      = auto()
    SHL       = auto()
    SHR       = auto()
    BAND      = auto()
    BOR       = auto()
    PLUS      = auto()
    MINUS     = auto()
    MULT      = auto()
    EQUAL     = auto()
    NOT_EQUAL = auto()
    GREATER   = auto()
    GR_EQ     = auto()
    LESSER    = auto()
    LESS_EQ   = auto()
    IF        = auto()
    ELSE      = auto()
    FI        = auto()
    WHILE     = auto()
    DO        = auto()
    DONE      = auto()
    END       = auto()
    MEM_ADDR  = auto()
    MEM_STORE = auto()
    MEM_LOAD  = auto()
    SYSCALL   = auto()
    EXIT      = auto()

class MacroId(Enum):
    WRITE     = auto()

class ConstantId(Enum):
    CATCH     = auto()

class TokenId(Enum):
    OP        = auto()
    MACRO     = auto()
    CONST     = auto()
    INT       = auto()
    STR       = auto()

STR_ALLOCATION_SIZE = 69_000
MEM_ALLOCATION_SIZE = 69_000

assert len(OperandId) == 33, "Exhaustive list of operands"
## TODO: add `include` to support the inclusion of base libraries of operations (ie. include "nova:core")
## TODO: add `{` and `}` as operands to help segment blocks and improve readability
## TODO: add `(` and `)` as operands to help with math ordering`

BUILTIN_OPS = {
    "+":       OperandId.PLUS,
    "-":       OperandId.MINUS,
    "*":       OperandId.MULT,
    "==":      OperandId.EQUAL,
    "!=":      OperandId.NOT_EQUAL,
    ">":       OperandId.GREATER,
    ">=":      OperandId.GR_EQ,
    "<":       OperandId.LESSER,
    "<=":      OperandId.LESS_EQ,
    "if":      OperandId.IF,
    "else":    OperandId.ELSE,
    "fi":      OperandId.FI,
    "while":   OperandId.WHILE,
    "do":      OperandId.DO,
    "done":    OperandId.DONE,
    "end":     OperandId.END,
    "mem":     OperandId.MEM_ADDR,
    "store8":  OperandId.MEM_STORE,
    "load8":   OperandId.MEM_LOAD,
    "syscall": OperandId.SYSCALL,
    "over":    OperandId.OVER,
    "swap":    OperandId.SWAP,
    "dup":     OperandId.DUP,
    "2dup":    OperandId.DUP2,
    "dump":    OperandId.DUMP,
    "drop":    OperandId.DROP,
    "shl":     OperandId.SHL,
    "shr":     OperandId.SHR,
    "band":    OperandId.BAND,
    "bor":     OperandId.BOR,
    "exit":    OperandId.EXIT
}

## TODO: add MACROS to examples to improve readability -> ie. rule110.nv
assert len(MacroId) == 1, "Exhaustive list of macros"
BUILTIN_MACRO = {
    "write":   [1, 1, 'syscall'],
}

assert len(ConstantId) == 1, "Exhaustive list of constants"
BUILTIN_CONST = {
    "CATCH":   22,
}

@dataclass
class FileLocation:
    file_path: str
    row:       int
    col:       int

@dataclass
class Token:
    typ:       TokenId
    location:  FileLocation
    value:     Union[int, str]

@dataclass
class Operand:
    action:    OperandId
    jump_to:   int
    mem_addr:  int
    location:  FileLocation
    value:     Union[int, str]

@dataclass
class Program:
    operands: List[Operand] = field(default_factory=list)

def parse_program_from_file(input_file_path: str) -> Program:
    with open(input_file_path, "r") as file:
        return generate_blocks(
                    Program(operands = [parse_token_as_op(token) for token in parse_tokens_from_file(input_file_path)])
                )

def generate_blocks(program: Program) -> Program:
    block = []
    program = unnest_program(program)
    for ip in range(len(program.operands)):
        assert len(OperandId) == 33, "Exhaustive list of operands"
        if program.operands[ip].action == OperandId.IF:
            block.append(ip)
        if program.operands[ip].action == OperandId.ELSE:
            ref = block.pop()
            assert program.operands[ref].action == OperandId.IF, "ERROR: `else` can only be used in `if` blocks"
            program.operands[ref].action = OperandId.IF
            program.operands[ref].jump_to = ip+1
            block.append(ip)
        if program.operands[ip].action == OperandId.FI:
            ref = block.pop()
            assert program.operands[ref].action == OperandId.IF or program.operands[ref].action == OperandId.ELSE, "ERROR: `fi` is expected to end the blocks for `if` or `else` only"
            program.operands[ip].jump_to = ip+1
            program.operands[ref].jump_to = ip
        if program.operands[ip].action == OperandId.WHILE:
            block.append(ip)
        if program.operands[ip].action == OperandId.DO:
            ref = block.pop()
            assert program.operands[ref].action == OperandId.WHILE, "ERROR: `do` can only be used in `while` blocks"
            program.operands[ip].jump_to = ref
            block.append(ip)
        if program.operands[ip].action == OperandId.DONE:
            ref = block.pop()
            program.operands[ip].jump_to = program.operands[ref].jump_to
            program.operands[ref].action = OperandId.DO
            program.operands[ref].jump_to = ip+1
        if program.operands[ip].action == OperandId.END:
           pass
    return program

def parse_token_as_op(token: TokenId):
    location = token.location
    word = token.value
    assert len(TokenId) == 5, "Exhaustive list of operands in parse_word()"
    if token.typ == TokenId.OP:
        if token.value in BUILTIN_OPS:
            return Operand(action   = BUILTIN_OPS[token.value],
                           jump_to  = -1,
                           mem_addr = -1,
                           location = token.location,
                           value    = token.value)
        else:
            print("%s:%d:%d: ERROR: unknown operand `%s` found" % (token.location + (token.value, )))
            exit(1)
    elif token.typ == TokenId.MACRO:
        macro = token.value
        return [Operand(action   = action,
                        jump_to  = -1,
                        mem_addr = -1,
                        location = token.location,
                        value    = value)
                for (action, value) in parse_macro(macro)]
    elif token.typ == TokenId.CONST:
        if token.value in BUILTIN_CONST:
            return Operand(action   = OperandId.PUSH_INT,
                           jump_to  = -1,
                           mem_addr = -1,
                           location = token.location,
                           value    = BUILTIN_CONST[token.value])
    elif token.typ == TokenId.INT:
        return Operand(action   = OperandId.PUSH_INT,
                       jump_to  = -1,
                       mem_addr = -1,
                       location = token.location,
                       value    = token.value)
    elif token.typ == TokenId.STR:
        return Operand(action   = OperandId.PUSH_STR,
                       jump_to  = -1,
                       mem_addr = -1,
                       location = token.location,
                       value    = token.value)
    else:
        assert False, "TokenId type is unreachable is unreachable"

def parse_tokens_from_file(input_file_path: str) -> Token:
    with open(input_file_path, "r") as file:
        return [Token(typ      = token_type,
                      location = FileLocation(input_file_path, row+1, col+1),
                      value    = token_value)
                for (row, line) in enumerate(file.readlines())
                for (col, (token_type, token_value)) in parse_line(line.split("//")[0])]

def parse_macro(macro: List[Token]) -> Token:
    instructions = BUILTIN_MACRO[macro]
    if macro in BUILTIN_MACRO:
        for i in instructions:
            if parse_word(i)[0] == TokenId.OP:
                if i in BUILTIN_OPS:
                    yield(BUILTIN_OPS[i], i)
                else:
                    assert False, "ERROR: `%s` not found in BUILTIN_OPS" % i
            elif parse_word(i)[0] == TokenId.INT:
                yield(OperandId.PUSH_INT, int(i))

def parse_line(line: str):
    start = find_next(line, 0, lambda x: not x.isspace())
    while start < len(line):
        if line[start] == "\"":
            end = find_next(line, start+1, lambda x: x == "\"")
            yield(start, parse_word(line[start+1:end], typ="str"))
        elif line[start:find_next(line, start, lambda x: x.isspace())] == "macro":
            (name, start, end) = parse_name(line, start)
            if name in BUILTIN_MACRO:
                print("ERROR: attempting to override a built-in macro `%s` - not permitted" % name)
                exit(1)
            (macro_stack, start, end) = parse_macro_stack(line, start, end)
            BUILTIN_MACRO[name] = macro_stack
            start = find_next(line, end+1, lambda x: not x.isspace())
        elif line[start:find_next(line, start, lambda x: x.isspace())] in BUILTIN_MACRO:
            end = find_next(line, start, lambda x: x.isspace())
            yield(start, parse_word(line[start:end], typ="macro"))
        elif line[start:find_next(line, start, lambda x: x.isspace())] == "const":
            (name, start, end) = parse_name(line, start)
            if name in BUILTIN_CONST:
                print("ERROR: attempting to override a built-in constant `%s` - not permitted" % name)
                exit(1)
            (value, start, end) = parse_const_int(line, start, end)
            BUILTIN_CONST[name] = value
        elif line[start:find_next(line, start, lambda x: x.isspace())] in BUILTIN_CONST:
            end = find_next(line, start, lambda x: x.isspace())
            yield(start, parse_word(line[start:end], typ="const"))
        else:
            end = find_next(line, start, lambda x: x.isspace())
            yield(start, parse_word(line[start:end]))
        start = find_next(line, end+1, lambda x: not x.isspace())

def parse_name(line, start):
    skip_end = find_next(line, start, lambda x: x.isspace())
    start_next = find_next(line, skip_end+1, lambda x: not x.isspace())
    end_next = find_next(line, start_next, lambda x: x.isspace())
    return (line[start_next:end_next], start_next, end_next)

def parse_macro_stack(line, start, end):
    macro_stack = []
    start = find_next(line, end+1, lambda x: not x.isspace())
    while line[start:find_next(line, start, lambda x: x.isspace())] != "end":
        end = find_next(line, start, lambda x: x.isspace())
        assert parse_word(line[start:end])[0] == TokenId.OP or parse_word(line[start:end])[0] == TokenId.INT, "ERROR: macro op value must be of type operation or integer"
        macro_stack.append(line[start:end])
        start = find_next(line, end+1, lambda x: not x.isspace())
    end = find_next(line, start, lambda x: x.isspace())
    return (macro_stack, start, end)

def parse_const_int(line, start, end):
    start = find_next(line, end+1, lambda x: not x.isspace())
    end = find_next(line, start, lambda x: x.isspace())
    value = line[start:end]
    assert int(value), "ERROR: const value must be of type integer"
    return (value, start, end)

def parse_word(token: TokenId, typ=None):
    assert len(TokenId) == 5, "Exhaustive list of operands in parse_word()"
    if typ == "str":
        return (TokenId.STR, bytes(token, "utf-8").decode("unicode_escape"))
    elif typ == "macro":
        return (TokenId.MACRO, token)
    elif typ == "const":
        return (TokenId.CONST, token)
    else:
        try:
            return (TokenId.INT, int(token))
        except ValueError:
            return (TokenId.OP, token)

def find_next(line: int, start: int, predicate: int) -> int:
    while start < len(line) and not predicate(line[start]):
        start += 1
    return start

def unnest_program(program: Program) -> Program:
    result = []
    for i in range(len(program.operands)):
        if type(program.operands[i]) is list:
            for j in range(len(program.operands[i])):
                result.append(program.operands[i][j])
        else:
            result.append(program.operands[i])
    program.operands = result
    return program

def simulate_program(program):
    stack = []
    mem = bytearray(MEM_ALLOCATION_SIZE + STR_ALLOCATION_SIZE)
    str_addr_start = 0
    ip = 0
    while ip < len(program.operands):
        assert len(OperandId) == 33, "Exhaustive list of operands in simulate_program()"
        op = program.operands[ip]
        if op.action == OperandId.PUSH_INT:
            stack.append(op.value)
            ip += 1
        elif op.action == OperandId.PUSH_STR:
            str_bytes = bytes(op.value, "utf-8")
            str_length = len(str_bytes)
            if op.mem_addr == -1:
                op.mem_addr = str_addr_start
                for i in reversed(range(str_length)):
                    mem[str_addr_start+i] = str_bytes[i]
                str_addr_start += str_length
                assert str_addr_start <= STR_ALLOCATION_SIZE, "ERROR: String buffer overflow"
            stack.append(str_length)
            stack.append(op.mem_addr)
            ip += 1
        elif op.action == OperandId.OVER:
            x = stack.pop()
            y = stack.pop()
            stack.append(y)
            stack.append(x)
            stack.append(y)
            ip += 1
        elif op.action == OperandId.SWAP:
            x = stack.pop()
            y = stack.pop()
            stack.append(x)
            stack.append(y)
            ip += 1
        elif op.action == OperandId.DROP:
            stack.pop()
            ip += 1
        elif op.action == OperandId.DUMP:
            x = stack.pop()
            print(x)
            ip += 1
        elif op.action == OperandId.DUP:
            x = stack.pop()
            stack.append(x)
            stack.append(x)
            ip += 1
        elif op.action == OperandId.DUP2:
            x = stack.pop()
            y = stack.pop()
            stack.append(y)
            stack.append(x)
            stack.append(y)
            stack.append(x)
            ip += 1
        elif op.action == OperandId.SHL:
            x = stack.pop()
            y = stack.pop()
            stack.append(y << x)
            ip += 1
        elif op.action == OperandId.SHR:
            x = stack.pop()
            y = stack.pop()
            stack.append(y >> x)
            ip += 1
        elif op.action == OperandId.BAND:
            x = stack.pop()
            y = stack.pop()
            stack.append(y & x)
            ip += 1
        elif op.action == OperandId.BOR:
            x = stack.pop()
            y = stack.pop()
            stack.append(y | x)
            ip += 1
        elif op.action == OperandId.PLUS:
            x = stack.pop()
            y = stack.pop()
            stack.append(x + y)
            ip += 1
        elif op.action == OperandId.MINUS:
            x = stack.pop()
            y = stack.pop()
            stack.append(y - x)
            ip += 1
        elif op.action == OperandId.MULT:
            x = stack.pop()
            y = stack.pop()
            stack.append(y * x)
            ip += 1
        elif op.action == OperandId.EQUAL:
            x = stack.pop()
            y = stack.pop()
            stack.append(int(y == x))
            ip += 1
        elif op.action == OperandId.NOT_EQUAL:
            x = stack.pop()
            y = stack.pop()
            stack.append(int(y != x))
            ip += 1
        elif op.action == OperandId.GREATER:
            x = stack.pop()
            y = stack.pop()
            stack.append(int(y > x))
            ip += 1
        elif op.action == OperandId.GR_EQ:
            x = stack.pop()
            y = stack.pop()
            stack.append(int(y >= x))
            ip += 1
        elif op.action == OperandId.LESSER:
            x = stack.pop()
            y = stack.pop()
            stack.append(int(y < x))
            ip += 1
        elif op.action == OperandId.LESS_EQ:
            x = stack.pop()
            y = stack.pop()
            stack.append(int(y <= x))
            ip += 1
        elif op.action == OperandId.IF:
            if stack.pop() == 0:
                ip = op.jump_to
            else:
                ip += 1
        elif op.action == OperandId.ELSE:
            ip = op.jump_to
        elif op.action == OperandId.FI:
            ip = op.jump_to
        elif op.action == OperandId.WHILE:
            ip += 1
        elif op.action == OperandId.DO:
            if stack.pop() == 0:
                ip = op.jump_to
            else:
                ip += 1
        elif op.action == OperandId.DONE:
            ip = op.jump_to
            ip += 1
        elif op.action == OperandId.END:
            ip += 1
        elif op.action == OperandId.MEM_ADDR:
            stack.append(STR_ALLOCATION_SIZE)
            ip += 1
        elif op.action == OperandId.MEM_STORE:
            byte = stack.pop()
            addr = stack.pop()
            mem[addr] = byte & 0xFF
            ip += 1
        elif op.action == OperandId.MEM_LOAD:
            addr = stack.pop()
            byte = mem[addr]
            stack.append(byte)
            ip += 1
        elif op.action == OperandId.SYSCALL:
            syscall_num = stack.pop()
            arg1 = stack.pop()
            arg2 = stack.pop()
            arg3 = stack.pop()
            if syscall_num == 1:
                print(mem[arg2:arg2+arg3].decode("utf-8"), end="")
            ip += 1
        elif op.action == OperandId.EXIT:
            x = stack.pop()
            exit(x)
            ip += 1
        else:
            assert False, "OperandIderands is unreachable"

def compile_program(program):
    str_stack = []
    with open("build/output.asm", "w") as out:
        out.write("segment .text\n")
        out.write("dump:\n")
        out.write("    mov r9, -3689348814741910323\n")
        out.write("    sub rsp, 40\n")
        out.write("    mov BYTE [rsp+31], 10\n")
        out.write("    lea rcx, [rsp+30]\n")
        out.write(".L2:\n")
        out.write("    mov rax, rdi\n")
        out.write("    lea r8, [rsp+32]\n")
        out.write("    mul r9\n")
        out.write("    mov rax, rdi\n")
        out.write("    sub r8, rcx\n")
        out.write("    shr rdx, 3\n")
        out.write("    lea rsi, [rdx+rdx*4]\n")
        out.write("    add rsi, rsi\n")
        out.write("    sub rax, rsi\n")
        out.write("    add eax, 48\n")
        out.write("    mov BYTE [rcx], al\n")
        out.write("    mov rax, rdi\n")
        out.write("    mov rdi, rdx\n")
        out.write("    mov rdx, rcx\n")
        out.write("    sub rcx, 1\n")
        out.write("    cmp rax, 9\n")
        out.write("    ja  .L2\n")
        out.write("    lea rax, [rsp+32]\n")
        out.write("    mov edi, 1\n")
        out.write("    sub rdx, rax\n")
        out.write("    xor eax, eax\n")
        out.write("    lea rsi, [rsp+32+rdx]\n")
        out.write("    mov rdx, r8\n")
        out.write("    mov rax, 1\n")
        out.write("    syscall\n")
        out.write("    add rsp, 40\n")
        out.write("    ret\n")

        out.write("global _start\n_start:\n")
        for ip in range(len(program.operands)):
            assert len(OperandId) == 33, "Exhaustive list of operands in compile_program()"
            op = program.operands[ip]
            out.write("addr_%d:\n" % ip)
            if op.action == OperandId.PUSH_INT:
                out.write("    push %d\n" % int(op.value))
            elif op.action == OperandId.PUSH_STR:
                str_bytes = bytes(op.value, "utf-8")
                out.write("    mov rax, %d\n" % len(bytes(op.value, "utf-8")))
                out.write("    push rax\n")
                out.write("    push str_%d\n" % len(str_stack))
                str_stack.append(str_bytes)
            elif op.action == OperandId.OVER:
                out.write("    pop rax\n")
                out.write("    pop rbx\n")
                out.write("    push rbx\n")
                out.write("    push rax\n")
                out.write("    push rbx\n")
            elif op.action == OperandId.SWAP:
                out.write("    pop rax\n")
                out.write("    pop rbx\n")
                out.write("    push rax\n")
                out.write("    push rbx\n")
            elif op.action == OperandId.DROP:
                out.write("    pop rax\n")
            elif op.action == OperandId.DUMP:
                out.write("    pop rdi\n")
                out.write("    call dump\n")
            elif op.action == OperandId.DUP:
                out.write("    pop rax\n")
                out.write("    push rax\n")
                out.write("    push rax\n")
            elif op.action == OperandId.DUP2:
                out.write("    pop rax\n")
                out.write("    pop rbx\n")
                out.write("    push rbx\n")
                out.write("    push rax\n")
                out.write("    push rbx\n")
                out.write("    push rax\n")
            elif op.action == OperandId.SHL:
                out.write("    pop rcx\n")
                out.write("    pop rax\n")
                out.write("    shl rax, cl\n")
                out.write("    push rax\n")
            elif op.action == OperandId.SHR:
                out.write("    pop rcx\n")
                out.write("    pop rax\n")
                out.write("    shr rax, cl\n")
                out.write("    push rax\n")
            elif op.action == OperandId.BAND:
                out.write("    pop rax\n")
                out.write("    pop rbx\n")
                out.write("    and rax, rbx\n")
                out.write("    push rax\n")
            elif op.action == OperandId.BOR:
                out.write("    pop rax\n")
                out.write("    pop rbx\n")
                out.write("    or rax, rbx\n")
                out.write("    push rax\n")
            elif op.action == OperandId.PLUS:
                out.write("    pop rax\n")
                out.write("    pop rbx\n")
                out.write("    add rax, rbx\n")
                out.write("    push rax\n")
            elif op.action == OperandId.MINUS:
                out.write("    pop rax\n")
                out.write("    pop rbx\n")
                out.write("    sub rbx, rax\n")
                out.write("    push rbx\n")
            elif op.action == OperandId.MULT:
                out.write("    pop rax\n")
                out.write("    pop rbx\n")
                out.write("    mul rbx\n")
                out.write("    push rax\n")
            elif op.action == OperandId.EQUAL:
                out.write("    mov rcx, 0\n")
                out.write("    mov rdx, 1\n")
                out.write("    pop rax\n")
                out.write("    pop rbx\n")
                out.write("    cmp rax, rbx\n")
                out.write("    cmove rcx, rdx\n")
                out.write("    push rcx\n")
            elif op.action == OperandId.NOT_EQUAL:
                out.write("    mov rcx, 0\n")
                out.write("    mov rdx, 1\n")
                out.write("    pop rax\n")
                out.write("    pop rbx\n")
                out.write("    cmp rax, rbx\n")
                out.write("    cmovne rcx, rdx\n")
                out.write("    push rcx\n")
            elif op.action == OperandId.GREATER:
                out.write("    mov rcx, 0\n")
                out.write("    mov rdx, 1\n")
                out.write("    pop rax\n")
                out.write("    pop rbx\n")
                out.write("    cmp rbx, rax\n")
                out.write("    cmovg rcx, rdx\n")
                out.write("    push rcx\n")
            elif op.action == OperandId.GR_EQ:
                out.write("    mov rcx, 0\n")
                out.write("    mov rdx, 1\n")
                out.write("    pop rax\n")
                out.write("    pop rbx\n")
                out.write("    cmp rbx, rax\n")
                out.write("    cmovge rcx, rdx\n")
                out.write("    push rcx\n")
            elif op.action == OperandId.LESSER:
                out.write("    mov rcx, 0\n")
                out.write("    mov rdx, 1\n")
                out.write("    pop rax\n")
                out.write("    pop rbx\n")
                out.write("    cmp rbx, rax\n")
                out.write("    cmovl rcx, rdx\n")
                out.write("    push rcx\n")
            elif op.action == OperandId.LESS_EQ:
                out.write("    mov rcx, 0\n")
                out.write("    mov rdx, 1\n")
                out.write("    pop rax\n")
                out.write("    pop rbx\n")
                out.write("    cmp rbx, rax\n")
                out.write("    cmovle rcx, rdx\n")
                out.write("    push rcx\n")
            elif op.action == OperandId.IF:
                out.write("    pop rax\n")
                out.write("    test rax, rax\n")
                out.write("    jz addr_%d\n" % op.jump_to)
            elif op.action == OperandId.ELSE:
                out.write("    jmp addr_%d\n" % op.jump_to)
            elif op.action == OperandId.FI:
                out.write("    jmp addr_%d\n" % op.jump_to)
            elif op.action == OperandId.WHILE:
                pass
            elif op.action == OperandId.DO:
                out.write("    pop rax\n")
                out.write("    test rax, rax\n")
                out.write("    jz addr_%d\n" % op.jump_to)
            elif op.action == OperandId.DONE:
                out.write("    jmp addr_%d\n" % op.jump_to)
            elif op.action == OperandId.END:
                assert False, "not implemented"
            elif op.action == OperandId.MEM_ADDR:
                out.write("    push mem\n")
            elif op.action == OperandId.MEM_STORE:
                out.write("    pop rbx\n")
                out.write("    pop rax\n")
                out.write("    mov [rax], bl\n")
            elif op.action == OperandId.MEM_LOAD:
                out.write("    pop rax\n")
                out.write("    xor rbx, rbx\n")
                out.write("    mov bl, [rax]\n")
                out.write("    push rbx\n")
            elif op.action == OperandId.SYSCALL:
                out.write("    pop rax\n")
                out.write("    pop rdi\n")
                out.write("    pop rsi\n")
                out.write("    pop rdx\n")
                out.write("    syscall\n")
            elif op.action == OperandId.EXIT:
                out.write("    mov rax, 60\n")
                out.write("    pop rdi\n")
                out.write("    syscall\n")
            else:
                assert False, "Operands is unreachable"
        out.write("addr_%d:\n" % len(program.operands))
        out.write("    mov rax, 60\n")
        out.write("    mov rdi, 0\n")
        out.write("    syscall\n")
        out.write("segment .bss\n")
        out.write("    mem: resb %d\n" % (STR_ALLOCATION_SIZE + MEM_ALLOCATION_SIZE))
        out.write("segment .data\n")
        for index, string in enumerate(str_stack):
            out.write("    str_%d: db " % index)
            for char in string:
                out.write("%d, " % char)
            out.write("\n")
        out.close()
        call_cmd()

def usage(program):
    print("-------------------------------------------")
    print("Usage: %s <SUBCOMMAND> [ARGS]" % program)
    print("SUBCOMMANDS:")
    print("    --compile  (-c) <file>       Compile the program to Assembly")
    print("    --help                       Provide usage details")
    print("    --simulate (-s) <file>       Simulate the program using Python3")
    print("-------------------------------------------")
    exit(1)

def call_cmd():
    print("BUILD:-------------------------------------")
    print("run: nasm -felf64 build/output.asm")
    subprocess.call(["nasm", "-felf64", "build/output.asm"])
    print("run: ld -o build/output build/output.o")
    subprocess.call(["ld", "-o", "build/output", "build/output.o"])
    print("run: build/output")
    print("-------------------------------------------")

if __name__ == "__main__":
    argv = sys.argv
    assert len(argv) >= 1
    (program, argv) = uncons(argv)
    if len(argv) < 1:
        print("ERROR: no subcommand has been provided")
        usage(program)
    (subcommand, argv) = uncons(argv)
    if subcommand == "--simulate" or subcommand == "-s":
        if len(argv) < 1:
            print("ERROR: no input file provided to simulation")
            usage(program)
        (input_file_path, argv) = uncons(argv)
        program = parse_program_from_file(input_file_path)
        simulate_program(program)
    elif subcommand == "--compile" or subcommand == "-c":
        if len(argv) > 1:
            (option, argv) = uncons(argv)
            if option == "--run" or option == "-r":
                (input_file_path, argv) = uncons(argv)
                program = parse_program_from_file(input_file_path)
                compile_program(program)
                subprocess.call(["build/output"])
                print("\n-------------------------------------------")
        elif len(argv) <= 1:
            (input_file_path, argv) = uncons(argv)
            program = parse_program_from_file(input_file_path)
            compile_program(program)
        elif len(argv) < 1:
            print("ERROR: no input file provided to compilation")
            usage(program)
    elif subcommand == "--help":
        usage(program)
    else:
        print("ERROR: unknown nova subcommand `%s`" % (subcommand))
        usage(program)

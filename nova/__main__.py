#!/usr/bin/env python3

import sys
import subprocess

from nova.helpers import uncons, usage
from nova.tokenizer import Tokenizer
from nova.lexer import Lexer
from nova.parser import Parser
from nova.simulator import simulate_program
from nova.compiler import compile_program

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
        tokenizer = Tokenizer(input_file_path)
        lexer = Lexer(tokenizer.raw_tokens)
        parser = Parser(lexer.tokens)
        simulate_program(parser.program)
    elif subcommand == "--compile" or subcommand == "-c":
        if len(argv) > 1:
            (option, argv) = uncons(argv)
            if option == "--run" or option == "-r":
                (input_file_path, argv) = uncons(argv)
                tokenizer = Tokenizer(input_file_path)
                lexer = Lexer(tokenizer.raw_tokens)
                parser = Parser(lexer.tokens)
                compile_program(parser.program)
                subprocess.call(["build/output"])
                print("\n-------------------------------------------")
        elif len(argv) <= 1:
            (input_file_path, argv) = uncons(argv)
            tokenizer = Tokenizer(input_file_path)
            lexer = Lexer(tokenizer.raw_tokens)
            parser = Parser(lexer.tokens)
            compile_program(parser.program)
        elif len(argv) < 1:
            print("ERROR: no input file provided to compilation")
            usage(program)
    elif subcommand == "--help":
        usage(program)
    else:
        print("ERROR: unknown nova subcommand `%s`" % (subcommand))
        usage(program)


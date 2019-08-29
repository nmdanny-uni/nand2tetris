import argparse
import re
import sys
import os
from model import CompilationError
from parser import StatementParser, tokenize
from symbol_table import SymbolTable
from pathlib import Path

def process_file(args, asm_file_name: str):
    """ Processes an .asm file """
    with open(asm_file_name, 'r') as asm_file:
        contents = asm_file.read()
        if args.verbose:
            print(f"Processing file {asm_file.name}")
        tokens = tokenize(contents)
        if args.print_tokens:
            joined = "\n".join(tokens)
            print(joined)

        statements = StatementParser.parse_tokens(tokens)
        if args.print_statements:
            joined = "\n".join(str(stmt) for stmt in statements)
            print(joined)

        tbl = SymbolTable(statements)
        tbl.resolve_symbols(statements)
        if args.print_resolved_statements:
            joined = "\n".join(str(stmt) for stmt in statements)
            print(joined)

        # for verbose output
        len_rom_index = max(len(str(stmt.rom_index)) for stmt in statements)

        hack_filename = args.out if args.out else Path(asm_file.name).with_suffix('.hack')
        with open(hack_filename, 'w') as hack_file:
            for stmt in statements:
                if args.verbose:
                    print(f"[{stmt.rom_index:{len_rom_index}}] {stmt.to_machine_code():16} {stmt}")
                if stmt.to_machine_code():
                    hack_file.write(stmt.to_machine_code() + '\n')
            if args.verbose:
                print(f"machine code written to {hack_filename}")

def main():
    """ Entry point to program, using command arguments or STDIN to feed an asm file,
        and various flags used for debugging purposes """
    argparser = argparse.ArgumentParser(description="Hack assembler.")
    argparser.add_argument(
        'input',
        help='A hack .asm file, or a directory with .asm files')

    #### the following arguments are for debugging/convenience, not part of the project usage ###
    argparser.add_argument('--print-tokens',
                           action='store_true',
                           help='print to STDOUT the tokenized form of file')
    argparser.add_argument('--print-statements',
                           action='store_true',
                           help='print to STDOUT the statements before symbol resolution')
    argparser.add_argument('--print-resolved-statements',
                           action='store_true',
                           help='print to STDOUT the statements after symbol resolution')

    argparser.add_argument('-o', '--out', default=None,
                           help='specify .hack output path, instead of using default behavior')
    
    argparser.add_argument('-v', '--verbose',
                           action='store_true',
                           help='print to STDOUT the machine code along with debug information')
    #############################################################################################
    args = argparser.parse_args()

    if Path(args.input).is_dir() and args.out:
        raise ValueError("Can't specify an output path for a directory")

    files = [args.input] if Path(args.input).is_file() else Path(args.input).glob("*.asm")
    for asm_file in files:
        try:
            process_file(args, asm_file)
        except CompilationError as err:
            print(f"Compilation error while assembling {asm_file}: {err}")



if __name__ == '__main__':
    main()

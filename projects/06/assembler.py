import argparse
import re
import sys
from parser import StatementParser, tokenize
from symbol_table import SymbolTable


def main():
    """ Entry point to program, using command arguments or STDIN to feed an asm file,
        and various flags used for debugging purposes """
    argparser = argparse.ArgumentParser(description="Hack assembler")
    argparser.add_argument(
        'asm',
        type=argparse.FileType('r'),
        nargs='?',
        default=sys.stdin,
        help='Hack .asm file to be assembled. (Pass as argument or via STDIN)')

    argparser.add_argument('--print-tokens',
                           action='store_true',
                           help='print tokenized form of file')
    argparser.add_argument('--print-statements',
                           action='store_true',
                           help='print statements before symbols')
    argparser.add_argument('--print-resolved-statements',
                           action='store_true',
                           help='print statements after symbol resolution')

    argparser.add_argument('--print-machine-code',
                           action='store_false',
                           help='print the raw machine code(as a string of bits)')
    
    argparser.add_argument('-v', '--verbose',
                           action='store_true',
                           help='include debug information')
    args = argparser.parse_args()

    with args.asm as asm_file:
        contents = asm_file.read()
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

        if args.print_machine_code:
            for stmt in statements:
                st = f"{stmt.to_machine_code():16} {stmt}" if args.verbose else stmt.to_machine_code()
                print(st)


if __name__ == '__main__':
    main()

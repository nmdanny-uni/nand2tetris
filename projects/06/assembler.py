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


if __name__ == '__main__':
    main()

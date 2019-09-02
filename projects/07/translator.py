import argparse
from model import CompilationError
import sys
import logging
from translation_context import TranslationContext

def main():
    """ Entry point to program, using command arguments or STDIN to feed an asm file,
        and various flags used for debugging purposes """
    argparser = argparse.ArgumentParser(description="VM translator to hack .asm")
    argparser.add_argument(
        'input',
        help='A .vm file, or a directory with .vm files')

    argparser.add_argument('-b', '--bootstrap', action='store_true',
                           help='include bootstrap code')

    # we use python's logging class to print debug statements, which are
    # ignored when not in verbose mode (so they won't bother any auto-testers)
    argparser.add_argument('-v', '--verbose',
                           action='store_true',
                           help='print to STDOUT the asm along with debug information')
    args = argparser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.ERROR)
    ctx = TranslationContext(args.bootstrap, args.input)
    ctx.write_asm_file()

if __name__ == '__main__':
    main()

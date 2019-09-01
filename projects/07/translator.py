import argparse
from model import CompilationError
import sys
import logging
from command_factory import CommandFactory, TranslationContext


def main():
    """ Entry point to program, using command arguments or STDIN to feed an asm file,
        and various flags used for debugging purposes """
    argparser = argparse.ArgumentParser(description="VM translator to hack .asm")
    argparser.add_argument(
        'input',
        help='A .vm file, or a directory with .vm files')

    argparser.add_argument('-b', '--bootstrap', action='store_true',
                           help='include bootstrap code')

    #### the following arguments are for debugging/convenience, not part of the project usage ###

    argparser.add_argument('-v', '--verbose',
                           action='store_true',
                           help='print to STDOUT the asm along with debug information')
    #############################################################################################
    args = argparser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.ERROR)
    ctx = TranslationContext(args.bootstrap, args.input)
    ctx.write_asm_file()

if __name__ == '__main__':
    main()

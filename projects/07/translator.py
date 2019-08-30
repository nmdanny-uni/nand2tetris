import argparse
from model import CompilationError
import sys
from parser import parse_file
from pathlib import Path
from command_factory import CommandFactory

COMMAND_FACTORY = CommandFactory()


def process_file(args, vm_file_name: str):
    """ Processes a .vm file """
    if args.verbose:
        print(f"Processing {vm_file_name}")
    commands = parse_file(vm_file_name, COMMAND_FACTORY)
    out_asm_file = args.out if args.out else Path(vm_file_name).with_suffix('.asm')
    with open(out_asm_file, 'w') as asm_file:
        for cmd in commands:
            if args.verbose:
                print(f"{cmd.to_asm()}")
            asm_file.write(cmd.to_asm() + '\n')


def main():
    """ Entry point to program, using command arguments or STDIN to feed an asm file,
        and various flags used for debugging purposes """
    argparser = argparse.ArgumentParser(description="VM translator to hack .asm")
    argparser.add_argument(
        'input',
        help='A .vm file, or a directory with .vm files')

    #### the following arguments are for debugging/convenience, not part of the project usage ###

    argparser.add_argument('-o', '--out', default=None,
                           help='specify .vm output path, instead of using default behavior')

    argparser.add_argument('-v', '--verbose',
                           action='store_true',
                           help='print to STDOUT the asm along with debug information')
    #############################################################################################
    args = argparser.parse_args()

    if Path(args.input).is_dir() and args.out:
        raise ValueError("Can't specify an output path for a directory")

    files = [args.input] if Path(args.input).is_file() else Path(args.input).glob("*.vm")
    for file in files:
        try:
            process_file(args, file)
        except CompilationError as err:
            print(f"Compilation error while translating {file}: {err}",file=sys.stderr)



if __name__ == '__main__':
    main()

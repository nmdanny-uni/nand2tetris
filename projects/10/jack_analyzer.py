
import argparse
import logging
from pathlib import Path

from compilation_engine import CompilationEngine
from tokenizer import Tokenizer
import util
import json
import dataclasses

# parsed program arguments, see main for possibilities
args = None


class JackAnalyzer:
    """ Responsible for driving the compilation process of a jack file or
        directory """
    def __init__(self, path: str):
        """ Creates an analyzer for a .jack file, or a folder containing
            a jack program. """
        self.__files = []
        if Path(path).is_file():
            self.__files.append(path)
        else:
            self.__files.extend(list(Path(path).glob("*.jack")))

    def run(self):
        """ Runs the analyzer, emitting XML and/or JSON files
            depending on the program's args. """
        for file in self.__files:
            try:
                # emit raw tokenizer output
                if args.verbose:
                    tokenizer = Tokenizer(file)
                    tokenizer.emit_tokens_xml()

                engine = CompilationEngine(file)
                engine.run(emit_xml=(not args.compile) or args.verbose,
                           emit_vm=args.compile,
                           emit_json=args.verbose)

            except Exception as ex:
                logging.error(f"Encountered error while processing '{file}')")
                logging.exception(ex)
                raise


def main():
    """ Entry point to program, with support for extra debugging flags if needed """
    argparser = argparse.ArgumentParser(description="Jack analyzer")
    argparser.add_argument(
        'input',
        help='A .jack file, or a directory with .jack files')


    # ignored when not in verbose mode (so they won't bother any auto-testers)
    # in this mode, .xml and .json is always emitted, regardless of the compile
    # flag
    argparser.add_argument('-v', '--verbose',
                           action='store_true',
                           help='print debug information')
    # basically toggles ex11,  in this mode, .xml isn't emitted UNLESS
    # verbose flag is on.
    argparser.add_argument('-c', '--compile',
                           action='store_true',
                           help='emit .vm instead of .xml')
    global args
    args = argparser.parse_args()

    # ensure debug prints are only printed in verbose mode
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.ERROR)

    analyzer = JackAnalyzer(args.input)
    analyzer.run()


if __name__ == '__main__':
    main()

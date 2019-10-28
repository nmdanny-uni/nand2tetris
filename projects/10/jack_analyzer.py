
import argparse
import logging
from pathlib import Path

from compilation_engine import CompilationEngine
from tokenizer import Tokenizer
import util

args = None

class JackAnalyzer:
    def __init__(self, path: str):
        """ Creates an analyzer for a .jack file, or a folder containing
            a jack program. """
        self.__files = []
        if Path(path).is_file():
            self.__files.append(path)
        else:
            self.__files.extend(list(Path(path).glob("*.jack")))

    def run(self):
        """ Runs the analyzer, emitting XML files in the process"""
        for file in self.__files:
            try:
                # emit raw tokenizer output
                if args.verbose:
                    tokenizer = Tokenizer(file)
                    util.write_xml_file(tokenizer.to_xml(), file, "T")

                with CompilationEngine(file) as engine:
                    # emit ex10 .xml
                    if not args.compile:
                        engine.emit_xml(semantic=False)

                    # emit ex11 .xml with semantic information only when debugging
                    if args.compile and args.verbose:
                        engine.emit_xml(semantic=True)

                    # emit ex11 .vm
                    if args.compile:
                        engine.emit_vm()

            except Exception as ex:
                logging.error(f"Encountered error while processing '{file}')")
                logging.exception(ex)


def main():
    """ Entry point to program, with support for extra debugging flags if needed """
    argparser = argparse.ArgumentParser(description="Jack analyzer")
    argparser.add_argument(
        'input',
        help='A .jack file, or a directory with .jack files')


    # we use python's logging class to print debug statements, which are
    # ignored when not in verbose mode (so they won't bother any auto-testers)
    argparser.add_argument('-v', '--verbose',
                           action='store_true',
                           help='print debug information')
    # basically toggles ex11,  in this mode, .xml isn't emitted UNLESS
    # verbose flag is on. (in which case, extra semantic markup will be added
    # too)
    argparser.add_argument('-c', '--compile',
                           action='store_true',
                           help='emit .vm instead of .xml')
    global args
    args = argparser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.ERROR)

    analyzer = JackAnalyzer(args.input)
    analyzer.run()

if __name__ == '__main__':
    main()

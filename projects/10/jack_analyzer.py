
import argparse
import sys
import logging
from tokenizer import Tokenizer
from compilation_engine import CompilationEngine
from pathlib import Path
import util


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
                tokenizer = Tokenizer(file)
                tokens = list(tokenizer.iter_tokens())
                engine = CompilationEngine(tokens)
                util.write_xml_file(tokenizer.to_xml(), file, "T")
                util.write_xml_file(engine.to_xml(), file, "")
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
    args = argparser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.ERROR)

    analyzer = JackAnalyzer(args.input)
    analyzer.run()

if __name__ == '__main__':
    main()

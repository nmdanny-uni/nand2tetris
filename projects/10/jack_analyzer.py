
import argparse
import sys
import logging
from tokenizer import Tokenizer
from pathlib import Path

class JackAnalyzer:
    def __init__(self, input: str):
        pass


def process_path(path: str):
    """ Process a .jack file, or a folder containing .jack files"""
    files = []
    if Path(path).is_file():
        logging.debug(f"Given path is file")
        files.append(path)
    else:
        logging.debug(f"Given path is directory")
        files.extend(Path(path).glob("*.jack"))
    for file in files:
        tokenizer = Tokenizer(file)
        tokenizer.create_xml_file()

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

    process_path(args.input)

if __name__ == '__main__':
    main()
import argparse
import re
import sys
from typing import Dict, List

VARIABLES_MEMORY_LOCATION = 16

DEFAULT_SYMBOL_TABLE = {"R0": 0}


class Statement:
    def __init__(self, line_number: int, asm_line_number: int):
        self.line_number = line_number


class Parser:
    def __init__(self, asm_raw: str):

        tokens = tokenize(asm_raw)
        joined = "\n".join(tokens)
        print(f"tokens:\n=====\n{joined}\n======")
        self._symbol_table: Dict[str, int] = {}
        self._statements: List[Statement] = []
        self._num_asm_lines = 0

    def __create_symbol_table(self):
        pass


COMMENT_REGEX = re.compile(r"//.*")
WHITESPACE_REGEX = re.compile(r"\s+")


def tokenize(asm: str) -> List[str]:
    """
    Given a raw string representing the contents of an ASM file, splits it into
    lines, ignoring whitespace, tabs and comments.
    """
    statements = []
    for line in asm.split(sep="\n"):
        line = re.sub(COMMENT_REGEX, "", line)
        line = re.sub(WHITESPACE_REGEX, "", line)
        if len(line) > 0:
            statements.append(line)
    return statements


def main():
    argparser = argparse.ArgumentParser(description="Hack assembler")
    argparser.add_argument(
        'asm',
        type=argparse.FileType('r'),
        nargs='?',
        default=sys.stdin,
        help='Hack .asm file to be assembled. (Pass as argument or via STDIN)')
    args = argparser.parse_args()

    with args.asm as asm_file:
        contents = asm_file.read()
        parser = Parser(contents)


if __name__ == '__main__':
    main()

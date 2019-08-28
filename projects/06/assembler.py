import argparse
import re
import sys
from typing import Dict, List, Optional

DEFAULT_SYMBOL_TABLE = {
    "R0": 0,
    "R1": 1,
    "R2": 2,
    "R3": 3,
    "R4": 4,
    "R5": 5,
    "R6": 6,
    "R7": 7,
    "R8": 8,
    "R9": 9,
    "R10": 10,
    "R11": 11,
    "R12": 12,
    "R13": 13,
    "R14": 14,
    "R15": 15,
    "SP": 0,
    "LCL": 1,
    "ARG": 2,
    "THIS": 3,
    "THAT": 4,
    "SCREEN": 16384,
    "KBD": 24576
}

# Variables begin from this
VARIABLES_MEMORY_LOCATION = 16


class CompilationError(Exception):
    pass


class Statement:
    """ A statement is any meaningful line in an ASM file """
    def __init__(self, line_number: int, rom_ix: Optional[int] = None):
        """ Creates a statement
        :param line_number: Line number in file where the statement occurred
        :param rom_ix: "Line" number in ROM (like above, ignoring pseudo-statements).
        """
        self.__line_number = line_number
        self.__rom_ix = rom_ix

    @property
    def rom_index(self) -> Optional[int]:
        """ Returns the line number(0 indexed) of this statement in the ROM, that is,
            it's line number after ignoring pseudo statements such as labels.
            Returns None for pseudo-statements
        """
        return self.__rom_ix


class Label(Statement):
    """ A label, which is a pseudo-statement"""
    def __init__(self, line_number: int, label_name: str):
        super().__init__(line_number)
        self.__label_name = label_name

    @property
    def label(self):
        return self.__label_name

    def __str__(self):
        return f"({self.label})"


class AInstruction(Statement):
    """ An A-instruction, containing an address or a variable(to be resolved at later stage)"""
    def __init__(self, line_number: int, rom_ix: int, value: str):
        super().__init__(line_number, rom_ix)
        self.__value = value

    def __str__(self):
        return f"{self.__value}"


class CInstruction(Statement):
    """ A C-instruction"""
    def __init__(self, line_number, rom_ix, contents: str):
        super().__init__(line_number, rom_ix)
        self.__contents = contents

    def __str__(self):
        return f"{self.__contents}"


class StatementParser:
    """
    Class responsible for parsing tokens as statements.
    """
    LABEL_REGEX = re.compile(r"\((\w+)\)")

    AInstruction_REGEX = re.compile(r"@(\w+)")

    @staticmethod
    def parse_tokens(tokens: List[str]) -> List[Statement]:
        """ Parses a list of tokens, yielding a list of Statements"""
        statements: List[Statement] = []
        rom_ix = 0
        for line_num, line in enumerate(tokens):
            match = StatementParser.LABEL_REGEX.match(line)
            if match:
                statements.append(Label(line_num, match.group(1)))
                continue

            match = StatementParser.AInstruction_REGEX.match(line)
            if match:
                statements.append(
                    AInstruction(line_num, rom_ix, match.group(1)))
                rom_ix += 1
                continue

            statements.append(CInstruction(line_num, rom_ix, line))
            rom_ix += 1

        return statements


class Assembler:
    def __init__(self, asm_raw: str):

        self.__tokens = tokenize(asm_raw)
        joined = "\n".join(self.__tokens)
        print(f"tokens:\n=====\n{joined}\n======")
        self.__statements = StatementParser.parse_tokens(self.__tokens)
        joinedStatements = "\n".join(map(str, self.__statements))
        print(f"statements:\n\n{joinedStatements}")

    def __create_symbol_table(self):
        pass


class SymbolTable:
    def __init__(self, statements: List[Statement]):
        self.__table = DEFAULT_SYMBOL_TABLE.copy()
        labels = (stm for stm in statements if stm is Label)
        for label_stm in labels:
            label = label_stm.label()
            if label in self.__table:
                raise CompilationError(
                    f"Label {label_stm.label()} appears multiple times in ASM")
            self.__table[label] = label_stm.asm_line_number()


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
        parser = Assembler(contents)


if __name__ == '__main__':
    main()
    main()

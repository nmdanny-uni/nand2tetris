import argparse
import re
import sys
from typing import Dict, List, Optional
from enum import IntFlag


# The following enums are used as bitfields, their bit representation making up various
# parts of a C-instruction

def bitfield_to_machine_code(enum: IntFlag, width: int) -> str:
    """ Converts an enum instance(that is a bitfield) of a given width(in bits),
        to a string representation of the bits """
    return f"{enum.value:0={width}b}"


class Jump(IntFlag):
    """ A 3-wide bitfield representing jump conditions dependant on ALU output """
    NULL = 0   # in case of missing jump flag
    GE = 1,    # j3: jump if out > 0
    EQ = 2,    # j2: jump if out = 0
    LE = 4     # j1: jump if out < 0


# Maps strings to the jump bitfield
JUMP_ST_TO_BITFIELD: Dict[Optional[str], Jump] = {
    None:  Jump.NULL,
    "JGT": Jump.GE,
    "JEQ": Jump.EQ,
    "JGE": Jump.GE | Jump.EQ,
    "JLT": Jump.LE,
    "JNE": Jump.GE | Jump.LE,
    "JLE": Jump.LE | Jump.EQ,
    "JMP": Jump.GE | Jump.EQ | Jump.LE
}


class Dest(IntFlag):
    """ A 3-wide bitfield representing the destination of an ALU computation """
    M = 1,  # d3: memory referenced at A ("M")
    D = 2,  # d2: D register("D")
    A = 4,  # d1: A register("A")

# Maps strings to dest bitfield
DEST_ST_TO_BITFIELD = {
    "M": Dest.M,
    "D": Dest.D,
    "A": Dest.A,
    "MD": Dest.M | Dest.D,
    "AM": Dest.A | Dest.M,
    "AD": Dest.A | Dest.D,
    "AMD": Dest.A | Dest.M | Dest.D
}

class Comp(IntFlag):
    """ A 7-wide bitfield representing ALU flags """
    NO = 1,   # c6: negate the output
    F = 2,    # c5: Add(if present), otherwise And
    NY = 4,   # c4: negate the second operand
    ZY = 8,   # c3: zero the second operand
    NX = 16,  # c2: negate the first operand
    ZX = 32,  # c1: zero the first operand
    A = 64,   # a: 0 for computations that use ARegister, 1 for those that use the MRegister


class ExtendedALUFlags(IntFlag):
    pass




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
    def __init__(self, rom_ix: int):
        """ Creates a statement
        :param rom_ix: "Line" number in ROM (like above, ignoring pseudo-statements).
        """
        self.__rom_ix = rom_ix

    @property
    def rom_index(self) -> int:
        """ Returns the line number(0 indexed) of this statement in the ROM, that is,
            it's line number after ignoring pseudo statements such as labels.
        """
        return self.__rom_ix


class Label(Statement):
    """ A label, which is a pseudo-statement"""
    def __init__(self, rom_ix: int, label_name: str):
        super().__init__(rom_ix)
        self.__label_name = label_name

    @property
    def label(self):
        return self.__label_name

    def __str__(self):
        return f"({self.label})"


class AInstruction(Statement):
    """ An A-instruction, containing an address or a variable(to be resolved at later stage)"""
    def __init__(self, rom_ix: int, st: str):
        super().__init__(rom_ix)
        self.__str_content = st
        self.__address = int(st) if st.isdigit() else None

    @property
    def string_contents(self):
        return self.__str_content

    @property
    def address(self) -> Optional[int]:
        return self.__address

    @address.setter
    def address(self, address: int):
        self.__address = address

    def __str__(self):
        st = f"@{self.string_contents}"
        if self.address:
            st += f" {self.address}"
        return st


class CInstruction(Statement):
    """ A C-instruction"""
    def __init__(self, rom_ix: int, contents: str,
                 jump: Jump = None, dest: Dest = None,
                 comp: Comp = None, ext: ExtendedALUFlags = None):
        super().__init__(rom_ix)
        self.__contents = contents
        self.__jump = jump
        self.__dest = dest
        self.__comp = comp
        self.__ext = ext

    def __str__(self):
        return f"{self.__contents:^20} {repr(self.__jump):^20}"


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
                statements.append(Label(rom_ix, match.group(1)))
                continue

            match = StatementParser.AInstruction_REGEX.match(line)
            if match:
                statements.append(AInstruction(rom_ix, match.group(1)))
                rom_ix += 1
                continue

            statements.append(CInstructionParser.parse(line, line_num, rom_ix))
            rom_ix += 1

        return statements


class CInstructionParser:
    """ Responsible for parsing the contents of a C instruction """

    # first group contains most of the instruction, second part may include
    # a jump instruction.
    MAIN_PATTERN = re.compile(r"^([^;\s]+)(?:;(.*))?")

    @staticmethod
    def parse(inst: str, line_number: int, rom_ix: int) -> CInstruction:
        match = re.match(CInstructionParser.MAIN_PATTERN, inst)
        if not match:
            raise CompilationError(f"Failed to parse CInstruction \"{inst}\" at line {line_number}")
        jump = JUMP_ST_TO_BITFIELD[match.group(2)]
        return CInstruction(rom_ix, contents=inst, jump=jump, dest=None,
                            comp=None, ext=None)

class SymbolTable:
    """ Symbol table, allowing to resolve variables and labels """
    def __init__(self, statements: List[Statement]):
        """ Creates a symbol table from a list of statements. """
        self.__table = DEFAULT_SYMBOL_TABLE.copy()
        self.__next_var_pos = VARIABLES_MEMORY_LOCATION

        # first pass, we update labels
        for stmt in statements:
            if isinstance(stmt, Label):
                label = stmt.label
                if label in self.__table:
                    raise CompilationError(
                        f"Label {label} appears multiple times in ASM")
                self.__table[label] = stmt.rom_index

        # second pass, we create variables

        for stmt in statements:
            if isinstance(stmt, AInstruction) and stmt.string_contents not in self.__table:
                    self.__table[stmt.string_contents] = self.__next_var_pos
                    self.__next_var_pos += 1

    def resolve_symbols(self, statements: List[Statement]):
        """ Updates addresses of A instructions to refer to their locations"""
        for stmt in statements:
            if isinstance(stmt, AInstruction) and stmt.address is None:
                stmt.address = self.__get_address(stmt.string_contents)

    def __get_address(self, symbol: str) -> int:
        if symbol in self.__table:
            return self.__table[symbol]
        raise CompilationError(f"Couldn't resolve symbol \"{symbol}\"")


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

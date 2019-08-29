
import re
from typing import Dict, List, Optional
from model import *

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


COMP_ST_TO_BITFIELD = {
    "0": Comp.C1 | Comp.C3 | Comp.C5,
    "1": Comp.C1 | Comp.C2 | Comp.C3 | Comp.C4 | Comp.C5 | Comp.C6,
    "-1": Comp.C1 | Comp.C2 | Comp.C3 | Comp.C5,
    "D": Comp.C3 | Comp.C4,
    "A": Comp.C1 | Comp.C2,
    "M": Comp.C1 | Comp.C2 | Comp.A
}


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

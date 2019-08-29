import re
from typing import List, Optional
from model import Jump, Comp, Dest, Statement, AInstruction, CInstruction, Label, CompilationError, ExtendedALUFlags

# detects comments
COMMENT_REGEX = re.compile(r"//.*")

# detects whitespace
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


# Maps jump strings to the jump bitfield
JUMP_ST_TO_BITFIELD = {
    None:  Jump.NULL,
    "JGT": Jump.GE,
    "JEQ": Jump.EQ,
    "JGE": Jump.GE | Jump.EQ,
    "JLT": Jump.LE,
    "JNE": Jump.GE | Jump.LE,
    "JLE": Jump.LE | Jump.EQ,
    "JMP": Jump.GE | Jump.EQ | Jump.LE
}


# Maps destination strings to dest bitfield
DEST_ST_TO_BITFIELD = {
    None: Dest.NULL,
    "M": Dest.M,
    "D": Dest.D,
    "A": Dest.A,
    "MD": Dest.M | Dest.D,
    "AM": Dest.A | Dest.M,
    "AD": Dest.A | Dest.D,
    "AMD": Dest.A | Dest.M | Dest.D
}

# Maps computation strings to comp bitfield, tupled with ALU mode as needed
COMP_ST_TO_BITFIELD = {
    "0": Comp.C1 | Comp.C3 | Comp.C5,
    "1": Comp.C1 | Comp.C2 | Comp.C3 | Comp.C4 | Comp.C5 | Comp.C6,
    "-1": Comp.C1 | Comp.C2 | Comp.C3 | Comp.C5,
    "D": Comp.C3 | Comp.C4,
    "A": Comp.C1 | Comp.C2,
    "M": Comp.C1 | Comp.C2 | Comp.A,
    "!D": Comp.C3 | Comp.C4 | Comp.C6,
    "!A": Comp.C1 | Comp.C2 | Comp.C6,
    "!M": Comp.C1 | Comp.C2 | Comp.C6 | Comp.A,
    "-D": Comp.C3 | Comp.C4 | Comp.C5 | Comp.C6,
    "-A": Comp.C1 | Comp.C2 | Comp.C5 | Comp.C6,
    "-M": Comp.C1 | Comp.C2 | Comp.C5 | Comp.C6 | Comp.A,
    "D+1": Comp.C2 | Comp.C3 | Comp.C4 | Comp.C5 | Comp.C6,
    "A+1": Comp.C1 | Comp.C2 | Comp.C4 | Comp.C5 | Comp.C6,
    "M+1": Comp.C1 | Comp.C2 | Comp.C4 | Comp.C5 | Comp.C6 | Comp.A,
    "D-1": Comp.C3 | Comp.C4 | Comp.C5,
    "A-1": Comp.C1 | Comp.C2 | Comp.C5,
    "M-1": Comp.C1 | Comp.C2 | Comp.C5 | Comp.A,
    "D+A": Comp.C5,
    "D+M": Comp.C5 | Comp.A,
    "D-A": Comp.C2 | Comp.C5 | Comp.C6,
    "D-M": Comp.C2 | Comp.C5 | Comp.C6 | Comp.A,
    "A-D": Comp.C4 | Comp.C5 | Comp.C6,
    "M-D": Comp.C4 | Comp.C5 | Comp.C6 | Comp.A,
    "D&A": Comp.NULL,
    "D&M": Comp.A,
    "D|A": Comp.C2 | Comp.C4 | Comp.C6,
    "D|M": Comp.C2 | Comp.C4 | Comp.C6 | Comp.A
}

# for commutative operators, add a second form (this doesn't seem to appear in
# the book, but is supported by course provided assembler)

COMP_ST_TO_BITFIELD["M+D"] = COMP_ST_TO_BITFIELD["D+M"]
COMP_ST_TO_BITFIELD["M&D"] = COMP_ST_TO_BITFIELD["D&M"]
COMP_ST_TO_BITFIELD["M|D"] = COMP_ST_TO_BITFIELD["D|M"]


COMP_ST_TO_BITFIELD["1+M"] = COMP_ST_TO_BITFIELD["M+1"]
COMP_ST_TO_BITFIELD["1+D"] = COMP_ST_TO_BITFIELD["D+1"]
COMP_ST_TO_BITFIELD["1+A"] = COMP_ST_TO_BITFIELD["A+1"]


# tuple them with normal ALU operation mode field
for (st, bitfield) in COMP_ST_TO_BITFIELD.items():
    COMP_ST_TO_BITFIELD[st] = (bitfield, ExtendedALUFlags.Normal)

# add shift operators
COMP_ST_TO_BITFIELD.update({
    "D<<": (Comp.C1 | Comp.C2, ExtendedALUFlags.Shift),
    "D>>": (Comp.C2, ExtendedALUFlags.Shift),
    "A<<": (Comp.C1, ExtendedALUFlags.Shift),
    "A>>": (Comp.NULL, ExtendedALUFlags.Shift),
    "M<<": (Comp.C1 | Comp.A, ExtendedALUFlags.Shift),
    "M>>": (Comp.A, ExtendedALUFlags.Shift)
})



class StatementParser:
    """
    Class responsible for parsing tokens as statements.
    """
    LABEL_REGEX = re.compile(r"\((.+)\)")

    AInstruction_REGEX = re.compile(r"@(.+)")

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

    # to be used on the first group of above regex, if two groups are parsed,
    # the first includes the destination, and the second includes computation.
    # if only one group is parsed, it includes the computation
    COMP_DEST_PARSER = re.compile(r"^([^=]+)(?:=(.+))?$")

    @staticmethod
    def parse(inst: str, line_number: int, rom_ix: int) -> CInstruction:
        match = re.match(CInstructionParser.MAIN_PATTERN, inst)
        if not match:
            raise CompilationError(f"Failed to parse CInstruction \"{inst}\" at line {line_number}")
        jump = JUMP_ST_TO_BITFIELD[match.group(2)]

        dest_st = None
        comp_dest_match = re.match(CInstructionParser.COMP_DEST_PARSER, match.group(1))
        if comp_dest_match.group(2):
            dest_st = comp_dest_match.group(1)
            comp_st = comp_dest_match.group(2)
        else:
            comp_st = comp_dest_match.group(1)

        if dest_st not in DEST_ST_TO_BITFIELD:
            raise CompilationError(f"Failed to parse CInstruction: unsupported destination \"{dest_st}\" at line {line_number}")
        dest = DEST_ST_TO_BITFIELD[dest_st]

        if comp_st not in COMP_ST_TO_BITFIELD:
            raise CompilationError(f"Failed to parse CInstruction: unsupported computation \"{comp_st}\" at line {line_number}")
        comp, ext = COMP_ST_TO_BITFIELD[comp_st]

        return CInstruction(rom_ix, contents=inst, jump=jump, dest=dest,
                            comp=comp, ext=ext)

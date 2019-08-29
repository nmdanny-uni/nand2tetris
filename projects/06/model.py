from enum import IntFlag
from typing import Dict, Optional, List




class CompilationError(Exception):
    """ Thrown upon errors in compilation """
    pass


def bitfield_to_machine_code(enum: IntFlag, width: int) -> str:
    """ Converts an enum instance(that is a bitfield) of a given width(in bits),
        to a string representation of the bits """
    return f"{enum.value:0={width}b}"


# The following enums are used as bitfields, their bit representation making up various
# parts of a C-instruction

class Jump(IntFlag):
    """ A 3-wide bitfield representing jump conditions dependant on ALU output """
    NULL = 0   # in case of missing jump flag
    GE = 1,    # j3: jump if out > 0
    EQ = 2,    # j2: jump if out = 0
    LE = 4     # j1: jump if out < 0


class Dest(IntFlag):
    """ A 3-wide bitfield representing the destination of an ALU computation """
    M = 1,  # d3: memory referenced at A ("M")
    D = 2,  # d2: D register("D")
    A = 4,  # d1: A register("A")


class Comp(IntFlag):
    """ A 7-wide bitfield representing ALU flags """
    C6 = NO = 1,   # negate the output
    C5 = F = 2,    # Add(if present), otherwise And
    C4 = NY = 4,   # negate the second operand
    C3 = ZY = 8,   # zero the second operand
    C2 = NX = 16,  # negate the first operand
    C1 = ZX = 32,  # zero the first operand
    A = 64,        # 0 for computations that use ARegister, 1 for those that use the MRegister


class ExtendedALUFlags(IntFlag):
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
    """ A C-instruction """
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


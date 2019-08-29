from enum import IntFlag
from typing import Optional


class CompilationError(Exception):
    """ Thrown upon errors in compilation """
    pass


class HackIntFlag(IntFlag):
    """ An extension of 'IntFlag', which is basically a Python Enum that supports
        bitwise operations, with a method that easily converts it to a string of
        bits
    """
    def to_machine_code(self) -> str:
        """ Converts an instance of this enum to a string representation of
            its bits """
        return f"{self.value:0={self.bit_width}b}"

    @property
    def bit_width(self) -> int:
        """ Number of bits required to represent any value in this bitfield """
        raise NotImplementedError

# The following enums are used as bitfields, their bit representation making up various
# parts of a C-instruction


class Jump(HackIntFlag):
    """ A 3-wide bitfield representing jump conditions dependant on ALU output
        This represents the bits at instruction[0..2] """
    NULL = 0   # in case of missing jump flag
    GE = 1,    # j3: jump if out > 0
    EQ = 2,    # j2: jump if out = 0
    LE = 4     # j1: jump if out < 0

    @property
    def bit_width(self) -> int:
        """ Number of bits required to represent any value in this bitfield """
        return 3


class Dest(HackIntFlag):
    """ A 3-wide bitfield representing the destination of an ALU computation
        This represents the bits at instruction[3..5] """
    NULL = 0,  # if value isn't stored anywhere
    M = 1,     # d3: memory referenced at A ("M")
    D = 2,     # d2: D register("D")
    A = 4,     # d1: A register("A")

    @property
    def bit_width(self) -> int:
        """ Number of bits required to represent any value in this bitfield """
        return 3

class Comp(HackIntFlag):
    """ A 7-wide bitfield representing ALU flags
        This represents the bits at instruction[6..12]
    """
    # note, in extended (mult/shift) operation, these flags have different meanings.
    NULL = 0,      # for an and instruction
    C6 = NO = 1,   # negate the output
    C5 = F = 2,    # Add(if present), otherwise And
    C4 = NY = 4,   # negate the second operand
    C3 = ZY = 8,   # zero the second operand
    C2 = NX = 16,  # negate the first operand
    C1 = ZX = 32,  # zero the first operand
    A = 64,        # 0 for computations that use ARegister, 1 for those that use the MRegister

    @property
    def bit_width(self) -> int:
        """ Number of bits required to represent any value in this bitfield """
        return 7


class ExtendedALUFlags(HackIntFlag):
    """ A 2-wide bitfield allowing to differ whether we are using the normal ALU
        (as defined in the book), or a mult/shift extension(as defined in moodle)
        This represents the bits at instruction[13..14]
        TODO check if relevant for 2019-2020 course
    """
    Normal = 0b11,  # Normal ALU mode,
    Mult = 0b10,    # multiplication (not implemented, only added for clarification)
    Shift = 0b01    # shift operation


    @property
    def bit_width(self) -> int:
        """ Number of bits required to represent any value in this bitfield """
        return 2



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

    def to_machine_code(self) -> str:
        """ Returns the machine code representation of this statement, as a string of bytes,
            where the MSB is the first character, and LSB is last character """
        raise NotImplementedError

class Label(Statement):
    """ A label, which is a pseudo-statement"""
    def __init__(self, rom_ix: int, label_name: str):
        super().__init__(rom_ix)
        self.__label_name = label_name

    @property
    def label(self):
        return self.__label_name

    def to_machine_code(self) -> str:
        return ""  # labels are pseudostatements, not represented in ROM

    def __str__(self):
        return f"({self.label})"


class AInstruction(Statement):
    """ An A-instruction, containing an address or a variable(to be resolved at later stage)"""
    def __init__(self, rom_ix: int, st: str):
        super().__init__(rom_ix)
        self.__str_content = st
        self.__address = int(st) if st.isdigit() else None

    # Number of bits required to encode any address
    WIDTH_BITS = 15

    @property
    def string_contents(self):
        return self.__str_content

    @property
    def address(self) -> Optional[int]:
        return self.__address

    @address.setter
    def address(self, address: int):
        if address > 2 ** AInstruction.WIDTH_BITS:
            raise CompilationError(f"Address {address} too large")
        self.__address = address

    def to_machine_code(self) -> str:
        if self.address is None:
            raise ValueError(f"Invalid usage: must translate AInstruction symbol before converting to machine code")

        return f"0{self.address:=0{AInstruction.WIDTH_BITS}b}"

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

    def to_machine_code(self) -> str:
        ext = self.__ext.to_machine_code()
        comp = self.__comp.to_machine_code()
        dest = self.__dest.to_machine_code()
        jump = self.__jump.to_machine_code()
        return f"1{ext}{comp}{dest}{jump}"

    def __str__(self):
        return f"{self.__contents}" # {repr(self.__jump):^3} {repr(self.__dest):^3} {repr(self.__comp):^8}"


from typing import List
from model import Statement, Label, AInstruction, CompilationError

# Symbol table of every hack program
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



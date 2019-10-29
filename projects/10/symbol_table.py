from __future__ import annotations
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, Optional
import pandas


class Kind(str, Enum):
    """ Represents the kind of a symbol """
    Static = "static"
    Field = "field"
    Arg = "arg"
    Var = "var"

    @staticmethod
    def from_str(s: str) -> Kind:
        if s == "static":
            return Kind.Static
        if s == "field":
            return Kind.Field
        if s == "arg":
            return Kind.Arg
        if s == "var":
            return Kind.Var
        raise ValueError(f"Unknown variable kind \"{s}\"")


@dataclass(frozen=True)
class Symbol:
    """ Represents a symbol in a symbol table
        It is immutable.
    """
    name: str
    type: str
    kind: Kind
    index: int


class SymbolTable:
    """ A symbol table for a certain class """
    __class_table: Dict[str, Symbol]
    __func_table: Dict[str, Symbol]

    def __init__(self):
        self.__class_table = {}
        self.__func_table = {}

    def start_subroutine(self):
        """ Resets the table's subroutine scope """
        self.__func_table.clear()

    def __get_table_for_kind(self, kind: Kind) -> Dict[str, Symbol]:
        if kind in [Kind.Var, Kind.Arg]:
            return self.__func_table
        return self.__class_table

    def __getitem__(self, item: str) -> Optional[Symbol]:
        """ Obtains the symbol of the given name in the current scope.
            Returns None if the symbol isn't found. """
        if item in self.__func_table:
            return self.__func_table[item]
        if item in self.__class_table:
            return self.__class_table[item]
        return None

    def define(self, name: str, sym_type: str, kind: Kind):
        """ Defines a new symbol in the table """
        index = self.var_count(kind)
        symbol = Symbol(name, sym_type, kind, index)
        self.__get_table_for_kind(symbol.kind)[symbol.name] = symbol

    def var_count(self, kind: Kind) -> int:
        """ Returns the number of variables of given kind """
        table = self.__get_table_for_kind(kind)
        return sum(1 for symbol in table.values() if symbol.kind is kind)

    def __repr__(self):
        class_symbols = [asdict(symbol) for symbol
                         in self.__class_table.values()]
        func_symbols = [asdict(symbol) for symbol
                        in self.__func_table.values()]
        class_df = pandas.DataFrame(class_symbols)
        class_df_st = class_df.to_string(index=False)
        func_df = pandas.DataFrame(func_symbols)
        func_df_st = "Empty" if func_df.empty else func_df.to_string(index=False)
        return f"Class table:\n{class_df_st}]\nFunction table:\n{func_df_st}"


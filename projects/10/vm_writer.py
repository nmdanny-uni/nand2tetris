from __future__ import annotations
from typing import List, Optional
from enum import Enum
from dataclasses import dataclass
import logging
from typing import Iterable, Union
from pathlib import Path
from symbol_table import Symbol, Kind


class Segment(str, Enum):
    Const = "constant",
    Arg = "argument",
    Local = "local",
    Static = "static",
    This = "this",
    That = "that",
    Pointer = "pointer",
    Temp = "temp"

    @staticmethod
    def from_kind(kind: Kind) -> Segment:
        """ Returns the segment that stores the given symbol.
            NOTE: When dealing with a field variable, proper use of the segment
                  requires anchoring the 'this' pointer to the field's belonging
                  class. """
        if kind is Kind.Var:
            return Segment.Local
        if kind is Kind.Arg:
            return Segment.Arg
        if kind is Kind.Static:
            return Segment.Static
        if kind is Kind.Field:
            return Segment.This
        raise ValueError(f"Unsupported kind {kind}")

class Operator(str, Enum):
    Add = "+",
    Sub = "-",
    Neg = "-",
    Eq = "=",
    Gt = ">",
    Lt = "<",
    And = "&",
    Or = "|",
    Not = "~",
    # uses OS implementations
    Mul = "*",
    Div = "/"

    def __repr__(self):
        return self.value

    @property
    def num_args(self) -> int:
        """ Returns the number of arguments used by this operator """
        if self in [Operator.Neg, Operator.Not]:
            return 1
        return 2


    @staticmethod
    def from_symbol(symbol: str, unary: bool) -> Operator:
        """ Converts a string symbol into an operator
            A 'unary' flag may be passed to signify that this is a unary
            operator (to differ between 'neg' and 'sub')
        """
        if unary:
            op = ST_TO_UNARY_OPERATOR.get(symbol, None)
        else:
            op = ST_TO_BINARY_OPERATOR.get(symbol, None)

        if not op:
            op = Operator[symbol.title()]

        if not op:
            raise ValueError(f"\"{symbol}\" is not a valid operator")
        return op


OPERATOR_TO_OS_CALL = {
    Operator.Mul: "Math.multiply",
    Operator.Div: "Math.divide"
}

ST_TO_BINARY_OPERATOR = {
    "+": Operator.Add,
    "-": Operator.Sub,
    "=": Operator.Eq,
    ">": Operator.Gt,
    "<": Operator.Lt,
    "&": Operator.And,
    "|": Operator.Or,
    "*": Operator.Mul,
    "/": Operator.Div
}

ST_TO_UNARY_OPERATOR = {
    "-": Operator.Neg,
    "~": Operator.Not
}

class VMWriter:
    """ Emits VM instructions to a vm file
        This class has a fluent style (you can chain write_ methods), moreover
        it contains higher-level writing methods compared to the proposed API.
     """
    def __init__(self, jack_file: str):
        """ Creates a VM writer for a corresponding jack file path """
        jack_path = Path(jack_file)
        file_name_no_ext = jack_path.stem
        self.__class_name = file_name_no_ext
        self.__vm_path = jack_path.parent / f"{file_name_no_ext}.vm"
        self.__file = open(self.__vm_path, mode='w')
        self.__debugging_buffer: List[str] = []

    def close(self):
        """ Closes the VM file """
        if self.__file:
            self.__file.close()

    def __enter__(self):
        self.__file = open(self.__vm_path, mode='w')

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __write_line(self, st: str):
        """ Writes a single line to the VM file and also logs it"""
        self.__file.write(st+"\n")
        print(st)
        logging.debug(st)

    def write_comment(self, comment: str) -> VMWriter:
        """ Writes a 1-line comment """
        self.__write_line(f"// {comment}")
        return self

    def write_multiline_comment(self, comments: Iterable[str]) -> VMWriter:
        """ writes a multiline comment """
        self.__write_line("/*")
        for comment in comments:
            self.__write_line(f" * {comment}")
        self.__write_line("*/")
        return self

    def write_push(self, segment: Segment, num: int) -> VMWriter:
        """ Writes a VM push command """
        assert num >= 0
        self.__write_line(f"push {segment.value} {num}")
        return self

    def write_pop(self, segment: Segment, num: int) -> VMWriter:
        """ Writes a VM pop command """
        assert num >= 0
        self.__write_line(f"pop {segment.value} {num}")
        return self

    def write_arithmetic(self, operator: Operator) -> VMWriter:
        """ Writes a VM arithmetic command"""
        if operator in OPERATOR_TO_OS_CALL:
            os_call = OPERATOR_TO_OS_CALL[operator]
            self.write_call(os_call, 2)
        else:
            self.__write_line(f"{operator.name.lower()}")
        return self

    def write_label(self, label: str) -> VMWriter:
        """ Writes a label """
        self.__write_line(f"label {label}")
        return self

    def write_goto(self, label: str) -> VMWriter:
        """ Writes a goto command """
        self.__write_line(f"goto {label}")
        return self

    def write_if_goto(self, label: str) -> VMWriter:
        """ Writes an if-goto statement"""
        self.__write_line(f"if-goto {label}")
        return self

    def write_call(self, func: str, num_args: int) -> VMWriter:
        """ Writes a call instruction"""
        assert num_args >= 0
        self.__write_line(f"call {func} {num_args}")
        return self

    def write_function(self, func_name: str, num_args: int) -> VMWriter:
        """ Writes a function declaration"""
        assert num_args >= 0
        self.__write_line(f"function {func_name} {num_args}")
        return self

    def write_return(self) -> VMWriter:
        """ Writes a return instruction """
        self.__write_line("return")
        return self

    ##################################################
    # the following are higher level writing methods #

    def write_class_anchor(self):
        """ Writes a command to pop the head of the stack(assumed to be a
            pointer to an object) to pointer[0] segment, so that push/pop
            operations to the 'this' segment will affect that object.
            """
        self.write_pop(Segment.Pointer, 0)
        return self

    def write_array_anchor(self) -> VMWriter:
        """ Writes a command to pop the head of the stack(assumed to be a
            pointer to an array cell) to pointer[1] segment, so that push/pop
            operations to the 'that' segment will affect that cell.
            """
        self.write_pop(Segment.Pointer, 1)
        return self

    def write_push_symbol(self, symbol: Symbol) -> VMWriter:
        """ Writes command to push a symbol(analyzed identifier) to the top of
            the stack.
            NOTE: Requires the 'this' segment to be properly anchored to the
                  current class
            """
        self.write_push(Segment.from_kind(symbol.kind), symbol.index)
        return self



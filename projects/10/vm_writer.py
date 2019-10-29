from __future__ import annotations
from typing import List, Optional
from enum import Enum
from dataclasses import dataclass
import logging
from typing import Iterable, Union
from pathlib import Path


class Segment(str, Enum):
    Const = "const",
    Arg = "arg",
    Local = "local",
    Static = "static",
    This = "this",
    That = "that",
    Pointer = "pointer",
    Temp = "temp"


class Operator(str, Enum):
    Add = "add",
    Sub = "sub",
    Neg = "neg",
    Eq = "eq",
    Gt = "gt",
    Lt = "lt",
    And = "and",
    Or = "or",
    Not = "not",
    # uses OS implementations
    Mul = "mul",
    Div = "div"

    def num_args(self) -> int:
        """ Returns the number of arguments used by this operator """
        if self in [Operator.Neg, Operator.Not]:
            return 1
        return 2


    @staticmethod
    def from_symbol(symbol: str, unary: bool = False) -> Operator:
        """ Converts a string symbol into an operator
            A 'unary' flag may be passed to signify that this is a unary
            operator (to differ between 'neg' and 'sub')
        """
        op = None
        if unary:
            op = ST_TO_UNARY_OPERATOR.get(symbol, None)
        else:
            op = ST_TO_BINARY_OPERATOR.get(symbol, None)

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
        This class has a fluent style (you can chain write_ methods)
     """
    def __init__(self, jack_file: str):
        """ Creates a VM writer for a corresponding jack file path """
        jack_path = Path(jack_file)
        file_name_no_ext = jack_path.stem
        self.__class_name = file_name_no_ext
        self.__vm_path = jack_path.parent / f"{file_name_no_ext}.vm"
        self.__file = open(self.__vm_path, mode='w')

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
        #logging.debug(st)

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
        self.__write_line(f"push {segment.name.lower()} {num}")
        return self

    def write_pop(self, segment: Segment, num: int) -> VMWriter:
        """ Writes a VM pop command """
        assert num >= 0
        self.__write_line(f"pop {segment.name.lower()} {num}")
        return self

    def write_arithmetic(self, operator: Union[str, Operator]) -> VMWriter:
        """ Writes a VM arithmetic command"""
        if isinstance(operator, str):
            operator = Operator.from_symbol(operator)
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


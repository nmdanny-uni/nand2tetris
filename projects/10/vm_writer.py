from __future__ import annotations
from typing import List, Optional, Iterable, Union
from enum import Enum
import logging
from jack_types import Kind, Operator, Symbol


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



class VMWriter:
    """ Emits VM instructions to a .vm file
     """
    def __init__(self, path: str):
        """ Creates a VM writer for a corresponding jack file path """
        self.__path = path
        self.__file = open(self.__path, mode='w')
        self.__debugging_buffer: List[str] = []

    def close(self):
        """ Closes the VM file and flushes it to disk """
        if self.__file:
            self.__file.close()

    def __write_line(self, st: str):
        """ Writes a single line to the VM file and also logs it"""
        self.__file.write(st+"\n")
        logging.debug(st)

    def write_comment(self, comment: str) -> VMWriter:
        """ Writes a 1-line comment(only if in debug mode) """
        if logging.getLogger().level is not logging.DEBUG:
            return self
        for line in comment.split("\n"):
            self.__write_line(f"// {line}")
        return self

    def write_multiline_comment(self, comment: str) -> VMWriter:
        """ Writes a multiline comment(only if in debug mode) """
        if logging.getLogger().level is not logging.DEBUG:
            return self
        self.__write_line("/*")
        for line in comment.split("\n"):
            self.__write_line(f" * {line}")
        self.__write_line("*/")
        return self

    def write_push(self, segment: Segment, num: int) -> VMWriter:
        """ Writes a VM push command """
        assert num >= 0
        self.__write_line(f"push {segment.value} {num}")
        return self

    def write_push_symbol(self, symbol: Symbol) -> VMWriter:
        """ Writes command to push a symbol(analyzed identifier) to the top of
            the stack.
            NOTE: Requires the 'this' segment to be properly anchored to the
                  current class
            """
        self.write_push(Segment.from_kind(symbol.kind), symbol.index)
        return self

    def write_push_string(self, st: str) -> VMWriter:
        """ Writes VM commands to create a string literal """
        self.write_push(Segment.Const, len(st))
        self.write_call("String.new", 1)
        for char in st:
            self.write_push(Segment.Const, ord(char))
            self.write_call("String.appendChar", 2)
        return self

    def write_pop(self, segment: Segment, num: int) -> VMWriter:
        """ Writes a VM pop command """
        assert num >= 0
        self.__write_line(f"pop {segment.value} {num}")
        return self

    def write_pop_to_symbol(self, symbol: Symbol) -> VMWriter:
        """ Writes a command to pop the value at the top of the stack, to the
            place occupied by given symbol. """
        self.write_pop(Segment.from_kind(symbol.kind), symbol.index)
        return self

    def write_arithmetic(self, operator: Operator) -> VMWriter:
        """ Writes a VM arithmetic command"""
        os_call = operator.as_os_call()
        if os_call:
            self.write_call(os_call, operator.num_args)
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


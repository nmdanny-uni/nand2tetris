from __future__ import annotations
from jack_types import *
from vm_writer import *
from symbol_table import *
import logging
from dataclasses import dataclass



class JackCompiler:
    """ Responsible for compiling a .jack source file, by recursively
        analyzing a Class object """
    def __init__(self, jack_path: str, clazz: Class):
        """ Initializes the compiler for a given path and a fully parsed
            class """
        self.__symbol_table = SymbolTable()
        self.__writer = VMWriter(jack_path)
        self.__class = clazz

    def run(self):
        """ Runs the compiler, emitting results to a .vm file """
        self.__compile_class()
        self.__writer.close()

    def __compile_class(self):
        clazz = self.__class
        for var in clazz.variable_declarations:
            self.__symbol_table.define(
                name=var.name,
                sym_type=var.type,
                kind=var.kind
            )

        for subroutine in clazz.subroutines:
            self.__compile_subroutine(subroutine)

    def __compile_subroutine(self, subroutine: Subroutine):
        subroutine_name = f"{self.__class.class_name}.{subroutine.name}"
        num_args = len(subroutine.arguments)
        self.__symbol_table.start_subroutine()
        for arg in subroutine.arguments:
            self.__symbol_table.define(
                name=arg.name,
                sym_type=arg.type,
                kind=Kind.Arg
            )

        for var in subroutine.body.variable_declarations:
            assert var.kind is Kind.Var
            self.__symbol_table.define(
                name=var.name,
                sym_type=var.type,
                kind=var.kind
            )

        logging.debug(f"Symbol tables for {subroutine_name}:\n{self.__symbol_table}\n")
        self.__writer.write_function(subroutine_name, num_args)

    def __compile_expression(self, expr: Expression):
        pass
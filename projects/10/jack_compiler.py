from __future__ import annotations
from jack_types import *
from vm_writer import *
from symbol_table import *
import logging
from dataclasses import dataclass, asdict
import json



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
        self.compile_class()
        self.__writer.close()


    def compile_class(self):
        clazz = self.__class
        for var in clazz.variable_declarations:
            self.__symbol_table.define(
                name=var.name,
                sym_type=var.type,
                kind=var.kind
            )

        for subroutine in clazz.subroutines:
            self.compile_subroutine(subroutine)

    def compile_subroutine(self, subroutine: Subroutine):
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
        for statement in subroutine.body.statements:
            self.compile_statement(statement)

    def __debug_comment_operation(self, semantic: Semantic):
        js = json.dumps(asdict(semantic), indent=4).split("\n")
        self.__writer.write_comment(f"compiling {type(semantic)}")
        self.__writer.write_multiline_comment(js)

    def compile_statement(self, statement: Statement):
        self.__debug_comment_operation(statement)
        if isinstance(statement, IfStatement):
            self.compile_if_statement(statement)
        elif isinstance(statement, DoStatement):
            self.compile_do_statement(statement)
        elif isinstance(statement, LetStatement):
            self.compile_let_statement(statement)
        elif isinstance(statement, WhileStatement):
            self.compile_while_statement(statement)
        elif isinstance(statement, ReturnStatement):
            self.compile_return_statement(statement)
        else:
            raise ValueError("Impossible/I forgot a statement?")

    def compile_if_statement(self, statement: IfStatement):
        #raise NotImplementedError("If statement")
        pass

    def compile_do_statement(self, statement: DoStatement):
        # raise NotImplementedError("Do statement")
        pass

    def compile_while_statement(self, statement: WhileStatement):
        # raise NotImplementedError("While statement")
        pass

    def compile_let_statement(self, statement: LetStatement):
        # raise NotImplementedError("Let statement")
        pass

    def compile_return_statement(self, statement: ReturnStatement):
        # raise NotImplementedError("Return statement")
        pass

    KEYWORD_TO_CONST = {
        "null": 0,
        "true": -1,
        "false": 0
    }

    def compile_expression(self, expr: Expression):
        """ Compiles an entire expression AST """
        self.__debug_comment_operation(expr)
        for cur in expr.iter_postorder_dfs():
            self.compile_expression_part(cur)

    def compile_expression_part(self, expr: Expression):
        """ Compiles a single 'part' of an Expression node, that is,
            it ignores children.
        """
        if isinstance(expr, ExpressionOperator):
            self.__writer.write_arithmetic(expr.operator)
        elif isinstance(expr, ExpressionLeaf):
            if isinstance(expr.term, IntegerConstant):
                self.__writer.write_push(Segment.Const, expr.term.value)
            elif isinstance(expr.term, KeywordConstant):
                val = JackCompiler.KEYWORD_TO_CONST[expr.term.value]
                if val < 0:
                    self.__writer \
                        .write_push(Segment.Const, -val)\
                        .write_arithmetic(Operator.Neg)
                else:
                    self.__writer.write_push(Segment.Const, val)
            else:
                raise NotImplementedError(f"TODO handling expression leaves of type {type(expr)}")
        elif isinstance(expr, ExpressionArrayIndexer):
            raise NotImplementedError("TODO array indexing")


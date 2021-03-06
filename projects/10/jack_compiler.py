""" (Ex11) implementation of the compiler """
from __future__ import annotations
from jack_types import *
from vm_writer import *
from symbol_table import *
from util import dataclass_to_json_string


class JackCompiler:
    """ Responsible for compiling a .jack source file, by recursively
        analyzing a Class object and emitting VM instructions. """
    def __init__(self, vm_writer: VMWriter, clazz: Class):
        """ Initializes the compiler for a given path and a fully parsed
            class """
        self.__symbol_table = SymbolTable()
        self.__writer = vm_writer
        self.__class = clazz
        self.__label_count = {}

    def gen_label(self, prefix: str = "") -> str:
        """ Generates a new label for the current subroutine """
        label_ix = self.__label_count.get(prefix, 0)
        self.__label_count[prefix] = label_ix + 1
        return f"{prefix}{label_ix}"

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
        self.__label_count.clear()

        # first step, updating symbol table
        self.__symbol_table.start_subroutine()
        if subroutine.subroutine_type == SubroutineType.Method:
            self.__symbol_table.define(
                name="this",
                sym_type=self.__class.class_name,
                kind=Kind.Arg
            )
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

        # writing the function's body
        num_locals = sum(1 for arg in subroutine.body.variable_declarations
                         if arg.kind is Kind.Var)
        self.__writer.write_function(subroutine.canonical_name, num_locals)

        # Anchoring 'this' to the current object
        if subroutine.subroutine_type == SubroutineType.Method:
            self.__writer.write_comment("Anchoring 'this'")
            self.__writer.write_push(Segment.Arg, 0)
            self.__writer.write_pop(Segment.Pointer, 0)

        # constructing an object instance, this also requires updating the
        # symbol table
        if subroutine.subroutine_type == SubroutineType.Constructor:
            self.__writer.write_comment("Creating object instance and "
                                        "anchoring to 'this")
            self.__writer.write_push(Segment.Const,
                                     self.__class.class_size_in_words)
            self.__writer.write_call("Memory.alloc", 1)
            self.__writer.write_pop(Segment.Pointer, 0)
            self.__symbol_table.define(name="this",
                                       sym_type=self.__class.class_name,
                                       kind=Kind.Field)

        self.__writer.write_comment(f"Symbol tables for "
                                    f"{subroutine.canonical_name}:\n"
                                    f"{self.__symbol_table}\n")
        for statement in subroutine.body.statements:
            self.compile_statement(statement)

    def __analyze_subroutine_call(self, call: SubroutineCall):
        """ Analyzes a subroutine call, updating essential fields """

        if call.subroutine_class is not None:
            # if we already analyzed this call
            return

        if not call.subroutine_class_or_self:
            # this is a local method class
            call.subroutine_class = self.__class.class_name
            call.call_type = SubroutineType.Method
            # the method's "this" is the same as our "this"
            call.subroutine_this = KeywordConstant("this")
        else:
            # either a static or a method call
            symbol = self.__symbol_table[call.subroutine_class_or_self]
            if symbol:
                # method call
                call.subroutine_class = symbol.type
                call.subroutine_this = Identifier(symbol.name)
                call.call_type = SubroutineType.Method
            else:
                # static call
                call.subroutine_class = call.subroutine_class_or_self
                call.call_type = SubroutineType.Function

    def __debug_comment_operation(self, node: ASTNode):
        """ Writes debug information about the object being compiled to
            a comment. (Only while in debug mode) """
        self.__writer.write_comment(f"compiling {type(node)}:")
        self.__writer.write_multiline_comment(
            dataclass_to_json_string(node))
        self.__writer.write_comment('')
        self.__writer.write_comment(repr(node))

    def compile_statements(self, statements: List[Statement]):
        """ Compiles a list of statements"""
        for statement in statements:
            self.compile_statement(statement)

    def compile_statement(self, statement: Statement):
        """ Compiles a statement """
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
        """ Compiles an if (else) statement """
        # generation of labels
        at_end_of_statement = self.gen_label("IF_END")
        condition_failed = at_end_of_statement
        if statement.else_body is not None:
            condition_failed = self.gen_label("IF_FALSE")

        # computing ~condition onto stack
        self.compile_expression(statement.condition)
        self.__writer.write_arithmetic(Operator.Not)
        # go to else body(if exists) or end of statement in case
        # condition failed
        self.__writer.write_if_goto(condition_failed)
        # body of 'if' branch
        self.compile_statements(statement.if_body)
        # skip the 'else branch'(only needed if there is an 'else')
        if statement.else_body is not None:
            self.__writer.write_goto(at_end_of_statement)

        if statement.else_body is not None:
            # body of 'else' branch
            self.__writer.write_label(condition_failed)
            self.compile_statements(statement.else_body)

        self.__writer.write_label(at_end_of_statement)

    def compile_do_statement(self, statement: DoStatement):
        """ Compiles a 'do' statement """
        self.compile_subroutine_call(statement.call)
        # ignore the returned value by dumping it to temp segment
        self.__writer.write_pop(Segment.Temp, 0)

    def compile_while_statement(self, statement: WhileStatement):
        """ Compiles a 'while' statement """
        loop_condition_check = self.gen_label("WHILE_EXP")
        after_loop = self.gen_label("WHILE_END")

        self.__writer.write_label(loop_condition_check)
        self.compile_expression(statement.condition)
        self.__writer.write_arithmetic(Operator.Not)
        # exiting loop if condition doesn't hold
        self.__writer.write_if_goto(after_loop)
        # loop body
        self.compile_statements(statement.body)
        # checking loop condition again
        self.__writer.write_goto(loop_condition_check)

        self.__writer.write_label(after_loop)

    def compile_let_statement(self, statement: LetStatement):
        """ Compiles a let statement """
        assignee = self.__symbol_table[statement.var_name]
        if not assignee:
            raise ValueError(f"Cant perform let on undeclared variable")
        if statement.arr_setter_expr is not None:
            self.compile_expression(statement.arr_setter_expr)
            self.__writer.write_push_symbol(assignee)
            self.__writer.write_arithmetic(Operator.Add)
            # head of stack contains &arr[index_expr]

            self.compile_expression(statement.assignment)
            # now head of stack contains assignment result, lets temporarily
            # move it away to the temp
            self.__writer.write_pop(Segment.Temp, 0)

            # now that head of stack contains &arr[index_expr], we can point
            # 'that' at &arr[index_expr]
            self.__writer.write_pop(Segment.Pointer, 1)
            # finally we assign it with the assignment's result
            self.__writer.write_push(Segment.Temp, 0)
            self.__writer.write_pop(Segment.That, 0)

        else:
            self.compile_expression(statement.assignment)
            self.__writer.write_pop_to_symbol(assignee)

    def compile_return_statement(self, statement: ReturnStatement):
        """ Yet another unnecessary docstring """
        if statement.return_expr is not None:
            self.compile_expression(statement.return_expr)
        else:
            # we are on a void function, we'll ensure we're returning 0
            self.__writer.write_push(Segment.Const, 0)

        self.__writer.write_return()

    def compile_subroutine_call(self, call: SubroutineCall):
        """ Compiles a subroutine, so that at the end of the call, the result
            will be at the head of the stack. """
        self.__analyze_subroutine_call(call)
        self.__debug_comment_operation(call)
        self.__writer.write_comment(f"compiling subroutine call {call}")
        num_args = len(call.arguments)

        # pushing the method's invoker (this/some other identifier)
        if call.call_type is SubroutineType.Method:
            num_args = num_args + 1
            if isinstance(call.subroutine_this, KeywordConstant):
                self.__writer.write_comment("local method(using 'this')")
                self.__writer.write_push(Segment.Pointer, 0)
            elif isinstance(call.subroutine_this, Identifier):
                self.__writer.write_comment("external method")
                symbol = self.__symbol_table[call.subroutine_this.name]
                assert symbol is not None
                self.__writer.write_push_symbol(symbol)
            else:
                raise ValueError("Impossible")
        else:
            self.__writer.write_comment("static(function/constructor)")
        for arg in call.arguments:
            self.compile_expression(arg)

        self.__writer.write_call(call.canonical_name, num_args)

    KEYWORD_TO_CONST = {
        "null": 0,
        "true": -1,
        "false": 0
    }

    def compile_expression(self, expr: Union[Expression, Term]):
        """ Recursive function for compiling an expression/term. This has the
            contract of ending with the expression's result at the head of the
            stack """
        self.__debug_comment_operation(expr)

        if isinstance(expr, Term):
            self.compile_term(expr)
            return

        if len(expr.elements) == 1:
            return self.compile_expression(expr.elements[0])

        if len(expr.elements) >= 3 and isinstance(expr.elements[1], Operator):
            assert isinstance(expr.elements[0], Term)
            assert isinstance(expr.elements[2], Term)

            # convert everything to the right of the operator to an expression
            # object so we'll be able to handle it recursively
            right_expr = Expression(elements=expr.elements[2:])

            self.compile_expression(expr.elements[0])
            self.compile_expression(right_expr)
            self.__writer.write_arithmetic(expr.elements[1])
            return

        raise ValueError("Impossible, all other scenarios were handled")

    def compile_term(self, term: Term):
        """ Compiles a single term"""
        if isinstance(term, Parentheses):
            self.compile_expression(term.expr)
        elif isinstance(term, UnaryOp):
            self.compile_term(term.term)
            self.__writer.write_arithmetic(term.operator)
        elif isinstance(term, IntegerConstant):
            self.__writer.write_push(Segment.Const, term.value)
        elif isinstance(term, KeywordConstant):
            self.compile_keyword_constant(term)
        elif isinstance(term, Identifier):
            sym = self.__symbol_table[term.name]
            if not sym:
                raise ValueError(f"Expression contains unresolved "
                                 f"identifier \"{term.name}\"")
            self.__writer.write_push_symbol(sym)
        elif isinstance(term, ArrayIndexer):
            self.compile_array_index_term(term)
        elif isinstance(term, StringConstant):
            self.__writer.write_push_string(term.value)
        elif isinstance(term, SubroutineCall):
            self.compile_subroutine_call(term)
        else:
            raise NotImplementedError(f"TODO impl compile term of type {type(term)}")

    def compile_keyword_constant(self, term: KeywordConstant):
        """ Compiles a keyword constant """
        if term.value == "this":
            self.__writer.write_push(Segment.Pointer, 0)
        else:
            num_value = JackCompiler.KEYWORD_TO_CONST[term.value]
            self.__writer.write_push(Segment.Const, abs(num_value))
            if num_value < 0:
                self.__writer.write_arithmetic(Operator.Neg)

    def compile_array_index_term(self, term: ArrayIndexer):
        """ Compiles an array indexing term """
        sym = self.__symbol_table[term.array_var]
        if not sym:
            raise ValueError(f"Expression contains unresolved array "
                             f"identifier \"{term.array_var}\"")
        self.compile_expression(term.index_expr)
        self.__writer.write_push_symbol(sym)
        self.__writer.write_arithmetic(Operator.Add)
        self.__writer.write_pop(Segment.Pointer, 1)
        self.__writer.write_push(Segment.That, 0)



from typing import Optional, NamedTuple, Iterator, List, Dict, Union
from xml.etree import ElementTree as ET
import logging
import dataclasses
import json
import util
from jack_types import *
from tokenizer import Tokenizer
from symbol_table import *
from xml_writer import XmlWriter, with_xml_tag
from jack_compiler import JackCompiler

class CompilationEngine:
    """ Responsible for parsing a single jack file, converting it to
        semantic objects and then compiling them via JackCompiler.
    """

    BUILT_IN_TYPES = ["int", "char", "boolean"]
    OPERATORS = ["+", "-", "*", "/", "&", "|", "<", ">", "="]
    UNARY_OPERATORS = ["-", "~"]
    KEYWORD_CONSTANTS = ["true", "false", "null", "this"]

    def __init__(self, jack_file: str):
        """ Creates and runs the parser over the given token list
        """
        tokenizer = Tokenizer(jack_file)
        self.__jack_file = jack_file
        self.__tokens = list(tokenizer.iter_tokens())
        self.__ix = 0
        self.__symbol_table = SymbolTable()
        self.__xml_writer = XmlWriter()

    def run(self, emit_xml: bool, emit_vm: bool, emit_json: bool):
        """ Runs the compiler

            :param emit_xml Should we emit .xml (if we are on ex10)
            :param emit_vm Should we emit .vm (if we are on ex11)
            :param emit_json Should we emit .json (for debugging)

        """
        self.__ix = 0  # reset the parser, just in case
        self.__xml_writer.reset()
        clazz = self.parse_class()
        if emit_xml:
            self.__xml_writer.flush_to_disk(self.__jack_file)
        if emit_vm:
            compiler = JackCompiler(self.__jack_file, clazz)
            compiler.run()
        if emit_json:
            util.write_json_file(clazz, self.__jack_file)

    def __has_more_tokens(self) -> bool:
        """ Returns true if there are more tokens to eat """
        return self.__ix < len(self.__tokens)

    def __advance_token(self):
        """ Advances to the next token"""
        if not self.__has_more_tokens():
            raise ValueError("Can't call advance_token as we already exhausted the input tokens")
        self.__ix = self.__ix + 1

    def matches(self, expected_type: str, *contents: str) -> Optional[Token]:
        """ Tries to match the current token with a token identified by the given
            type, and optionally by any of the given contents(if the number of arguments is non
            empty), returning the token, or None if there's a mismatch or no more
            tokens.
        """
        if not self.__has_more_tokens():
            return None
        token = self.__tokens[self.__ix]
        if token.type != expected_type:
            return None
        if len(contents) > 0 and token.contents not in contents:
            return None
        return token

    def eat_optional(self, expected_type: str, *contents: str) -> Optional[Token]:
        """ Same as matches(), but also advances to the next token if the match
            succeeds. """
        token = self.matches(expected_type, *contents)
        if not token:
            return None
        self.__xml_writer.write_leaf(token.type, str(token.contents))
        self.__advance_token()
        return token

    def eat(self, expected_type: str, *contents: str) -> Token:
        """ Similar to eat_optional(), but throws when match fails. """
        token = self.eat_optional(expected_type, *contents)
        if not token:
            raise ValueError(f"Failed match for {expected_type} {contents}")
        return token

    def eat_type(self, include_void=False) -> Token:
        """ Eats either a keyword(representing a built in type) or an identifier
            (representing a class, no validation is done yet to ensure it is
            a valid class)
            May optionally accept the void keyword as-well, which is appropriate
            for function return type. """
        token = self.eat_optional("keyword", *CompilationEngine.BUILT_IN_TYPES)
        if include_void and not token:
            token = self.eat_optional("keyword", "void")
        if not token:
            token = self.eat("identifier")
        return token


    @with_xml_tag("class")
    def parse_class(self) -> Class:
        self.eat("keyword", "class")
        class_name = self.eat("identifier")
        self.eat("symbol", "{")
        clazz = Class(
            class_name=class_name.contents,
            class_file_path=str(self.__jack_file),
            variable_declarations=[],
            subroutines=[]
        )
        while self.matches("keyword", "field", "static"):
            var_dec = self.parse_class_variable_declaration()
            clazz.variable_declarations.extend(var_dec)
        while self.matches("keyword", "constructor", "function", "method"):
            subroutine = self.parse_subroutine()
            clazz.subroutines.append(subroutine)
        self.eat("symbol", "}")
        return clazz

    @with_xml_tag("classVarDec")
    def parse_class_variable_declaration(self) -> List[ClassVariableDeclaration]:
        var_decl_type = self.eat("keyword", "field", "static")
        var_type = self.eat_type()
        var_name = self.eat("identifier")
        clazz = ClassVariableDeclaration(
            name=var_name.contents,
            type=var_type.contents,
            kind=Kind.from_str(var_decl_type.contents)
        )
        classes = [clazz]
        while self.matches("symbol", ","):
            self.eat("symbol", ",")
            next_var_name = self.eat("identifier")
            classes.append(ClassVariableDeclaration(
                name=next_var_name.contents,
                type=clazz.type,
                kind=clazz.kind
            ))
        self.eat("symbol", ";")
        return classes

    @with_xml_tag("subroutineDec")
    def parse_subroutine(self) -> Subroutine:
        subroutine_type = self.eat("keyword", "constructor", "function", "method")
        return_type = self.eat_type(include_void=True)
        var_name = self.eat("identifier")
        self.eat("symbol", "(")
        arguments = self.parse_parameter_list()
        self.eat("symbol", ")")
        body = self.parse_subroutine_body()
        subroutine = Subroutine(
            subroutine_type=SubroutineType.from_str(subroutine_type.contents),
            name=var_name.contents,
            arguments=arguments,
            return_type=(None if return_type.contents == "void"
                         else return_type.contents),
            body=body
        )
        return subroutine

    @with_xml_tag("parameterList")
    def parse_parameter_list(self) -> List[SubroutineArgument]:
        if self.matches("symbol", ")"):
            return []

        params = []
        first_type = self.eat_type()
        first_var = self.eat("identifier")
        params.append(SubroutineArgument(
            name=first_var.contents,
            type=first_type.contents
        ))
        while self.matches("symbol", ","):
            self.eat("symbol", ",")
            next_type = self.eat_type()
            next_var = self.eat("identifier")
            params.append(SubroutineArgument(
                name=next_var.contents,
                type=next_type.contents
            ))

        return params

    @with_xml_tag("subroutineBody")
    def parse_subroutine_body(self) -> SubroutineBody:
        body = SubroutineBody(
            variable_declarations=[],
            statements=[]
        )
        self.eat("symbol", "{")
        while self.matches("keyword", "var"):
            dec = self.parse_var_dec()
            body.variable_declarations.extend(dec)
        statements = self.parse_statements()
        body.statements.extend(statements)
        self.eat("symbol", "}")
        return body

    @with_xml_tag("varDec")
    def parse_var_dec(self) -> List[SubroutineVariableDeclaration]:
        self.eat("keyword", "var")
        var_type = self.eat_type()
        var_name = self.eat("identifier")
        declaration = SubroutineVariableDeclaration(
            name=var_name.contents,
            type=var_type.contents,
            kind=Kind.Var
        )
        declarations = [declaration]
        while self.matches("symbol", ","):
            self.eat("symbol", ",")
            extra_var_name = self.eat("identifier")
            declarations.append(SubroutineVariableDeclaration(
                name=extra_var_name.contents,
                type=declaration.type,
                kind=declaration.kind
            ))
        self.eat("symbol", ";")
        return declarations

    @with_xml_tag("statements")
    def parse_statements(self) -> List[Statement]:
        statements = []
        while True:
            match = self.matches("keyword", "let", "if", "while", "do", "return")
            if not match:
                break
            if match.contents == "let":
                statement = self.parse_let()
                statements.append(statement)
            elif match.contents == "if":
                statement = self.parse_if()
                statements.append(statement)
            elif match.contents == "while":
                statement = self.parse_while()
                statements.append(statement)
            elif match.contents == "do":
                statement = self.parse_do()
                statements.append(statement)
            elif match.contents == "return":
                statement = self.parse_return()
                statements.append(statement)
            else:
                raise ValueError("Impossible(matches function is wrong)")

        return statements

    @with_xml_tag("doStatement")
    def parse_do(self) -> DoStatement:
        self.eat("keyword", "do")
        call = self.parse_subroutine_call()
        self.eat("symbol", ";")
        return DoStatement(call=call)

    def parse_subroutine_call(self, identifier=None) -> SubroutineCall:
        """ Parses a subroutine call, optionally using a pre-existing identifier
            token if it was eaten already.

            NOTE: this returns a list of nodes, not  wrapped in extra structure
                  like the rest of the methods
        """
        if not identifier:
            identifier = self.eat("identifier")

        if self.matches("symbol", "("):
            # we are perform a subroutine call, (where 'identifier' is a
            # local method)
            self.eat("symbol", "(")
            args = self.parse_expression_list()
            self.eat("symbol", ")")
            return SubroutineCall(call_type=SubroutineType.Method, # TODO determine this?
                                  subroutine_name=identifier.contents,
                                  arguments=args)

        elif self.matches("symbol", "."):
            # we are performing a subroutine call, where 'identifier' is a class
            # variable in case of a method call, or class identifier in case of
            # a static method/constructor call
            self.eat("symbol", ".")
            subroutine_name = self.eat("identifier")
            self.eat("symbol", "(")
            args = self.parse_expression_list()
            self.eat("symbol", ")")
            full_name = f"{identifier.contents}.{subroutine_name.contents}"
            return SubroutineCall(call_type=SubroutineType.Method,
                                  subroutine_name=full_name,
                                  arguments=args)
        else:
            raise ValueError("Failed to parse subroutine call")

    @with_xml_tag("letStatement")
    def parse_let(self) -> LetStatement:
        self.eat("keyword", "let")
        var_name = self.eat("identifier")
        var_index_expr = None
        if self.matches("symbol", "["):
            self.eat("symbol", "[")
            var_index_expr = self.parse_expression()
            self.eat("symbol", "]")
        self.eat("symbol", "=")
        assignment_expr = self.parse_expression()
        self.eat("symbol", ";")
        return LetStatement(var_name=var_name.contents,
                            var_index_expr=var_index_expr,
                            assignment=assignment_expr)

    @with_xml_tag("whileStatement")
    def parse_while(self) -> WhileStatement:
        self.eat("keyword", "while")
        self.eat("symbol", "(")
        condition_expr = self.parse_expression()
        self.eat("symbol", ")")

        self.eat("symbol", "{")
        statements_body = self.parse_statements()
        self.eat("symbol", "}")
        return WhileStatement(condition=condition_expr, body=statements_body)

    @with_xml_tag("returnStatement")
    def parse_return(self) -> ReturnStatement:
        self.eat("keyword", "return")
        if self.matches("symbol", ";"):
            self.eat("symbol", ";")
            return ReturnStatement(return_expr=None)
        else:
            return_expr = self.parse_expression()
            self.eat("symbol", ";")
            return ReturnStatement(return_expr=return_expr)

    @with_xml_tag("ifStatement")
    def parse_if(self) -> IfStatement:
        self.eat("keyword", "if")
        self.eat("symbol", "(")
        condition = self.parse_expression()
        self.eat("symbol", ")")
        self.eat("symbol", "{")
        statements = self.parse_statements()
        self.eat("symbol", "}")

        else_statements = None
        if self.matches("keyword", "else"):
            self.eat("keyword", "else")
            self.eat("symbol", "{")
            else_statements = self.parse_statements()
            self.eat("symbol", "}")
        return IfStatement(condition = condition, if_body=statements,
                           else_body=else_statements)

    @with_xml_tag("expression")
    def parse_expression(self) -> Expression:
        term = self.parse_term()
        expr = Expression(term=term, other=[])
        while self.matches("symbol", *CompilationEngine.OPERATORS):
            operator = self.eat("symbol", *CompilationEngine.OPERATORS)
            operator_typed = Operator.from_symbol(operator.contents)
            term = self.parse_term()
            expr.other.append((operator_typed, term))
        return expr

    @with_xml_tag("term")
    def parse_term(self) -> Term:
        # trivial cases where we have an integer/string/keyword constant
        token = self.eat_optional("integerConstant")
        if token:
            return IntegerConstant(int(token.contents))

        token = self.eat_optional("stringConstant")
        if token:
            return StringConstant(token.contents)

        token = self.eat_optional("keyword", *CompilationEngine.KEYWORD_CONSTANTS)
        if token:
            return KeywordConstant(token.contents)

        if self.matches("symbol", "("):
            # we have a sub-expression
            self.eat("symbol", "(")
            expr = self.parse_expression()
            self.eat("symbol", ")")
            return Parentheses(expr=expr)

        if self.matches("symbol", *CompilationEngine.UNARY_OPERATORS):
            # we have a unary operation
            unary_op = self.eat("symbol", *CompilationEngine.UNARY_OPERATORS)
            term = self.parse_term()
            return UnaryOp(operator=Operator.from_symbol(unary_op.contents),
                           term=term)

        # we have 3 different possibilities involving an identifier
        identifier = self.eat("identifier")
        if self.matches("symbol", "["):
            # we are array-indexing (where 'identifier' is an array)
            self.eat("symbol", "[")
            indexer_expr = self.parse_expression()
            self.eat("symbol", "]")
            return ArrayIndexer(array_var=identifier.contents,
                                index_expr=indexer_expr)
        elif self.matches("symbol", "(", "."):
            # we are performing a subroutine call
            return self.parse_subroutine_call(identifier=identifier)
        else:
            # we have a plain variable reference
            return VariableReference(var_name=identifier.contents)

    @with_xml_tag("expressionList")
    def parse_expression_list(self) -> List[Expression]:
        if self.matches("symbol", ")"):
            return []

        expression = self.parse_expression()
        expressions = [expression]
        while self.matches("symbol", ","):
            self.eat("symbol", ",")
            expression = self.parse_expression()
            expressions.append(expression)
        return expressions


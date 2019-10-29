from typing import Optional, NamedTuple, Iterator, List, Dict, Union
from xml.etree import ElementTree as ET
import logging
import dataclasses
import json
import util
from jack_node import *
from tokenizer import Tokenizer
from vm_writer import *
from symbol_table import *
from xml_writer import XmlWriter, with_xml_tag

class CompilationEngine:
    """ Responsible for parsing a list of jack tokens"""

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

    def close(self):
        """ Closes the VM writer"""
        if self.__vm_writer:
            self.__vm_writer.close()

    def __enter__(self):
        self.__vm_writer = VMWriter(self.__jack_file)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def run(self, emit_xml: bool, emit_vm: bool, emit_json: bool):
        self.__ix = 0  # reset the parser, just in case
        self.__xml_writer.reset()
        clazz = self.parse_class()
        if emit_xml:
            self.__xml_writer.flush_to_disk(self.__jack_file)
        if emit_vm:
            self.__vm_writer.write_return()
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
    def parse_class(self) -> NonTerminalNode:
        identifier = self.eat("keyword", "class")
        class_name = self.eat("identifier")
        opener = self.eat("symbol", "{")
        var_decs = []
        semantic = Class(
            class_name=identifier.contents,
            class_file_path=str(self.__jack_file),
            variable_declarations=[],
            subroutines=[]
        )
        while self.matches("keyword", "field", "static"):
            xml, sem = self.parse_class_variable_declaration()
            var_decs.append(xml)
            semantic.variable_declarations.extend(sem)
        subroutines = []
        while self.matches("keyword", "constructor", "function", "method"):
            xml, sem = self.parse_subroutine()
            subroutines.append(xml)
            semantic.subroutines.append(sem)
        closer = self.eat("symbol", "}")
        return NonTerminalNode(type="class", contents=[
            identifier, class_name, opener, *var_decs, *subroutines, closer
        ], semantic=semantic)

    @with_xml_tag("classVarDec")
    def parse_class_variable_declaration(self) -> Tuple[NonTerminalNode,
                                                        List[ClassVariableDeclaration]]:
        var_decl_type = self.eat("keyword", "field", "static")
        var_type = self.eat_type()
        var_name = self.eat("identifier")
        extra_tokens = []
        semantic = ClassVariableDeclaration(
            name=var_name.contents,
            type=var_type.contents,
            kind=Kind.from_str(var_decl_type.contents)
        )
        semantics = [semantic]
        while self.matches("symbol", ","):
            comma = self.eat("symbol", ",")
            next_var_name = self.eat("identifier")
            extra_tokens.extend([comma, next_var_name])
            semantics.append(ClassVariableDeclaration(
                name=next_var_name.contents,
                type=semantic.type,
                kind=semantic.kind
            ))
        semicolon = self.eat("symbol", ";")
        return NonTerminalNode(type="classVarDec", contents=[
            var_decl_type, var_type, var_name, *extra_tokens, semicolon
        ]), semantics

    @with_xml_tag("subroutineDec")
    def parse_subroutine(self) -> Tuple[NonTerminalNode, Subroutine]:
        subroutine_type = self.eat("keyword", "constructor", "function", "method")
        return_type = self.eat_type(include_void=True)
        var_name = self.eat("identifier")
        args_opener = self.eat("symbol", "(")
        param_list, arguments = self.parse_parameter_list()
        args_closer = self.eat("symbol", ")")
        body, body_sem = self.parse_subroutine_body()
        semantic = Subroutine(
            subroutine_type=SubroutineType.from_str(subroutine_type.contents),
            name=var_name.contents,
            arguments=arguments,
            return_type=(None if return_type.contents == "void"
                         else return_type.contents),
            body=body_sem
        )
        return NonTerminalNode(type="subroutineDec", contents=[
            subroutine_type, return_type, var_name, args_opener, param_list, args_closer,
            body
        ]), semantic

    @with_xml_tag("parameterList")
    def parse_parameter_list(self) -> Tuple[NonTerminalNode,
                                            List[SubroutineArgument]]:
        if self.matches("symbol", ")"):
            return NonTerminalNode(type="parameterList", contents=[]), []
        tokens = []
        semantics = []
        first_type = self.eat_type()
        first_var = self.eat("identifier")
        semantics.append(SubroutineArgument(
            name=first_var.contents,
            type=first_type.contents
        ))
        tokens.extend([first_type, first_var])
        while self.matches("symbol", ","):
            comma = self.eat("symbol", ",")
            next_type = self.eat_type()
            next_var = self.eat("identifier")
            tokens.extend([comma, next_type, next_var])
            semantics.append(SubroutineArgument(
                name=next_var.contents,
                type=next_type.contents
            ))

        return NonTerminalNode(type="parameterList", contents=tokens), semantics

    @with_xml_tag("subroutineBody")
    def parse_subroutine_body(self) -> Tuple[NonTerminalNode, SubroutineBody]:
        semantic = SubroutineBody(
            variable_declarations=[],
            statements=[]
        )
        body_opener = self.eat("symbol", "{")
        var_decs = []
        while self.matches("keyword", "var"):
            xml, sem = self.parse_var_dec()
            var_decs.append(xml)
            semantic.variable_declarations.extend(sem)
        statements, statements_sem = self.parse_statements()
        semantic.statements.extend(statements_sem)
        body_closer = self.eat("symbol", "}")
        return NonTerminalNode(type="subroutineBody", contents=[body_opener, *var_decs, statements, body_closer]), semantic

    @with_xml_tag("varDec")
    def parse_var_dec(self) -> Tuple[NonTerminalNode, List[SubroutineVariableDeclaration]]:
        dec = self.eat("keyword", "var")
        var_type = self.eat_type()
        var_name = self.eat("identifier")
        extra_vars = []
        semantic = SubroutineVariableDeclaration(
            name=var_name.contents,
            type=var_type.contents,
            kind=Kind.Var
        )
        semantics = [semantic]
        while self.matches("symbol", ","):
            comma = self.eat("symbol", ",")
            extra_var_name = self.eat("identifier")
            extra_vars.extend([comma, extra_var_name])
            semantics.append(SubroutineVariableDeclaration(
                name=extra_var_name.contents,
                type=semantic.type,
                kind=semantic.kind
            ))
        semicolon = self.eat("symbol", ";")
        return NonTerminalNode(type="varDec", contents=[dec, var_type, var_name, *extra_vars, semicolon]), semantics

    @with_xml_tag("statements")
    def parse_statements(self) -> Tuple[NonTerminalNode, List[Statement]]:
        statements = []
        statements_sem = []
        while True:
            match = self.matches("keyword", "let", "if", "while", "do", "return")
            if not match:
                break
            if match.contents == "let":
                statement, statement_sem = self.parse_let()
                statements.append(statement)
                statements_sem.append(statement_sem)
            elif match.contents == "if":
                statement, statement_sem = self.parse_if()
                statements.append(statement)
                statements_sem.append(statement_sem)
            elif match.contents == "while":
                statement, statement_sem = self.parse_while()
                statements.append(statement)
                statements_sem.append(statement_sem)
            elif match.contents == "do":
                statement, statement_sem = self.parse_do()
                statements.append(statement)
            elif match.contents == "return":
                statement, statement_sem = self.parse_return()
                statements.append(statement)
                statements_sem.append(statement_sem)
            else:
                raise ValueError("Impossible(matches function is wrong)")

        return NonTerminalNode(type="statements", contents=statements), statements_sem

    @with_xml_tag("doStatement")
    def parse_do(self) -> Tuple[NonTerminalNode, DoStatement]:
        do = self.eat("keyword", "do")
        subroutine_call_tokens, call_sem = self.parse_subroutine_call()
        semicolon = self.eat("symbol", ";")
        sem = DoStatement(call=call_sem)
        return NonTerminalNode(type="doStatement", contents=[do, *subroutine_call_tokens, semicolon]), sem

    def parse_subroutine_call(self, identifier=None) -> Tuple[List[Node], SubroutineCall]:
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
            args_opener = self.eat("symbol", "(")
            args, args_sem = self.parse_expression_list()
            args_closer = self.eat("symbol", ")")
            return [identifier, args_opener, args, args_closer], SubroutineCall(call_type=SubroutineType.Method, # TODO determine this?
                                                                                subroutine_name=identifier.contents,
                                                                                arguments=args_sem)

        elif self.matches("symbol", "."):
            # we are performing a subroutine call, where 'identifier' is a class
            # variable in case of a method call, or class identifier in case of
            # a static method/constructor call
            dot = self.eat("symbol", ".")
            subroutine_name = self.eat("identifier")
            args_opener = self.eat("symbol", "(")
            args , args_sem = self.parse_expression_list()
            args_closer = self.eat("symbol", ")")
            subrot_name = f"{identifier.contents}.{subroutine_name.contents}"
            return [identifier, dot, subroutine_name, args_opener, args, args_closer], SubroutineCall(call_type=SubroutineType.Method,
                                                                                                      subroutine_name=subrot_name,
                                                                                                      arguments=args_sem)
        else:
            raise ValueError("Failed to parse subroutine call")

    @with_xml_tag("letStatement")
    def parse_let(self) -> Tuple[NonTerminalNode, LetStatement]:
        tokens = []
        let = self.eat("keyword", "let")
        var_name = self.eat("identifier")
        tokens.extend([let, var_name])
        var_index_expr = None
        if self.matches("symbol", "["):
            index_opener = self.eat("symbol", "[")
            index_expression, var_index_expr = self.parse_expression()
            index_closer = self.eat("symbol", "]")
            tokens.extend([index_opener, index_expression, index_closer])
        equals = self.eat("symbol", "=")
        expression, expr_sem = self.parse_expression()
        semicolon = self.eat("symbol", ";")
        tokens.extend([equals, expression, semicolon])
        sem = LetStatement(var_name=var_name.contents,
                           var_index_expr=var_index_expr,
                           assignment=expr_sem)
        return NonTerminalNode(type="letStatement", contents=tokens), sem

    @with_xml_tag("whileStatement")
    def parse_while(self) -> Tuple[NonTerminalNode, WhileStatement]:
        while_tok = self.eat("keyword", "while")
        cond_opener = self.eat("symbol", "(")
        cond_expr, cond_sem = self.parse_expression()
        cond_closer = self.eat("symbol", ")")

        block_opener = self.eat("symbol", "{")
        statements, statements_sem = self.parse_statements()
        block_closer = self.eat("symbol", "}")
        sem = WhileStatement(condition=cond_sem, body=statements_sem)
        return NonTerminalNode(type="whileStatement", contents=[
            while_tok, cond_opener, cond_expr, cond_closer,
            block_opener, statements, block_closer]), sem

    @with_xml_tag("returnStatement")
    def parse_return(self) -> Tuple[NonTerminalNode, ReturnStatement]:
        return_tok = self.eat("keyword", "return")
        if self.matches("symbol", ";"):
            semicolon = self.eat("symbol", ";")
            return NonTerminalNode(type="returnStatement",
                                   contents=[return_tok, semicolon]), ReturnStatement(return_expr=None)
        else:
            expr, expr_sem = self.parse_expression()
            semicolon = self.eat("symbol", ";")
            return NonTerminalNode(type="returnStatement",
                                   contents=[return_tok, expr, semicolon]), ReturnStatement(return_expr=expr_sem)

    @with_xml_tag("ifStatement")
    def parse_if(self) -> Tuple[NonTerminalNode, IfStatement]:
        if_tok = self.eat("keyword", "if")
        cond_opener = self.eat("symbol", "(")
        cond, cond_sem = self.parse_expression()
        cond_closer = self.eat("symbol", ")")
        block_opener = self.eat("symbol", "{")
        statements, body_sem = self.parse_statements()
        block_closer = self.eat("symbol", "}")
        tokens = [if_tok, cond_opener, cond, cond_closer, block_opener,
                  statements, block_closer]

        else_sem = None
        if self.matches("keyword", "else"):
            else_tok = self.eat("keyword", "else")
            else_opener = self.eat("symbol", "{")
            else_statements, else_sem = self.parse_statements()
            else_closer = self.eat("symbol", "}")
            tokens.extend([else_tok, else_opener, else_statements, else_closer])
        sem = IfStatement(condition = cond_sem, if_body=body_sem, else_body=else_sem)
        return NonTerminalNode(type="ifStatement", contents=tokens), sem

    @with_xml_tag("expression")
    def parse_expression(self) -> Tuple[NonTerminalNode, Expression]:
        term, term_sem = self.parse_term()
        expr = Expression(term=term_sem, other=[])
        tokens = [term]
        while self.matches("symbol", *CompilationEngine.OPERATORS):
            operator = self.eat("symbol", *CompilationEngine.OPERATORS)
            operator_sem = Operator.from_symbol(operator.contents)
            tokens.append(operator)
            term, term_sem = self.parse_term()
            tokens.append(term)
            expr.other.append((operator_sem, term_sem))
        return NonTerminalNode(type="expression", contents=tokens), expr

    @with_xml_tag("term")
    def parse_term(self) -> Tuple[NonTerminalNode, Term]:
        # trivial cases where we have an integer/string/keyword constant
        token = self.eat_optional("integerConstant")
        if token:
            return NonTerminalNode(type="term", contents=[token]), IntegerConstant(int(token.contents))

        token = self.eat_optional("stringConstant")
        if token:
            return NonTerminalNode(type="term", contents=[token]), StringConstant(token.contents)

        token = self.eat_optional("keyword", *CompilationEngine.KEYWORD_CONSTANTS)
        if token:
            return NonTerminalNode(type="term", contents=[token]), KeywordConstant(token.contents)

        if self.matches("symbol", "("):
            # we have a sub-expression
            expr_opener = self.eat("symbol", "(")
            expr, expr_sem = self.parse_expression()
            expr_closer = self.eat("symbol", ")")
            return NonTerminalNode(type="term", contents=[expr_opener, expr, expr_closer]), Parentheses(expr=expr_sem)

        if self.matches("symbol", *CompilationEngine.UNARY_OPERATORS):
            # we have a unary operation
            unary_op = self.eat("symbol", *CompilationEngine.UNARY_OPERATORS)
            term, term_sem = self.parse_term()
            return NonTerminalNode(type="term", contents=[unary_op, term]), UnaryOp(operator=Operator.from_symbol(unary_op.contents),
                                                                                    term=term_sem)

        # we have 3 different possibilities involving an identifier
        identifier = self.eat("identifier")
        if self.matches("symbol", "["):
            # we are array-indexing (where 'identifier' is an array)
            index_opener = self.eat("symbol", "[")
            index_expr, index_expr_sem = self.parse_expression()
            index_closer = self.eat("symbol", "]")
            return NonTerminalNode(type="term", contents=[
                identifier, index_opener, index_expr, index_closer
            ]), ArrayIndexer(array_var=identifier.contents,
                             index_expr=index_expr_sem
                            )
            pass
        elif self.matches("symbol", "(", "."):
            # we are performing a subroutine call
            tokens, call_sem = self.parse_subroutine_call(identifier=identifier)
            return NonTerminalNode(type="term", contents=tokens), call_sem
        else:
            # we have a plain variable reference
            return NonTerminalNode(type="term", contents=[identifier]), VariableReference(var_name=identifier.contents)

    @with_xml_tag("expressionList")
    def parse_expression_list(self) -> Tuple[NonTerminalNode, List[Expression]]:
        if self.matches("symbol", ")"):
            return NonTerminalNode(type="expressionList", contents=[]), []

        expr, expr_sem = self.parse_expression()
        tokens = [expr]
        exprs_sem = [expr_sem]
        while self.matches("symbol", ","):
            tokens.append(self.eat("symbol", ","))
            expr, expr_sem = self.parse_expression()
            tokens.append(expr)
            exprs_sem.append(expr_sem)
        return NonTerminalNode(type="expressionList", contents=tokens), exprs_sem


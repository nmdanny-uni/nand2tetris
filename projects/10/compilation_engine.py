from typing import Optional, NamedTuple, Iterator, List, Dict, Union
from xml.etree import ElementTree as ET
import logging
from jack_node import Node, Token, NonTerminalNode


class CompilationEngine:
    """ Responsible for parsing a list of jack tokens"""

    BUILT_IN_TYPES = ["int", "char", "boolean"]
    OPERATORS = ["+", "-", "*", "/", "&", "|", "<", ">", "="]
    UNARY_OPERATORS = ["-", "~"]
    KEYWORD_CONSTANTS = ["true", "false", "null", "this"]

    def __init__(self, tokens: List[Token]):
        """ Creates and runs the parser over the given token list """
        self.__tokens = tokens
        self.__ix = 0
        self.__parsed_class = self.parse_class()

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

    def parse_class(self) -> NonTerminalNode:
        identifier = self.eat("keyword", "class")
        class_name = self.eat("identifier")
        opener = self.eat("symbol", "{")
        var_decs = []
        while self.matches("keyword", "field", "static"):
            var_decs.append(self.parse_class_variable_declaration())
        subroutines = []
        while self.matches("keyword", "constructor", "function", "method"):
            subroutines.append(self.parse_subroutine())
        closer = self.eat("symbol", "}")
        return NonTerminalNode(type="class", contents=[
            identifier, class_name, opener, *var_decs, *subroutines, closer
        ])

    def parse_class_variable_declaration(self) -> NonTerminalNode:
        var_decl_type = self.eat("keyword", "field", "static")
        var_type = self.eat_type()
        var_name = self.eat("identifier")
        extra_tokens = []
        while self.matches("symbol", ","):
            comma = self.eat("symbol", ",")
            next_var_name = self.eat("identifier")
            extra_tokens.extend([comma, next_var_name])
        semicolon = self.eat("symbol", ";")
        return NonTerminalNode(type="classVarDec", contents=[
            var_decl_type, var_type, var_name, *extra_tokens, semicolon
        ])

    def parse_subroutine(self) -> NonTerminalNode:
        subroutine_type = self.eat("keyword", "constructor", "function", "method")
        return_type = self.eat_type(include_void=True)
        var_name = self.eat("identifier")
        args_opener = self.eat("symbol", "(")
        param_list = self.parse_parameter_list()
        args_closer = self.eat("symbol", ")")
        body = self.parse_subroutine_body()
        return NonTerminalNode(type="subroutineDec", contents=[
            subroutine_type, return_type, var_name, args_opener, param_list, args_closer,
            body
        ])

    def parse_parameter_list(self) -> NonTerminalNode:
        if self.matches("symbol", ")"):
            return NonTerminalNode(type="parameterList", contents=[])
        tokens = []
        first_type = self.eat_type()
        first_var = self.eat("identifier")
        tokens.extend([first_type, first_var])
        while self.matches("symbol", ","):
            comma = self.eat("symbol", ",")
            next_type = self.eat_type()
            next_var = self.eat("identifier")
            tokens.extend([comma, next_type, next_var])

        return NonTerminalNode(type="parameterList", contents=tokens)

    def parse_subroutine_body(self) -> NonTerminalNode:
        body_opener = self.eat("symbol", "{")
        var_decs = []
        while self.matches("keyword", "var"):
            var_decs.append(self.parse_var_dec())
        statements = self.parse_statements()
        body_closer = self.eat("symbol", "}")
        return NonTerminalNode(type="subroutineBody", contents=[body_opener, *var_decs, statements, body_closer])

    def parse_var_dec(self) -> NonTerminalNode:
        dec = self.eat("keyword", "var")
        var_type = self.eat_type()
        var_name = self.eat("identifier")
        extra_vars = []
        while self.matches("symbol", ","):
            comma = self.eat("symbol", ",")
            extra_var_name = self.eat("identifier")
            extra_vars.extend([comma, extra_var_name])
        semicolon = self.eat("symbol", ";")
        return NonTerminalNode(type="varDec", contents=[dec, var_type, var_name, *extra_vars, semicolon])

    def parse_statements(self) -> NonTerminalNode:
        statements = []
        while True:
            match = self.matches("keyword", "let", "if", "while", "do", "return")
            if not match:
                break
            if match.contents == "let":
                statements.append(self.parse_let())
            elif match.contents == "if":
                statements.append(self.parse_if())
            elif match.contents == "while":
                statements.append(self.parse_while())
            elif match.contents == "do":
                statements.append(self.parse_do())
            elif match.contents == "return":
                statements.append(self.parse_return())
            else:
                raise ValueError("Impossible(matches function is wrong)")

        return NonTerminalNode(type="statements", contents=statements)

    def parse_do(self) -> NonTerminalNode:
        do = self.eat("keyword", "do")
        subroutine_call_tokens = self.parse_subroutine_call()
        semicolon = self.eat("symbol", ";")
        return NonTerminalNode(type="doStatement", contents=[do, *subroutine_call_tokens, semicolon])

    def parse_subroutine_call(self, identifier=None) -> List[Node]:
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
            args = self.parse_expression_list()
            args_closer = self.eat("symbol", ")")
            return [identifier, args_opener, args, args_closer]

        elif self.matches("symbol", "."):
            # we are performing a subroutine call, where 'identifier' is a class
            # variable in case of a method call, or class identifier in case of
            # a static method/constructor call
            dot = self.eat("symbol", ".")
            subroutine_name = self.eat("identifier")
            args_opener = self.eat("symbol", "(")
            args = self.parse_expression_list()
            args_closer = self.eat("symbol", ")")
            return [identifier, dot, subroutine_name, args_opener, args, args_closer]
        else:
            raise ValueError("Failed to parse subroutine call")

    def parse_let(self) -> Node:
        tokens = []
        let = self.eat("keyword", "let")
        var_name = self.eat("identifier")
        tokens.extend([let, var_name])
        if self.matches("symbol", "["):
            index_opener = self.eat("symbol", "[")
            index_expression = self.parse_expression()
            index_closer = self.eat("symbol", "]")
            tokens.extend([index_opener, index_expression, index_closer])
        equals = self.eat("symbol", "=")
        expression = self.parse_expression()
        semicolon = self.eat("symbol", ";")
        tokens.extend([equals, expression, semicolon])
        return NonTerminalNode(type="letStatement", contents=tokens)

    def parse_while(self) -> NonTerminalNode:
        while_tok = self.eat("keyword", "while")
        cond_opener = self.eat("symbol", "(")
        cond_expr = self.parse_expression()
        cond_closer = self.eat("symbol", ")")

        block_opener = self.eat("symbol", "{")
        statements = self.parse_statements()
        block_closer = self.eat("symbol", "}")
        return NonTerminalNode(type="whileStatement", contents=[
            while_tok, cond_opener, cond_expr, cond_closer,
            block_opener, statements, block_closer])

    def parse_return(self) -> NonTerminalNode:
        return_tok = self.eat("keyword", "return")
        if self.matches("symbol", ";"):
            semicolon = self.eat("symbol", ";")
            return NonTerminalNode(type="returnStatement",
                                   contents=[return_tok, semicolon])
        else:
            expr = self.parse_expression()
            semicolon = self.eat("symbol", ";")
            return NonTerminalNode(type="returnStatement",
                                   contents=[return_tok, expr, semicolon])

    def parse_if(self) -> NonTerminalNode:
        if_tok = self.eat("keyword", "if")
        cond_opener = self.eat("symbol", "(")
        cond = self.parse_expression()
        cond_closer = self.eat("symbol", ")")
        block_opener = self.eat("symbol", "{")
        statements = self.parse_statements()
        block_closer = self.eat("symbol", "}")
        tokens = [if_tok, cond_opener, cond, cond_closer, block_opener,
                  statements, block_closer]

        if self.matches("keyword", "else"):
            else_tok = self.eat("keyword", "else")
            else_opener = self.eat("symbol", "{")
            else_statements = self.parse_statements()
            else_closer = self.eat("symbol", "}")
            tokens.extend([else_tok, else_opener, else_statements, else_closer])
        return NonTerminalNode(type="ifStatement", contents=tokens)

    def parse_expression(self) -> NonTerminalNode:
        tokens = [self.parse_term()]
        while self.matches("symbol", *CompilationEngine.OPERATORS):
            tokens.append(self.eat("symbol", *CompilationEngine.OPERATORS))
            tokens.append(self.parse_term())
        return NonTerminalNode(type="expression", contents=tokens)

    def parse_term(self) -> NonTerminalNode:
        # trivial cases where we have an integer/string/keyword constant
        token = self.eat_optional("integerConstant")
        if token:
            return NonTerminalNode(type="term", contents=[token])

        token = self.eat_optional("stringConstant")
        if token:
            return NonTerminalNode(type="term", contents=[token])

        token = self.eat_optional("keyword", *CompilationEngine.KEYWORD_CONSTANTS)
        if token:
            return NonTerminalNode(type="term", contents=[token])

        if self.matches("symbol", "("):
            # we have a sub-expression
            expr_opener = self.eat("symbol", "(")
            expr = self.parse_expression()
            expr_closer = self.eat("symbol", ")")
            return NonTerminalNode(type="term", contents=[expr_opener, expr, expr_closer])

        if self.matches("symbol", *CompilationEngine.UNARY_OPERATORS):
            # we have a unary operation
            unary_op = self.eat("symbol", *CompilationEngine.UNARY_OPERATORS)
            term = self.parse_term()
            return NonTerminalNode(type="term", contents=[unary_op, term])

        # we have 3 different possibilities involving an identifier
        identifier = self.eat("identifier")
        if self.matches("symbol", "["):
            # we are array-indexing (where 'identifier' is an array)
            index_opener = self.eat("symbol", "[")
            index_expr = self.parse_expression()
            index_closer = self.eat("symbol", "]")
            return NonTerminalNode(type="term", contents=[
                identifier, index_opener, index_expr, index_closer
            ])
            pass
        elif self.matches("symbol", "(", "."):
            # we are performing a subroutine call
            tokens = self.parse_subroutine_call(identifier=identifier)
            return NonTerminalNode(type="term", contents=tokens)
        else:
            # we have a plain variable reference
            return NonTerminalNode(type="term", contents=[identifier])

    def parse_expression_list(self) -> NonTerminalNode:
        if self.matches("symbol", ")"):
            return NonTerminalNode(type="expressionList", contents=[])

        tokens = [self.parse_expression()]
        while self.matches("symbol", ","):
            tokens.append(self.eat("symbol", ","))
            tokens.append(self.parse_expression())
        return NonTerminalNode(type="expressionList", contents=tokens)

    def to_xml(self) -> ET.Element:
        """ Returns the XML representation of the parse tree represented
            by the file's parse tree """
        return self.__parsed_class.to_xml()

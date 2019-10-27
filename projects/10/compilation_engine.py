from tokenizer import Token
from typing import Optional, NamedTuple, Iterator, List, Dict, Union
from xml.etree import ElementTree as ET
import logging


class Node(NamedTuple):
    type: str
    contents: List['Node']

    def to_xml(self) -> ET.Element:
        root = ET.Element(self.type)
        for node in self.contents:
            root.append(node.to_xml())
        return root


class CompilationEngine:
    def __init__(self, tokens: List[Token]):
        self.__tokens = tokens
        self.__ix = 0
        cls = self.parse_class()
        logging.error(f"class: {cls}")

    def __has_more_tokens(self) -> bool:
        """ Returns true if there are more tokens to eat """
        return self.__ix < len(self.__tokens)

    def __advance_token(self):
        """ Advances to the next token"""
        if not self.__has_more_tokens():
            raise ValueError("Can't call advance_token as we already exhausted the input tokens")
        self.__ix = self.__ix + 1

    def matches(self, expected_type: str, *contents: str) -> Optional[Node]:
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

    BUILT_IN_TYPES = ["int", "char", "boolean"]

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

    def parse_class(self) -> Node:
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
        return Node(type="class", contents=[
            identifier, class_name, opener, *var_decs, *subroutines, closer
        ])

    def parse_class_variable_declaration(self) -> Node:
        var_decl_type = self.eat("keyword", "field", "static")
        var_type = self.eat_type()
        var_name = self.eat("identifier")
        extra_tokens = []
        while (self.matches("symbol", ",")):
            comma = self.eat("symbol", ",")
            next_var_name = self.eat("identifier")
            extra_tokens.extend([comma, next_var_name])
        semicolon = self.eat("symbol", ";")
        return Node(type="classVarDec", contents=[
            var_decl_type, var_type, var_name, extra_tokens, semicolon
        ])

    def parse_subroutine(self) -> Node:
        subroutine_type = self.eat("keyword", "constructor", "function", "method")
        return_type = self.eat_type(include_void=True)
        var_name = self.eat("identifier")
        args_opener = self.eat("symbol", "(")
        param_list = self.parse_parameter_list()
        args_closer = self.eat("symbol", ")")
        body = self.parse_subroutine_body()
        return Node(type="subroutineDec", contents=[
            subroutine_type, return_type, var_name, args_opener, param_list, args_closer,
            body
        ])

    def parse_parameter_list(self) -> Node:
        tokens = []
        if not self.matches("symbol", ")"):
            first_type = self.eat_type()
            first_var = self.eat("identifier")
            tokens.extend([first_type, first_var])
            while self.matches("symbol", ","):
                comma = self.eat("symbol", ",")
                next_type = self.eat_type()
                next_var = self.eat("identifier")
                tokens.extend([comma, next_type, next_var])

        return Node(type="parameterList", contents=tokens)

    def parse_subroutine_body(self) -> Node:
        body_opener = self.eat("symbol", "{")
        var_decs = []
        while (self.matches("keyword", "var")):
            var_decs.append(self.parse_var_dec())
        statements = self.parse_statements()
        body_closer = self.eat("symbol", "}")
        return Node(type="subroutineBody", contents=[body_opener, *var_decs, statements, body_closer])

    def parse_var_dec(self) -> Node:
        dec = self.eat("keyword", "var")
        var_type = self.eat_type()
        var_name = self.eat("identifier")
        extra_vars = []
        while self.matches("symbol", ","):
            comma = self.eat("symbol", ",")
            extra_var_name = self.eat("identifier")
            extra_vars.extend([comma, extra_var_name])
        semicolon = self.eat("symbol", ";")
        return Node(type="varDec", contents=[dec, var_type, var_name, *extra_vars, semicolon])

    def parse_statements(self) -> Node:
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

        return Node(type="statements", contents=statements)

    def parse_do(self) -> Node:
        do = self.eat("keyword", "do")
        subroutine_call = self.parse_subroutine_call()
        semicolon = self.eat("symbol", ";")
        return Node(type="doStatement", contents=[do, subroutine_call, semicolon])

    def parse_subroutine_call(self) -> Node:
        raise NotImplementedError()

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
        return Node(type="letStatement", contents=tokens)

    def parse_while(self) -> Node:
        while_tok = self.eat("keyword", "while")
        opener = self.eat("symbol", "(")
        statements = self.parse_statements()
        closer = self.eat("symbol", ")")
        return Node(type="whileStatement", contents=[
            while_tok, opener, statements, closer])

    def parse_return(self) -> Node:
        return_tok = self.eat("keyword", "return")
        if self.matches("symbol", ";"):
            semicolon = self.eat("symbol", ";")
            return Node(type="returnStatement",
                        contents=[return_tok, semicolon])
        else:
            expr = self.parse_expression()
            semicolon = self.eat("symbol", ";")
            return Node(type="returnStatement",
                        contents=[return_tok, expr, semicolon])

    def parse_if(self) -> Node:
        if_tok = self.eat("keyword", "if")
        cond_opener = self.eat("symbol", "(")
        cond = self.parse_expression()
        cond_closer = self.eat("symbol", ")")
        block_opener = self.eat("symbol", "{")
        statements = self.parse_statements()
        block_closer = self.eat("symbol", "}")
        return Node(type="ifStatement", contents=[
            if_tok, cond_opener, cond, cond_closer,
            block_opener, statements, block_closer])

    def parse_expression(self) -> Node:
        raise NotImplementedError()
        return Node(type="expression", contents=[])

    def parse_term(self) -> Node:
        raise NotImplementedError()
        return Node(type="term", contents=[])

    def compile_expression_list(self) -> Node:
        raise NotImplementedError()
        return Node(type="expressionList", contents=[])

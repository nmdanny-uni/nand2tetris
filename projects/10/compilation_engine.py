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
            raise ValueError("Can't advance to next token, no more tokens available")
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

    def eat_many(self, min_count: int, expected_type: str, *contents: str) -> List[Token]:
        """ Tries to match 'min_count' or more tokens, returning a list of the matched
            tokens. """
        matches: List[Token] = []
        for _ in range(min_count):
            matches.append(self.eat(expected_type, *contents))
        while self.__has_more_tokens():
            next_token = self.eat_optional(expected_type, *contents)
            if not next_token:
                break
            matches.append(next_token)
        return matches

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
        var_type = self.eat("identifier")
        var_names = self.eat_many(1, "identifier")
        return Node(type="classVarDec", contents=[
            var_decl_type, var_type, var_names
        ])

    def parse_subroutine(self) -> Node:
        subroutine_type = self.eat("keyword", "constructor", "function", "method")
        return_type = self.eat
        var_name = self.eat("identifier")
        args_opener = self.eat("symbol", "(")
        param_list = self.parse_parameter_list()
        args_closer = self.eat("symbol", ")")
        body = self.parse_subroutine_body
        return Node(type="subroutineDec", contents=[
            subroutine_type, return_type, var_name, args_opener, param_list, args_closer,
            body
        ])

    def parse_parameter_list(self) -> Node:
        return Node(type="parameterList", contents=[])

    def parse_subroutine_body(self) -> Node:
        return Node(type="subroutineBody", contents=[])

    def parse_var_dec(self) -> Node:
        return Node(type="varDec", contents=[])

    def parse_statements(self) -> Node:
        return Node(type="statements", contents=[])

    def parse_do(self) -> Node:
        return Node(type="do", contents=[])

    def parse_let(self) -> Node:
        return Node(type="let", contents=[])

    def parse_while(self) -> Node:
        return Node(type="while", contents=[])

    def parse_return(self) -> Node:
        return Node(type="return", contents=[])

    def parse_if(self) -> Node:
        return Node(type="if", contents=[])

    def parse_expression(self) -> Node:
        return Node(type="expression", contents=[])

    def parse_term(self) -> Node:
        return Node(type="term", contents=[])

    def compile_expression_list(self) -> Node:
        return Node(type="expressionList", contents=[])

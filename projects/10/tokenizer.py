import logging
import util
from xml.etree import ElementTree as ET
import re
from typing import NamedTuple, Iterator, Union


class Token(NamedTuple):
    """ A token, also doubles as terminal nodes in the compilation engine.  """
    type: str
    contents: Union[str, int]  # int for an integerConstant, string otherwise
    file_pos: int  # used for error reporting, token's position(index) in file

    def to_xml(self) -> ET.Element:
        """ Converts the token to a XML node """
        tag = ET.Element(self.type)
        tag.text = str(self.contents)
        return tag


class Tokenizer:
    """ Responsible for converting a .jack file to a list of tokens """
    KEYWORDS = ['class', 'constructor', 'function', 'method', 'field',
                'static', 'var', 'int', 'char', 'boolean', 'void', 'true',
                'false', 'null', 'this', 'let', 'do', 'if', 'else', 'while',
                'return']

    SYMBOLS = ['{', '}', '(', ')', '[', ']',
               '.', ',', ';', '+', '-', '*', '/',
               '&', '|', '<', '>', '=', '~']

    # so they can be put safely in a regex character class
    ESCAPED_SYMBOLS = [f'\\{symbol}' for symbol in SYMBOLS]

    MULTI_LINE_COMMENT_REGEX = r"(?P<multiComment>/\*[\s\S]*?\*/)"

    STRING_CONSTANT_REGEX = r"(?P<stringConstant>\".*?\")"

    COMMENT_REGEX = r"(?P<comment>//.*)"

    INT_CONSTANT_REGEX = r"(?P<integerConstant>\d+)"

    SYMBOL_REGEX = fr"(?P<symbol>[{''.join(ESCAPED_SYMBOLS)}])"

    KEYWORD_OR_IDENTIFIER_REGEX = r"(?P<keywordOrIdent>\w+)"

    TOKENIZER_REGEX = re.compile('|'.join([
        MULTI_LINE_COMMENT_REGEX, STRING_CONSTANT_REGEX, COMMENT_REGEX,
        INT_CONSTANT_REGEX, SYMBOL_REGEX, KEYWORD_OR_IDENTIFIER_REGEX
    ]))

    def __init__(self, jack_path: str):
        """ Creates a Tokenizer to a given .jack file """
        with open(jack_path, 'r') as file:
            self.__jack_path = jack_path
            self.__content = file.read()

    def iter_tokens(self) -> Iterator[Token]:
        """ Iterates over all tokens in the given jack file """
        for match in re.finditer(Tokenizer.TOKENIZER_REGEX, self.__content):
            token_type = match.lastgroup
            if not token_type:
                raise ValueError(f"Regex match failed")
            contents = match.group(token_type)
            if token_type == "multiComment" or token_type == "comment":
                continue
            if token_type == "integerConstant":
                contents = int(contents)
            elif token_type == "stringConstant":
                contents = contents[1:-1]  # remove quotes
            elif token_type == "keywordOrIdent":
                if contents in Tokenizer.KEYWORDS:
                    token_type = "keyword"
                else:
                    token_type = "identifier"
            yield Token(token_type, contents, match.start())

    def to_xml(self) -> ET.Element:
        """ Returns the XML representation of the tokenized output """
        tokens = ET.Element("tokens")
        for token in self.iter_tokens():
            tokens.append(token.to_xml())
        return tokens

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Union, Any, Optional, Tuple, TypeVar, Iterator
from symbol_table import Kind
from vm_writer import Operator
from enum import Enum


@dataclass
class Token:
    """ A token - a terminal nodes in the parse tree.  """
    type: str
    contents: Union[str, int]  # int for an integerConstant, string otherwise
    file_pos: int  # used for error reporting, token's position(index) in file


class Semantic(ABC):
    """ A semantic object is a node in the program's parse tree consisting of
        essential information for compilation, presented in a type-safe manner
        alongside various enums. It can also define various methods to be used
        for compilation.
        """


@dataclass
class ClassVariableDeclaration:
    name: str
    type: str
    kind: Kind  # must be static or field


@dataclass
class Class:
    class_name: str
    class_file_path: str
    variable_declarations: List[ClassVariableDeclaration]
    subroutines: List[Subroutine]

    @property
    def class_size_in_words(self) -> int:
        """ Returns the number of words(16-bit integers) needed to store
            this class in the heap """
        return len(self.variable_declarations)


class SubroutineType(str, Enum):
    """ Identfies the type of a subroutine, or a subroutine call.
        NOTE: When performing a subroutine call, the caller can't differ between
              a constructor or a function, thus we'll default to providing
              a function. But it doesn't matter, because differing between
              these is only needed when defining a subroutine, not calling it.
    """
    Constructor = "constructor",
    Function = "function",
    Method = "method"

    @staticmethod
    def from_str(s: str) -> SubroutineType:
        if s == "constructor":
            return SubroutineType.Constructor
        if s == "function":
            return SubroutineType.Function
        if s == "method":
            return SubroutineType.Method
        raise ValueError(f"Unknown subroutine type \"{s}\"")


@dataclass
class Subroutine:
    subroutine_type: SubroutineType
    class_name: str
    name: str
    arguments: List[SubroutineArgument]
    return_type: Optional[str]
    body: SubroutineBody

    @property
    def canonical_name(self) -> str:
        """ Returns the full name of the subroutine as per the standard VM
            mapping """
        return f"{self.class_name}.{self.name}"

@dataclass
class SubroutineBody:
    variable_declarations: List[SubroutineVariableDeclaration]
    statements: List[Statement]

@dataclass
class SubroutineVariableDeclaration:
    name: str
    type: str
    kind: Kind  # must be var or arg


@dataclass
class SubroutineArgument:
    name: str
    type: str


@dataclass
class Statement(Semantic):
    pass


@dataclass
class LetStatement(Statement):
    var_name: str
    var_index_expr: Optional[Expression]
    assignment: Expression

    def __repr__(self):
        if self.var_index_expr:
            return f"let {self.var_name}[{self.var_index_expr}] = {self.assignment}"
        return f"let {self.var_name} = {self.assignment}"


@dataclass
class IfStatement(Statement):
    condition: Expression
    if_body: List[Statement]
    else_body: Optional[List[Statement]]

    def __repr__(self):
        body = "\n".join(repr(stmt) for stmt in self.if_body)
        st = f"if ({self.condition}) {{\n {body} }}"
        if self.else_body:
            body = "\n".join(repr(stmt) for stmt in self.else_body)
            st += f" else {{ {body} }}"

        return st

@dataclass
class WhileStatement(Statement):
    condition: Expression
    body: List[Statement]

    def __repr__(self):
        body = "\n".join(repr(stmt) for stmt in self.body)
        return f"while ({self.condition}) {{\n {body} }}"


@dataclass
class DoStatement(Statement):
    call: SubroutineCall

    def __repr__(self):
        return f"do {self.call}"


@dataclass
class ReturnStatement(Statement):
    return_expr: Optional[Expression]

    def __repr__(self):
        return f"return {repr(self.return_expr) if self.return_expr else ''}"


@dataclass
class Term(Semantic):
    pass


@dataclass
class IntegerConstant(Term):
    value: int

    def __repr__(self):
        return str(self.value)


@dataclass
class StringConstant(Term):
    value: str

    def __repr__(self):
        return f"\"{self.value}\""


@dataclass
class KeywordConstant(Term):
    value: str

    def __repr__(self):
        return self.value


@dataclass
class Identifier(Term):
    name: str

    def __repr__(self):
        return self.name


@dataclass
class ArrayIndexer(Term):
    array_var: str
    index_expr: Expression

    def __repr__(self):
        return f"{self.array_var}[{self.index_expr}]"


@dataclass
class UnaryOp(Term):
    operator: Operator
    term: Term

    def __repr__(self):
        return f"{self.operator}{self.term}"


@dataclass
class Parentheses(Term):
    expr: Expression

    def __repr__(self):
        return f"({self.expr})"


@dataclass
class SubroutineCall(Term):

    # determined at parse time, the part before the dot
    # it is None for local method calls
    subroutine_class_or_self: Optional[str]

    # the name after the dot (not a proper function name)
    subroutine_name: str

    # argument expressions, not including the 'this' parameter
    arguments: List[Expression]

    # the subroutines's class, this is filled by JackCompiler as it requires
    # knowledge of the symbol table
    subroutine_class: Optional[str] = None

    # the 'this' variable name(from callers point of view), in case this is
    # a method call. Empty for static function/constructor call
    subroutine_this: Optional[Union[KeywordConstant, Identifier]] = None

    # the type of the call. It will never be 'constructor' as the caller can't
    # determine that(without inspecting other .vm files), and it doesn't matter
    # anyway.
    call_type: Optional[SubroutineType] = None

    @property
    def canonical_name(self) -> str:
        """ The full name of the subroutine according to VM standard
            mapping """
        if not self.subroutine_class:
            raise ValueError("Cannot determine canonical name of subroutine"
                             "call without knowing its class(need to analyze)")
        return f"{self.subroutine_class}.{self.subroutine_name}"

    def __repr__(self):
        name = f"{self.subroutine_name}"
        args = ", ".join(repr(arg) for arg in self.arguments)
        if self.subroutine_class_or_self:
            name = f"{self.subroutine_class_or_self}.{self.subroutine_name}"
        return f"{name}({args})"

@dataclass
class Expression(Semantic):
    """ A parsed expression is a list of terms joined by operators. """
    elements: List[Union[Operator, Term]]

    def __repr__(self):
        return "".join(repr(elm) for elm in self.elements)


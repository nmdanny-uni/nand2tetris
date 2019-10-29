from __future__ import annotations
from abc import ABC
from dataclasses import dataclass
from typing import List, Union, Any, Optional, Tuple
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


class SubroutineType(str, Enum):
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
    name: str
    arguments: List[SubroutineArgument]
    return_type: Optional[str]
    body: SubroutineBody

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
class Statement:
    pass


@dataclass
class LetStatement(Statement):
    var_name: str
    var_index_expr: Optional[Expression]
    assignment: Expression


@dataclass
class IfStatement(Statement):
    condition: Expression
    if_body: List[Statement]
    else_body: Optional[List[Statement]]


@dataclass
class WhileStatement(Statement):
    condition: Expression
    body: List[Statement]


@dataclass
class DoStatement(Statement):
    call: SubroutineCall


@dataclass
class ReturnStatement(Statement):
    return_expr: Optional[Expression]


@dataclass
class Expression(Semantic):
    term: Term
    other: List[Tuple[Operator, Term]]  # operators tupled with terms


@dataclass
class Term(Semantic):
    pass

@dataclass
class IntegerConstant(Term):
    value: int


@dataclass
class StringConstant(Term):
    value: str


@dataclass
class KeywordConstant(Term):
    value: str


@dataclass
class VariableReference(Term):
    var_name: str


@dataclass
class ArrayIndexer(Term):
    array_var: str
    index_expr: Expression


@dataclass
class UnaryOp(Term):
    operator: Operator
    term: Term


@dataclass
class Parentheses(Term):
    expr: Expression


@dataclass
class SubroutineCall(Term):
    call_type: SubroutineType
    subroutine_name: str  # might include the class with a dot
    arguments: List[Expression]

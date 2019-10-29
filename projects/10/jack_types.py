from __future__ import annotations
from abc import ABC
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
class Statement(ABC):
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


@dataclass
class ExpressionNode(ABC):
    """ An AST representation of an expression that may be used for
        compilation purposes. """

    def iter_postorder_dfs(self) -> Iterator[ExpressionNode]:
        """ Iterates over AST node in postorder notation.
            This corresponds to RPN, which maps directly to the order of
            VM instruction calls"""
        if isinstance(self, (ExpressionLeaf, ExpressionArrayIndexer)):
            yield self
        elif isinstance(self, ExpressionOperator):
            for operand in self.operands:
                yield from operand.iter_postorder_dfs()
            yield self

    @staticmethod
    def from_term(term: Term) -> ExpressionNode:
        """ Transforms a term object into a node in the AST, recursively
            transforming inner contents of terms if necessary. """
        if isinstance(term, (KeywordConstant, IntegerConstant, StringConstant,
                             VariableReference)):
            return ExpressionLeaf(term)

        if isinstance(term, UnaryOp):
            return ExpressionOperator(term.operator,
                                      [ExpressionNode.from_term(term.term)])

        if isinstance(term, Parentheses):
            return ExpressionNode.from_expression(term.expr)

        if isinstance(term, ArrayIndexer):
            indexer_expr = ExpressionNode.from_expression(term.index_expr)
            return ExpressionArrayIndexer(term.array_var, indexer_expr)

    @staticmethod
    def from_expression(expr: Expression) -> ExpressionNode:
        """ Transforms an expression(a sequence of terms joined by operators)
            into an AST node. It doesn't handle order of operations(except
             for parenthesized expressions), for example, it'll transform the
             following:
             1 * 2 + 3 / 4 * 5
             into
             ((((1*2)+3)/4)*5)
             """

        if len(expr.other) == 0:
            return ExpressionNode.from_term(expr.term)

        def helper(left: ExpressionNode,
                   rest: List[Tuple[Operator, Term]]) -> ExpressionNode:
            if len(rest) == 0:
                return left

            op, right_term = rest[0]
            right = ExpressionNode.from_term(right_term)
            joined = ExpressionOperator(op, [left, right])

            return helper(joined, rest[1:])

        return helper(ExpressionNode.from_term(expr.term),
                      expr.other)


@dataclass(init=False)
class ExpressionLeaf(ExpressionNode):
    """ A terminal node in the expression AST """
    term: Term

    def __init__(self, term: Term):
        assert isinstance(term, (KeywordConstant, IntegerConstant,
                                 StringConstant, VariableReference))
        self.term = term


@dataclass(init=False)
class ExpressionOperator(ExpressionNode):
    """ A unary/binary operator """
    operator: Operator
    operands: List[ExpressionNode]

    def __init__(self, op: Operator, args: List[ExpressionNode]):
        self.operator = op
        self.operands = args


@dataclass(init=False)
class ExpressionArrayIndexer(ExpressionNode):
    """ An array indexing operation """
    array_name: str
    index_expr: ExpressionNode

    def __init__(self, array_name: str, index_expr: ExpressionNode):
        self.array_name = array_name
        self.index_expr = index_expr







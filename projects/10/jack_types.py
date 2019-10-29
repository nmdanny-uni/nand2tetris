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
class Expression(Semantic):
    """ An AST representation of an expression that may be used for
        compilation purposes. """

    def iter_postorder_dfs(self) -> Iterator[Expression]:
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
    def from_term(term: Term) -> Expression:
        """ Transforms a term object into a node in the AST, recursively
            transforming inner contents of terms if necessary. """
        if isinstance(term, (KeywordConstant, IntegerConstant, StringConstant,
                             VariableReference)):
            return ExpressionLeaf(term)

        if isinstance(term, UnaryOp):
            return ExpressionOperator(term.operator,
                                      [Expression.from_term(term.term)])

        if isinstance(term, Parentheses):
            return term.expr

        if isinstance(term, ArrayIndexer):
            return ExpressionArrayIndexer(term.array_var, term.index_expr)

    @staticmethod
    def from_expression(term: Term,
                        others: List[Tuple[Operator, Term]]
                        ) -> Expression:
        """ Transforms an expression(a sequence of terms joined by operators)
            into an AST node.

             :param term: First term in an expression
             :param others: List of operators followed by terms.

             For example, the expression '1 + 2 + 3' would have
             term = 1, others= [(+,2), (+,3)]

             It doesn't handle order of operations(except for *), for example,
             it'll transform the following:
             1 * 2 + 3 / 4 * 5
             into
             ((((1*2)+3)/4)*5)

             * Parenthesized expressions are correctly handled, and unary
             terms are given precedence

             """

        if len(others) == 0:
            return Expression.from_term(term)

        def helper(left: Expression,
                   rest: List[Tuple[Operator, Term]]) -> Expression:
            if len(rest) == 0:
                return left

            op, right_term = rest[0]
            right = Expression.from_term(right_term)
            joined = ExpressionOperator(op, [left, right])

            return helper(joined, rest[1:])

        return helper(Expression.from_term(term),
                      others)


@dataclass(init=False)
class ExpressionLeaf(Expression):
    """ A terminal node in the expression AST """
    term: Term

    def __init__(self, term: Term):
        assert isinstance(term, (KeywordConstant, IntegerConstant,
                                 StringConstant, VariableReference))
        self.term = term


@dataclass(init=False)
class ExpressionOperator(Expression):
    """ A unary/binary operator """
    operator: Operator
    operands: List[Expression]

    def __init__(self, op: Operator, args: List[Expression]):
        self.operator = op
        self.operands = args


@dataclass(init=False)
class ExpressionArrayIndexer(Expression):
    """ An array indexing operation """
    array_name: str
    index_expr: Expression

    def __init__(self, array_name: str, index_expr: Expression):
        self.array_name = array_name
        self.index_expr = index_expr







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
    class_name: str
    name: str
    arguments: List[SubroutineArgument]
    return_type: Optional[str]
    body: SubroutineBody

    @property
    def canonical_name(self) -> str:
        """ Returns the full name of the subroutine as per the standard VM
            mapping """
        return f"{self.class_name}_{self.name}"

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
class Identifier(Term):
    name: str


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

    @property
    def canonical_name(self) -> str:
        """ The full name of the subroutine according to VM standard
            mapping """
        if not self.subroutine_class:
            raise ValueError("Cannot determine canonical name of subroutine"
                             "call without knowing its class(need to analyze)")
        return f"{self.subroutine_class}.{self.subroutine_name}"


@dataclass
class Expression(Semantic):
    """ An AST representation of an expression that may be used for
        compilation purposes. """

    @abstractmethod
    def iter_postorder_dfs(self) -> Iterator[Expression]:
        """ Iterates over AST node in postorder notation.
            This corresponds to RPN, which maps directly to the order of
            VM instruction calls"""
        raise NotImplementedError("")

    @staticmethod
    def from_term(term: Term) -> Expression:
        """ Transforms a term object into a node in the AST, recursively
            transforming inner contents of terms if necessary. """
        if isinstance(term, (KeywordConstant, IntegerConstant, StringConstant,
                             Identifier)):
            return ExpressionLeaf(term)

        if isinstance(term, UnaryOp):
            return ExpressionOperator(term.operator,
                                      [Expression.from_term(term.term)])

        if isinstance(term, Parentheses):
            return term.expr

        if isinstance(term, ArrayIndexer):
            return ExpressionArrayIndexer(term)

        if isinstance(term, SubroutineCall):
            return ExpressionSubroutineCall(term)

        raise NotImplementedError(f"BUG: forgot to convert {type(term)} to ast")

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
                                 StringConstant, Identifier))
        self.term = term

    def iter_postorder_dfs(self) -> Iterator[Expression]:
        yield self


@dataclass(init=False)
class ExpressionOperator(Expression):
    """ A unary/binary operator """
    operator: Operator
    operands: List[Expression]

    def __init__(self, op: Operator, args: List[Expression]):
        self.operator = op
        self.operands = args

    def iter_postorder_dfs(self) -> Iterator[Expression]:
        for operand in self.operands:
            yield from operand.iter_postorder_dfs()
        yield self


@dataclass(init=False)
class ExpressionArrayIndexer(Expression):
    """ An array indexing operation """
    indexer: ArrayIndexer

    def __init__(self, indexer: ArrayIndexer):
        self.indexer = indexer

    def iter_postorder_dfs(self) -> Iterator[Expression]:
        yield self


@dataclass(init=False)
class ExpressionSubroutineCall(Expression):
    """ A subroutine call expression """
    call: SubroutineCall

    def __init__(self, call: SubroutineCall):
        self.call = call

    def iter_postorder_dfs(self) -> Iterator[Expression]:
        yield self




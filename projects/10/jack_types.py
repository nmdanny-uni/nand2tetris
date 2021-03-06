from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Union, Any, Optional, Tuple, TypeVar, Iterator
from enum import Enum
from util import dataclass_to_json_string


@dataclass
class Token:
    """ A token is the basic block of the program's structure. It is emitted
        by the Tokenizer and is used to construct AST nodes during parsing.
    """
    type: str
    contents: Union[str, int]  # int for an integerConstant, string otherwise


class Kind(str, Enum):
    """ Represents the kind of a symbol """
    Static = "static"
    Field = "field"
    Arg = "arg"
    Var = "var"

    @staticmethod
    def from_str(s: str) -> Kind:
        if s == "static":
            return Kind.Static
        if s == "field":
            return Kind.Field
        if s == "arg":
            return Kind.Arg
        if s == "var":
            return Kind.Var
        raise ValueError(f"Unknown variable kind \"{s}\"")


@dataclass(frozen=True)
class Symbol:
    """ Represents a symbol in a symbol table
        It is immutable.
    """
    name: str
    type: str
    kind: Kind
    index: int


class ASTNode(ABC):
    """ Represents a node in in the program's parse tree consisting of
        essential information for compilation, presented in a type-safe manner
        alongside various enums. It can also define various methods to be used
        for compilation.

        Not all of the object's fields are necessarily populated by JackParser,
        some are updated in a second pass by JackCompiler.
        """

    def __repr__(self):
        return dataclass_to_json_string(self)


@dataclass
class Class(ASTNode):
    """ A class, this is the root of the parse tree"""
    class_name: str
    variable_declarations: List[ClassVariableDeclaration]
    subroutines: List[Subroutine]

    @property
    def class_size_in_words(self) -> int:
        """ Returns the number of words(16-bit integers) needed to store
            this class in the heap """
        return sum(1 for decl in self.variable_declarations
                   if decl.kind is Kind.Field)


@dataclass
class ClassVariableDeclaration(ASTNode):
    """ A class variable declaration, used for creation of a symbol table """
    name: str
    type: str
    kind: Kind  # must be static or field


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
    """ A subroutine (a method, constructor or function)"""
    subroutine_type: SubroutineType
    class_name: str
    name: str
    arguments: List[SubroutineArgument]
    return_type: Optional[str]  # None for void functions
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
    """ A subroutine variable declaration(of 'Var' kind), used to populate the
        the function-scope symbol table """
    name: str
    type: str
    kind: Kind  # must be var or arg


@dataclass
class SubroutineArgument:
    """ A subroutine argument declaration(of 'Arg' kind), used to populate
        the function-scope symbol table """
    name: str
    type: str


@dataclass
class Statement(ASTNode):
    pass


@dataclass
class LetStatement(Statement):
    var_name: str
    arr_setter_expr: Optional[Expression]
    assignment: Expression

    def __repr__(self):
        if self.arr_setter_expr:
            return f"let {self.var_name}[{self.arr_setter_expr}] = {self.assignment}"
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
class Term(ASTNode):
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
    """ A subroutine call. This type is also updated by the JackCompiler """

    # determined at parse time - it is the part before the dot(class identifier
    # in case of static calls, or the invoker/the 'this' parameter of the
    # method)
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
class Expression(ASTNode):
    """ A parsed expression is a list of terms joined by operators. """
    elements: List[Union[Operator, Term]]

    def __repr__(self):
        return "".join(repr(elm) for elm in self.elements)


class Operator(str, Enum):
    """ A unary/binary operator, which might or might not need special OS
        support. """

    # Strings below are only used for debugging purposes
    Add = " + ",
    Sub = " - ",
    Neg = "-",
    Eq = " = ",
    Gt = " > ",
    Lt = " < ",
    And = " & ",
    Or = " | ",
    Not = "~",
    # the following use OS implementation
    Mul = "*",
    Div = "/"

    def __repr__(self):
        return self.value

    @property
    def num_args(self) -> int:
        """ Returns the number of arguments used by this operator """
        if self in [Operator.Neg, Operator.Not]:
            return 1
        return 2

    @staticmethod
    def from_symbol(symbol: str, unary: bool) -> Operator:
        """ Converts a string symbol into an operator
            A 'unary' flag may be passed to signify that this is a unary
            operator (to differ between 'neg' and 'sub')
        """
        if unary:
            return ST_TO_UNARY_OPERATOR[symbol]
        else:
            return ST_TO_BINARY_OPERATOR[symbol]

    def as_os_call(self) -> Optional[str]:
        """ If the given operator is implemented via OS calls, returns the
            name of the OS routine used for it """
        if self is Operator.Mul:
            return "Math.multiply"
        if self is Operator.Div:
            return "Math.divide"


ST_TO_BINARY_OPERATOR = {
    "+": Operator.Add,
    "-": Operator.Sub,
    "=": Operator.Eq,
    ">": Operator.Gt,
    "<": Operator.Lt,
    "&": Operator.And,
    "|": Operator.Or,
    "*": Operator.Mul,
    "/": Operator.Div
}

ST_TO_UNARY_OPERATOR = {
    "-": Operator.Neg,
    "~": Operator.Not
}

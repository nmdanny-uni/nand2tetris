""" This module defines two important type hierarchies:
    - Node, representing a node in the parse tree of a jack program,
      which may be one of:

      - Token, a terminal node
      - NonTerminalNode, a node that may have children

    These have methods that convert them to .XML(a pretty simple operation once
    we've built the entire parse tree)
    in addition, each node has a 'semantic' field, which is used in ex11:

    - Semantic, representing a node in the program's structure, this doesn't
      have unnecessary child-nodes such as commas, colons and other structural
      elements that were required for ex10. It can be thought as a type-safe
      wrapper for Node, and contains properties and methods relevant to the
      ex11 compilation process.

      (For debugging purposes, semantic objects may be included in .xml when
       running via a verbose flag, but usually their main use is compilation)

"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from xml.etree import ElementTree as ET
from typing import List, Union, Any, Optional, Tuple
from symbol_table import Kind
from vm_writer import Operator
from enum import Enum

@dataclass
class Node(ABC):
    """ A node in the parse tree """
    @abstractmethod
    def to_xml(self, semantic: bool = False) -> ET.Element:
        """ Converts the node to an XML node, optionally including
            ex11 semantic information """
        raise NotImplementedError("to_xml() not implemented")



def attach_semantic_info_to_node(node: ET.Element, semantic: Semantic):
    """ A debugging method used to attach semantic information to an XML
        node as attributes or """
    for key, value in asdict(semantic).items():
        node.set(key, str(value))

@dataclass
class Token(Node):
    """ A token - a terminal nodes in the parse tree.  """
    type: str
    contents: Union[str, int]  # int for an integerConstant, string otherwise
    file_pos: int  # used for error reporting, token's position(index) in file
    semantic: Optional[Semantic] = None

    def to_xml(self, semantic: bool = False) -> ET.Element:
        tag = ET.Element(self.type)
        tag.text = str(self.contents)
        if semantic and self.semantic is not None:
            attach_semantic_info_to_node(tag, self.semantic)
        return tag


@dataclass
class NonTerminalNode(Node):
    """ A "non terminal node, which may include several sub-nodes """
    type: str
    contents: List[Node]
    semantic: Optional[Semantic] = None

    def to_xml(self, semantic: bool = False) -> ET.Element:
        root = ET.Element(self.type)
        if semantic and self.semantic is not None:
            attach_semantic_info_to_node(root, self.semantic)
        for node in self.contents:
            root.append(node.to_xml(semantic))
        return root


class Semantic(ABC):
    """ A semantic object is used to enrich a node in the parse tree with
        information that will be used in parsing. It is essentially a cleaner
        version of 'Node' (without unnecessary symbols, e.g colons, commas...)
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

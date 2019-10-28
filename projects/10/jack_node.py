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
from typing import List, Union, Any, Optional
from symbol_table import Kind

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
    statements: List[Statement]

@dataclass
class SubroutineVariableDeclaration:
    name: str
    type: str
    kind: Kind  # must be var or arg

@dataclass
class Statement:
    pass


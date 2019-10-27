from abc import ABC, abstractmethod
from dataclasses import dataclass
from xml.etree import ElementTree as ET
from typing import List, Union


@dataclass
class Node(ABC):
    """ A node in the parse tree """
    @abstractmethod
    def to_xml(self) -> ET.Element:
        """ Converts the node to an XML node """
        raise NotImplementedError("to_xml() not implemented")


@dataclass
class Token(Node):
    """ A token - a terminal nodes in the parse tree.  """
    type: str
    contents: Union[str, int]  # int for an integerConstant, string otherwise
    file_pos: int  # used for error reporting, token's position(index) in file

    def to_xml(self) -> ET.Element:
        """ Converts the token to a XML node """
        tag = ET.Element(self.type)
        tag.text = str(self.contents)
        return tag


@dataclass
class NonTerminalNode(Node):
    """ A "non terminal node, which may include several sub-nodes """
    type: str
    contents: List[Node]

    def to_xml(self) -> ET.Element:
        """ Converts the node to a XML node """
        root = ET.Element(self.type)
        for node in self.contents:
            root.append(node.to_xml())
        return root

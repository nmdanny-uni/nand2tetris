""" This module is responsible for creating commands, it is essentially a
    parsing class. """

from model import CompilationError, Command, Push, Pop, UnaryCommand, BinaryCommand
from segment_factory import SegmentFactory

class CommandFactory:
    """ Responsible for creating command instances"""

    Commands = {
        "neg": UnaryCommand("neg", "-M"),
        "not": UnaryCommand("not", "!M"),
        "add": BinaryCommand("add", "M + D"),
        "sub": BinaryCommand("sub", "M - D"),
        "and": BinaryCommand("and", "M & D"),
        "or": BinaryCommand("or", "M | D")
    }
    
    def __init__(self):
        self.__segment_factory = SegmentFactory()

    def parse_line(self, file_name: str, line: str, line_num: int) -> Command:
        """ Parses a line in the given file, returning a command """
        parts = line.split(sep=" ")
        if len(parts) == 3:
            segment = self.__segment_factory.get_segment(file_name, parts[1])
            if not parts[2].isdigit():
                raise CompilationError(f"expected integer at line {line_num}, got \"{parts[2]}\" instead.")
            if parts[0] == "push":
                return Push(segment, int(parts[2]))
            return Pop(segment, int(parts[2]))

        if len(parts) == 1:
            if not parts[0] in CommandFactory.Commands:
                raise CompilationError(f"Unknown command \"{parts[0]}\" at line {line_num}")
            return CommandFactory.Commands[parts[0]]

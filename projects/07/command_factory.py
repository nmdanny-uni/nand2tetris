""" This module is responsible for creating commands, it is essentially a
    parsing class. """
from model import (CompilationError, Command, Push, Pop, UnaryCommand,
                   BinaryCommand, CompareCommand, CompareType,
                   LabelCommand, GotoCommand, IfGotoCommand,
                   FunctionDefinition, Call, Return)
from segment_factory import SegmentFactory


class CommandFactory:
    """ Responsible for creating command instances. This is essentially a
        parsing class """

    # Maps keywords to more primitive commands(that don't require
    #  context such as function name, or have any arguments)
    Commands = {
        "neg": UnaryCommand("neg", "-M"),
        "not": UnaryCommand("not", "!M"),
        "add": BinaryCommand("add", "M + D"),
        "sub": BinaryCommand("sub", "M - D"),
        "and": BinaryCommand("and", "M & D"),
        "or": BinaryCommand("or", "M | D"),
        "eq": CompareCommand("eq", CompareType.EQ),
        "gt": CompareCommand("gt", CompareType.GT),
        "lt": CompareCommand("lt", CompareType.LT),
    }

    # Branching commands(ex8) that take a parameter, thus we
    # map these strings to those constructors
    ArgCommands = {
        "label": LabelCommand,
        "goto": GotoCommand,
        "if-goto": IfGotoCommand
    }

    def __init__(self):
        self.__segment_factory = SegmentFactory()

    def parse_line(self, file_name: str, function_name: str,
                   line: str, line_num: int) -> Command:
        """ Parses a line, returning an appropriate command. """
        parts = line.split(sep=" ")

        # a push/pop with a segment part, or a call command
        if len(parts) == 3:

            if not parts[2].isdigit():
                raise CompilationError(f"when parsing push/pop/call, expected integer at line {line_num}"
                                       f" got \"{parts[2]}\" instead.")

            if parts[0] == "call":
                return Call(function_name, parts[1], int(parts[2]))

            elif parts[0] == "function":
                return FunctionDefinition(file_name, parts[1], int(parts[2]))

            segment = self.__segment_factory.get_segment(file_name, parts[1])
            if parts[0] == "push":
                return Push(segment, int(parts[2]))
            elif parts[0] == "pop":
                return Pop(segment, int(parts[2]))

        # goto/if-goto/label command (takes an argument)
        if len(parts) == 2:
            if not function_name:
                raise CompilationError("label must live in a function")
            label_name = parts[1]
            return CommandFactory.ArgCommands[parts[0]](function_name, label_name)

        # either a primitive command, or a call/return 
        if len(parts) == 1:
            if parts[0] in CommandFactory.Commands:
                return CommandFactory.Commands[parts[0]]

            if parts[0] == "return":
                return Return(function_name)

        raise CompilationError(f"Unrecognized command \"{line}\" at line {line_num}")

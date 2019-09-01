""" This module is responsible for creating commands, it is essentially a
    parsing class. """
from typing import Iterator, Optional
from model import (CompilationError, Command, Push, Pop, UnaryCommand,
                   BinaryCommand, CompareCommand, CompareType,
                   FunctionDefinition)
from segment_factory import SegmentFactory
from pathlib import Path
import re
import logging


# detects comments
COMMENT_REGEX = re.compile(r"//.*")

# detects whitespace
WHITESPACE_REGEX = re.compile(r"\s+")


def tokenize(vm: str) -> Iterator[str]:
    """
    Given a raw string representing the contents of a VM file, splits it into
    lines, ignoring whitespace, tabs and comments.
    """
    for line in vm.split(sep="\n"):
        line = re.sub(COMMENT_REGEX, "", line)
        line = line.strip()
        # eliminate redundant whitespace, converting them to a single space
        line = re.sub(WHITESPACE_REGEX, " ", line)
        if len(line) > 0:
            yield line


class TranslationContext:
    """ This class drives the VM translation process of a file/directory
        It uses CommandFactory to actually create the Command objects(which
        are then translated to ASM strings via to_str method), and it provides
        the commands with extra context, such as file name, and the current
        function name(needed for some of the ex8 commands)
        It is also responsible for generating bootstrap code.
    """

    def __init__(self, do_bootstrap: bool, file_or_dir: str):
        """
        :param args: Command line arguments
        :param do_bootstrap: Whether to generate bootstrap code
                             (True for ex8, False for ex7)
        :param file_or_dir: Input (a .vm file or a directory of .vm files)
        """
        self.__command_factory = CommandFactory()
        self.__do_bootstrap = do_bootstrap
        root = Path(file_or_dir)
        if root.is_file():
            self.__files = [root]
        else:
            self.__files = list(root.glob("*.vm"))
        self.__out_asm_file = root.with_suffix('.asm')
        logging.info(f"Translating {root} with {len(self.__files)} files ")

    def write_asm_file(self):
        """ Creates an output asm file"""
        logging.info(f"Creating {self.__out_asm_file}")

        with open(self.__out_asm_file, 'w') as out_file:
            for line in self.to_asm():
                logging.debug(line)
                out_file.write(line)

    def __gen_bootstrap(self) -> str:
        return f"""// bootstrap code
        // TODO
        """
    
    def to_asm(self) -> Iterator[str]:
        """ Generates asm code """
        if self.__do_bootstrap:
            yield self.__gen_bootstrap()

        for file_name in self.__files:
            logging.info(f"processing {file_name}")
            with open(file_name, 'r') as vm_f:
                cur_function = None
                contents = vm_f.read()
                for (line_num, line) in enumerate(tokenize(contents)):
                    command = self.__command_factory.parse_line(str(file_name),
                                                                cur_function,
                                                                line, line_num)
                    if isinstance(command, FunctionDefinition):
                        cur_function = command.function_name
                        logging.info(f"entering function {cur_function}")
                    yield command.to_asm()

class CommandFactory:
    """ Responsible for creating command instances. This is essentially a
        parsing class (though it isn't purely a parser, it also provides some
        semantic context for the parsed objects, such as their function)"""

    Commands = {
        "neg": UnaryCommand("neg", "-M"),
        "not": UnaryCommand("not", "!M"),
        "add": BinaryCommand("add", "M + D"),
        "sub": BinaryCommand("sub", "M - D"),
        "and": BinaryCommand("and", "M & D"),
        "or": BinaryCommand("or", "M | D"),
        "eq": CompareCommand("eq", CompareType.EQ),
        "gt": CompareCommand("gt", CompareType.GT),
        "lt": CompareCommand("lt", CompareType.LT)
    }

    def __init__(self):
        self.__segment_factory = SegmentFactory()

    def parse_line(self, file_name: str, function_name: Optional[str],
                   line: str, line_num: int) -> Command:
        """ Parses a line, returning an appropriate command. """
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

        raise CompilationError(f"Unrecognized command format \"{line}\" at line {line_num}")

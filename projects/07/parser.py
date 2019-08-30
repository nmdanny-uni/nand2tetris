import re

from typing import List, Iterator
from model import CompilationError, Command
from command_factory import CommandFactory

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
        #line = re.sub(WHITESPACE_REGEX, "", line)
        if len(line) > 0:
            yield line


def parse_file(file_name: str, command_fac: CommandFactory) -> Iterator[Command]:
    """ Parses a file, generating commands """
    with open(file_name, 'r') as file:
        for (line_num, line) in enumerate(tokenize(file.read())):
            yield command_fac.parse_line(file_name, line, line_num)

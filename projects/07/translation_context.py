import re
import logging
from pathlib import Path
from typing import Iterator, Optional
from model import Call, FunctionDefinition

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
        # eliminate redundant whitespace, converting them to a single space
        line = re.sub(WHITESPACE_REGEX, " ", line)
        if len(line) > 0:
            yield line


# Where on the Hack platform should the stack pointer be initialized to?
DEFAULT_SP_LOCATION = 256


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
            self.__out_asm_file = root.with_suffix('.asm') 
        else:
            self.__files = list(root.glob("*.vm"))
            self.__out_asm_file = root / Path(root.stem).with_suffix('.asm')

        logging.info(f"Translating {root} with {len(self.__files)} files."
                     f"Is using bootstrap: {do_bootstrap}")

    def write_asm_file(self):
        """ Creates an output asm file"""
        logging.info(f"Creating {self.__out_asm_file}")

        with open(self.__out_asm_file, 'w') as out_file:
            for line in self.to_asm():
                logging.debug(line)
                out_file.write(line.strip()+'\n')

    def __gen_bootstrap(self) -> str:
        return f"""// beginning of bootstrap code
        @{DEFAULT_SP_LOCATION}
        D = A
        @SP
        M = D
        """ + Call("BOOTSTRAP_FUNCTION", "Sys.init", 0).to_asm()

    def to_asm(self) -> Iterator[str]:
        """ Generates asm code """
        if self.__do_bootstrap:
            yield self.__gen_bootstrap()

        for file_name in self.__files:
            logging.info(f"processing {file_name}")
            with open(file_name, 'r') as vm_f:
                yield f"// processing {file_name}"
                # by the hack spec, each file must begin with a function
                # however, some .vm files from ex7 and ex8 do not follow
                # this, hence we put them in an implicit function
                cur_function = "NO_FUNCTION"
                contents = vm_f.read()
                for (line_num, line) in enumerate(tokenize(contents)):
                    command = self.__command_factory.parse_line(str(file_name),
                                                                cur_function,
                                                                line, line_num)
                    if isinstance(command, FunctionDefinition):
                        cur_function = command.function_name
                        logging.info(f"entering function {cur_function}")
                    yield command.to_asm()

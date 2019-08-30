""" This module defines the basic types in the VM specification, namely,
    segments and commands. It also defines other useful types such as
    compilation error class. """


class CompilationError(Exception):
    pass


class Segment:

    """ A segment is an abstraction over RAM, allowing to generate ASM code for
        pushing and popping values to it.
        This class allows creation of segments, and generating ASM for push/pop
        operations. """

    def __init__(self, name: str, base_pointer: str):
        """ Creates a segment
        :param name: Name of segment in commands
        :param base_pointer: RAM location(symbol/address) of pointer to base of
                             segment
        """
        self.__name = name
        self.__base_pointer = base_pointer

    # TODO optimization: if base pointer is an integer(e.g, pointer/temp),
    # can use direct

    def gen_push(self, index: int) -> str:
        """ Generates a push command's ASM using given index"""
        return f"""// push {self.__name} {index}
        @{index}
        D = A
        @{self.__base_pointer} // D = segment[{index}]
        A = M + D
        D = M
        @SP // *SP = D
        A = M
        M = D
        @SP // SP++
        M = M + 1
        """

    def gen_pop(self, index: int) -> str:
        """ Generates a pop command's ASM using given index """
        # impl note: this clobbers R13 - don't use it between pop calls
        return f"""// pop {self.__name} {index}
        @{index}  // R13 = &segment[{index}]
        D = A
        @{self.__base_pointer}
        D = D + M
        @R13
        M = D
        @SP // D = *(SP--)
        M = M - 1
        A = M
        D = M
        @R13 // segment[{index}] = D
        A = M
        M = D
        """


class ConstantSegment(Segment):
    """ The constant segment is a virtual segment, that is, it doesn't use
        memory. (But the constants must be within the RAM address bounds)"""

    def __init__(self):
        super().__init__("constant", "")

    def gen_push(self, index: int) -> str:
        return f"""// push constant {index}
        @{index}
        D = A
        @SP // *SP = {index}
        A = M
        M = D
        @SP // SP++
        M = M + 1
        """

    def gen_pop(self, index: int) -> str:
        return f"""// pop constant {index}
        @SP  // SP--
        M = M - 1
        """


class StaticSegment(Segment):
    """ Static segments are shared within a .vm file """

    def __init__(self, stripped_name: str):
        """ Creates a static named for file "stripped_name.vm" (that is, the
            argument is without an extension)"""
        self.__file_name_stripped = stripped_name
        super().__init__("static", "")

    def gen_push(self, index: int) -> str:
        return f"""// push static {index}
        @{self.__file_name_stripped}.{index}
        D = M
        @SP // *SP = D
        A = M
        M = D
        @ SP // SP++
        M = M + 1
        """

    def gen_pop(self, index) -> str:
        return f"""// pop static {index}
        @SP // D = *(SP--)
        M = M - 1
        A = M
        D = M
        @{self.__file_name_stripped}.{index}
        M = D
        """


class Command:
    """ A parsed VM command """

    def __init__(self):
        pass

    def to_asm(self) -> str:
        """ Converts the VM command to ASM """
        raise NotImplementedError


class Push(Command):
    """ A push command """

    def __init__(self, segment: Segment, index: int):
        super().__init__()
        self.__segment = segment
        self.__index = index

    def to_asm(self) -> str:
        return self.__segment.gen_push(self.__index)


class Pop(Command):
    """ A pop command """

    def __init__(self, segment: Segment, index: int):
        super().__init__()
        self.__segment = segment
        self.__index = index

    def to_asm(self) -> str:
        return self.__segment.gen_pop(self.__index)

class UnaryCommand(Command):
    """ An arithmetic/logical command that pops 1 value from the stack,
        performs a computation over it and pushes the result to the stack.
        (Impl note: this doesn't actually push/pop, it is done directly)
    """

    def __init__(self, name: str, asm_op: str):
        """ Creates the command with a given name(for debugging purposes),
            where asm_op is an ASM string containing the computation part
            using the M register for input """
        self.__name = name
        self.__asm_op = asm_op

    def to_asm(self) -> str:
        return f"""// {self.__name}
        @SP
        A = M
        M = {self.__asm_op}
        """


class BinaryCommand(Command):
    """ An arithmetic/logical command that pops 2 values from the stack,
        performs a computation over them and pushes the result to the stack."""

    def __init__(self, name: str, asm_op: str):
        """ Creates the command with a given name(for debugging purposes),
            where asm_op is an ASM string containing the computation part
            where 'M' is the first operand(x), and 'D' is the second one(y).
        """
        self.__name = name
        self.__asm_op = asm_op

    def to_asm(self) -> str:
        return f"""// {self.__name}
        @SP
        M = M - 1
        A = M
        D = M // D = y
        @SP
        A = M - 1 // this time, don't decrement SP, as we're doing a replacement
        M = {self.__asm_op}
        """

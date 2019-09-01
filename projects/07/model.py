""" This module defines the basic types in the VM specification, namely,
    segments and commands. It also defines other useful types such as
    compilation error class. """

from enum import Enum

class CompilationError(Exception):
    pass

class Segment:

    """ A segment is an abstraction over RAM, allowing to generate ASM code for
        pushing and popping values to it.
        This class allows creation of segments, and generating ASM for push/pop
        operations. """

    def __init__(self, name: str, base_pointer: str, indirection: bool = True):
        """ Creates a segment
        :param name: Name of segment in commands
        :param base_pointer: RAM location(symbol/address) of (pointer to) base
                             of segment
        :param indirection: True if base_pointer is a pointer to base,
                            False if base_pointer is a base itself
                            e.g, for temp and pointer segments.
        """
        self.__name = name
        self.__base_pointer = base_pointer
        self.__indirection = indirection

    def gen_push(self, index: int) -> str:
        """ Generates a push command's ASM using given index"""
        return f"""// push {self.__name} {index}
        @{index}
        D = A
        @{self.__base_pointer} // D = segment[{index}]
        A = {'M + D' if self.__indirection else 'A + D'}
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
        D = {'D + M' if self.__indirection else 'D + A'}
        @R13
        M = D
        @SP // SP--; D = *SP
        AM = M - 1
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
        @SP  // *SP = D
        A = M
        M = D
        @ SP // SP++
        M = M + 1
        """

    def gen_pop(self, index) -> str:
        return f"""// pop static {index}
        @SP // D = *(SP--)
        AM = M - 1
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
        A = M - 1
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
        AM = M - 1
        D = M // D = y
        @SP
        A = M - 1 // this time, don't decrement SP, as we're doing a replacement
        M = {self.__asm_op}
        """


class CompareType(Enum):
    """ What kind of comparison operation we want"""
    LT = 1,
    EQ = 2,
    GT = 3

    def to_asm(self) -> str:
        """ Returns ASM jump instruction, in case comparison result
            for `x CompareType y` is true """
        # at this point, D = x - y
        if self is CompareType.EQ:
            return "JEQ"  # x=y iff D=0
        if self is CompareType.LT:
            return "JLT"  # x<y iff D<0
        return "JGT"  # x>y iff D>0


class CompareCommand(Command):
    """ An equal/greater/less than command, depending on the passed
        compare_type """

    # Used to create unique labels for jump labels
    Counter = 0

    def __init__(self, name: str, compare_type: CompareType):
        self.__name = name
        self.__compare_type = compare_type

    def to_asm(self) -> str:
        CompareCommand.Counter += 1

        return f"""// {self.__name}
        @SP
        AM = M - 1
        D = M  // D = y
        @SP
        A = M - 1 // this time, don't decrement SP, as we're doing a replacement
        D = M - D // D = x - y


        @IF_TRUE_{CompareCommand.Counter}
        D; {self.__compare_type.to_asm()}
        @SP // otherwise, push false(0) to stack(by doing a replacement)
        A = M - 1
        M = 0
        @CONTINUE_{CompareCommand.Counter}
        0; JMP // in order to not enter the ifTrue portion

        (IF_TRUE_{CompareCommand.Counter})
        @SP
        A = M - 1
        M = -1 // push true(-1=0b1...11) to stack(by doing a replacement)

        (CONTINUE_{CompareCommand.Counter})
        """


class LabelCommand(Command):
    """ A label command """

    def __init__(self, function_name: str, label_name: str):
        """
        :param file_name: Function name in which the label was found
        :param label_name: The label string, as defined in the .vm file """
        self.__function_name = function_name
        self.__label_name = label_name

    def to_asm(self) -> str:
        return f"""// label {self.__label_name}
        ({self.__function_name}${self.__label_name})
        """

class IfGotoCommand(Command):
    """ A conditional branch command """

    def __init__(self, function_name: str, label_name: str):
        """
        :param function_name: Function in which the goto command was found
        :param label_name: The label string, as defined in the .vm file.
                           label must be in the same function """
        self.__function_name = function_name
        self.__label_name = label_name

    def to_asm(self) -> str:
        # remember that true = -1, false=0
        # thus, we jump whenever stack head is != 0, that is, JNE
        return f"""// if-goto {self.__label_name}
        // pop boolean onto D
        @SP
        AM = M - 1
        D = M
        @{self.__function_name}${self.__label_name}
        D; JNE
        """


class GotoCommand(Command):
    """ A branching statement"""

    def __init__(self, function_name: str, label_name: str):
        """
        :param function_name: Function in which the goto command was found
        :param label_name: The label string, as defined in the .vm file.
                           label must be in the same function """
        self.__function_name = function_name
        self.__label_name = label_name

    def to_asm(self) -> str:
        return f"""// goto {self.__label_name}
        @{self.__function_name}${self.__label_name}
        0; JMP
        """


class FunctionDefinition(Command):
    """ A function definition. """

    def __init__(self, function_name: str, num_args: int):
        """
        :param function_name: The name of the function being defined
        :param num_args: Number of arguments used by this function
        """
        self.__function_name = function_name
        self.__num_args = num_args

    def to_asm(self) -> str:
        return f"""// function {self.__function_name} {self.__num_args}
        ({self.__function_name})
        // TODO repeat num_args times, a loop which zeroes the local args
        """

    @property
    def function_name(self) -> str:
        return self.__function_name

    @property
    def num_args(self) -> int:
        return self.__num_args


class Call(Command):
    """ A function call command """

    def __init__(self, caller_function_name: str,
                 callee_function_name: str,
                 num_args: int):
        """
        :param caller_function_name: The function in which the call is invoked
        :param callee_function_name: The name of the function being invoked
        :param num_args: Number of args to be passed to the function """
        self.__caller_function_name = caller_function_name
        self.__callee_function_name = callee_function_name
        self.__num_args = num_args

    def to_asm(self) -> str:
        return f"""// call {self.__callee_function_name} {self.__num_args} (at {self.__caller_function_name})
        // TODO impl Call
        """

class Return(Command):
    """ A function return command """

    def __init__(self, function_name: str):
        """
        :param function_name: Name of function where this command appears """
        self.__function_name = function_name

    def to_asm(self) -> str:
        return f"""// return (within {self.__function_name})
        // TODO impl Return
        """

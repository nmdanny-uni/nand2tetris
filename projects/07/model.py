""" This module defines the basic types in the VM specification, namely,
    segments and commands. It also defines other useful types such as
    compilation error class.

    These classes have the sole purpose of generating .asm code strings, they
    are similar to many of the functions in the suggested 'CodeWriter' module,
    but organized via classes - I believe this improves readability, and makes
    it easy to use various helper methods(or other classes, as with Segment) to
    shorten code. It is also more extensible, one can easily support more types
    of commands by adding them here, and adding parsing functionality to the
    command factory.
"""

from enum import Enum


class CompilationError(Exception):
    pass


class Segment:
    """ This is essentially a helper class hierarchy used to generate ASM code
        needed for Push/Pop operations, depending on the arguments passed
        via constructor

        A segment is an abstraction of RAM, allowing to treat a segment in the
        RAM as an array, and is accessible via the base pointer - directly or
        via a dereference. """

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
    """ Static segments are shared within a .vm file. (The SegmentFactory
        is responsible for enforcing that) """

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
        A = M - 1 // now we don't decrement SP, as we're doing a replacement
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

    # some insights about comparison:
    # when comparing(via subtraction) numbers with the same sign, overflow is impossible
    # when comparing for equality, overflow doesn't matter
    # when comparing numbers with different sign, we can tell the result based on signs:
    #   if x>0 and y<0:  x > y (push true, -1, if GT, otherwise 0)
    #   if x<0 and y>0:  y > x (push false, 0, if GT, otherwise -1)

    def to_asm(self) -> str:
        CompareCommand.Counter += 1

        # optimization: when performing equality, use the much shorter version
        # that doesn't use 4 different branches
        if self.__compare_type is CompareType.EQ:
            return self.__to_asm_eq()

        ret_val_x_gt_y = "-1" if self.__compare_type is CompareType.GT else "0"
        ret_val_y_gt_x = "-1" if self.__compare_type is CompareType.LT else "0"

        label_x_gt_0 = f"IF_X_GT_0_{CompareCommand.Counter}"
        label_x_gt_y = f"IF_X_GT_Y_{CompareCommand.Counter}"
        label_y_gt_x = f"IF_Y_GT_X_{CompareCommand.Counter}"
        label_cmp_via_subtract = f"COMPARE_BY_SUBTRACTION_{CompareCommand.Counter}"

        # when we need to push 'True' to the stack, this isn't a new label - we can re-use one of the previous branches
        # (we know they're guaranteed to push 'True' or 'False' depending on CompareType)
        label_cmp_success = label_x_gt_y if self.__compare_type is CompareType.GT else label_y_gt_x
        # likewise for 'False'
        label_cmp_fail = label_y_gt_x if self.__compare_type is CompareType.GT else label_x_gt_y

        continue_label = f"CONTINUE_AFTER_CMP_{CompareCommand.Counter}"

        return f"""// {self.__name}
        // first, loading x and y into r14, r15 respectively
        @SP
        AM = M - 1
        D = M
        @R15
        M = D // R15 = y
        @SP
        A = M - 1
        D = M
        @R14
        M = D // R14 = x
        // now, SP points one past 'x', we didn't decrement it, so we can simply replace 'x' with the comparison result


        // now, checking for edge cases(4 possibilities involving x,y opposite signs)

        @{label_x_gt_0}
        D; JGT

        // -----------------------------------------------------
        // we are now on branch where x <= 0, checking for y > 0
        @R15
        D = M
        // if y > 0, then y > 0 >= x, transitively, y > x
        @{label_y_gt_x}
        D; JGT

        // ---------------------------------------------------
        // we are on branch where x <=0 and y <= 0, using classic subtraction
        
        @{label_cmp_via_subtract}
        0; JMP

        // ---------------------------------------------------
        ({label_x_gt_0})
        // we are on branch where x > 0, checking for y <= 0
        @R15
        D = M
        // if y <= 0, then y <= 0 < x, transitively, x > y
        @{label_x_gt_y}
        D; JLE

        // ----------------------------------------------------
        // we are on branch where x > 0 and y  > 0, using classic subtraction
        ({label_cmp_via_subtract})
        
        @R15
        D = M
        @R14
        D = M - D // D = x - y
        
        // comparison success if either (x - y > 0) or (x - y < 0) depending on the type of the command
        // corresponding to (x > y) or (y > x) respectively.
        @{label_cmp_success}
        D; {self.__compare_type.to_asm()}

        // comparison failed
        @{label_cmp_fail}
        0; JMP
        
        // ------------- setting results and continuing ---------------------
        // note how we don't increment SP, since we're replacing the 'x' that was before it
        ({label_x_gt_y})
        @SP
        A = M - 1
        M = {ret_val_x_gt_y}
        @{continue_label}
        0; JMP

        ({label_y_gt_x})
        @SP
        A = M - 1
        M = {ret_val_y_gt_x}
        @{continue_label}
        0; JMP

        ({continue_label})
        """

    # ASM code for an 'Eq' operation. This originally served as LT/GT too, but did't handle overflow well.
    def __to_asm_eq(self) -> str:

        return f"""// {self.__name}
        @SP
        AM = M - 1
        D = M  // D = y
        @SP
        A = M - 1 // now we don't decrement SP, as we're doing a replacement
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
    """ A conditional branch command, jumping to a label if the
        head of the stack is true. """

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
    """ A branch command, jumping to a label."""

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
    """ A function definition command. """

    def __init__(self, file_name: str, function_name: str, num_args: int):
        """
        :param file_name: File name where this function is located
        :param function_name: The name of the function being defined
        :param num_args: Number of local arguments used by this function
        """
        self.__file_name = file_name
        self.__function_name = function_name
        self.__num_args = num_args

    def __initialize_locals(self) -> str:
        """ Create the ASM code for initializing num_args locals to 0. """
        # this relies on the fact that in the Hack platform, the locals are
        # on the global stack, specifically, after the caller function's saved
        # state(this function's LCL), and since this code is accessed after
        # the Call command finishes, SP(=LCL) will indeed point at the first
        # free memory space for a local.
        push_zero = f"""// push zero
        @SP
        A = M
        M = 0
        @SP
        M = M + 1
        """
        return "".join([push_zero] * self.__num_args)

    def to_asm(self) -> str:
        return f"""// function {self.__function_name} {self.__num_args}
        ({self.__function_name})
        {self.__initialize_locals()}
        """

    @property
    def function_name(self) -> str:
        return self.__function_name


class Call(Command):
    """ A function call command """

    # Used to create unique return labels
    Counter = 0

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
        Call.Counter += 1

    def __push_symbol_to_stack(self, symbol: str, indirection: bool = True) -> str:
        """ Creates ASM code for pushing a given symbol to stack, either
            directly or its dereferenced value, depending on the 'indirection'
            parameter. """
        return f"""
        @{symbol}
        D = {'M' if indirection else 'A'}
        @SP
        A = M
        M = D
        @SP
        M = M + 1
        """

    def __get_return_address(self) -> str:
        """ This method determines the format of the return address
            from a called function, for this call. (Unique among all calls)"""
        return f"""return_to_{self.__caller_function_name}__{Call.Counter}"""

    def to_asm(self) -> str:
        return f"""// call {self.__callee_function_name} {self.__num_args})
        // push caller's return address
        // note, unlike the following, the address is accessible directly(
        // it is a label, it doesn't require a dereferencing)
        {self.__push_symbol_to_stack(self.__get_return_address(), False)}
        // push caller's LCL
        {self.__push_symbol_to_stack('LCL')}
        // push caller's ARG
        {self.__push_symbol_to_stack('ARG')}
        // push caller's THIS
        {self.__push_symbol_to_stack('THIS')}
        // push caller's THAT
        {self.__push_symbol_to_stack('THAT')}

        // Update callee ARG
        @{self.__num_args}
        D = -A // D = -n
        @5
        D = D - A // D = -n-5
        @SP
        D = M + D // D = SP-n-5
        @ARG
        M = D // ARG = SP-n-5 (no deref, we're updating pointers)

        // Update callee LCL
        @SP
        D = M
        @LCL
        M = D // LCL = SP (no deref, we're updating pointers)

        // goto called function
        @{self.__callee_function_name}
        0; JMP

        ({self.__get_return_address()})
        """


class Return(Command):
    """ A function return command """

    def __init__(self, function_name: str):
        """
        :param function_name: Name of function where this command appears """
        self.__function_name = function_name

    def __set_symbol_to_deref_frame(self, symbol: str, ix: int) -> str:
        """ Performs symbol = *(LCL - ix), returning ASM """
        return f"""
        @{ix}
        D = A
        @LCL
        A = M - D
        D = M // D = *(LCL + ix)
        @{symbol}
        M = D // symbol = *(LCL + ix)
        """

    def to_asm(self) -> str:
        return f"""// return (within {self.__function_name})
        // store ret addr in R14
        {self.__set_symbol_to_deref_frame('R14', 5)}

        @SP
        AM = M - 1
        D = M
        @ARG
        A = M
        M = D // *ARG = *(pop())

        @ARG
        D = M
        @SP
        M = D+1 // SP = ARG+1  (no deref, updating pointers)

        {self.__set_symbol_to_deref_frame('THAT', 1)}
        {self.__set_symbol_to_deref_frame('THIS', 2)}
        {self.__set_symbol_to_deref_frame('ARG', 3)}
        {self.__set_symbol_to_deref_frame('LCL', 4)}

        @R14
        A = M
        0; JMP // goto RET
        """

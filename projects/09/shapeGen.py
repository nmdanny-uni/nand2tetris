import re
import struct
from bitstring import Bits

SHAPES="""
# I
X+XX
X+XX
X+XX
X+XX

XXXX
++++
XXXX
XXXX

XX+X
XX+X
XX+X
XX+X

XXXX
XXXX
++++
XXXX

# J
X+XX
X+XX
++XX
XXXX

+XXX
+++X
XXXX
XXXX

XX++
XX+X
XX+X
XXXX

XXXX
+++X
XX+X
XXXX

# L
X+XX
X+XX
X++X
XXXX

XXXX
+++X
+XXX
XXXX

++XX
X+XX
X+XX
XXXX

XX+X
+++X
XXXX
XXXX

# O (same for all rotations)
++XX
++XX
XXXX
XXXX

++XX
++XX
XXXX
XXXX

++XX
++XX
XXXX
XXXX

++XX
++XX
XXXX
XXXX

# S
XXXX
X++X
++XX
XXXX

+XXX
++XX
X+XX
XXXX

X++X
++XX
XXXX
XXXX

X+XX
X++X
XX+X
XXXX

# T
XXXX
+++X
X+XX
XXXX

X+XX
++XX
X+XX
XXXX

X+XX
+++X
XXXX
XXXX

X+XX
X++X
X+XX
XXXX

# Z
XXXX
++XX
X++X
XXXX

X+XX
++XX
+XXX
XXXX

++XX
X++X
XXXX
XXXX

XX+X
X++X
X+XX
XXXX
""".replace('X', '0').replace('+', '1')


def mk_shapes():
    clean_lines = SHAPES.split(sep="\n")
    junk = re.compile("(?:#.+)")
    clean_lines = list(filter(lambda st: st != "",
                         re.sub(junk, "", SHAPES).strip().split(sep="\n")))

    for shape_no in range(28):
        shape_st_rows = clean_lines[shape_no*4:shape_no*4+4]
        yield Shape(shape_st_rows)


class Shape:
    def __init__(self, str_rep):
        self.__str_rep = str_rep

    def __str__(self):
        return "\n".join(self.__str_rep) +\
               f"\nin binary: {self.to_binary_string()}" +\
               f"\nas int16: {self.to_int16()} \n"

    def to_binary_string(self):
        binary_num_st = "".join(line[::-1] for line in self.__str_rep[::-1])
        return binary_num_st


    def to_int16(self):
        bits = Bits(bin=self.to_binary_string())
        return bits.int


shapes = list(mk_shapes())
for ix, shape in enumerate(shapes):
    print(f"Shape number {ix+1}:")
    print(shape)
    print()

for ix, shape in enumerate(shapes):
    print(f"let shapes[{ix}] = {shape.to_int16()};")

import unittest

from model import Jump, Dest, Comp
from parser import JUMP_ST_TO_BITFIELD, DEST_ST_TO_BITFIELD, COMP_ST_TO_BITFIELD

class TestBitFields(unittest.TestCase):
    def test_jump(self):
        possibilities = {
            None: "000",
            "JGT": "001",
            "JEQ": "010",
            "JGE": "011",
            "JLT": "100",
            "JNE": "101",
            "JLE": "110",
            "JMP": "111"
        }
        for (jump_st, expected) in possibilities.items():
            enum = JUMP_ST_TO_BITFIELD[jump_st]
            self.assertEqual(expected, enum.to_machine_code())


    def test_dest(self):
        possibilities = {
            None: "000",
            "M": "001",
            "D": "010",
            "MD": "011",
            "A": "100",
            "AM": "101",
            "AD": "110",
            "AMD": "111"
        }
        for (dest_st, expected) in possibilities.items():
            enum = DEST_ST_TO_BITFIELD[dest_st]
            self.assertEqual(expected, enum.to_machine_code())


    def test_comp(self):
        possibilities = {
            #c1...c6..a"
            "0":   "0101010",
            "1":   "0111111",
            "-1":  "0111010",
            "D":   "0001100",
            "A":   "0110000",
            "M":   "1110000",
            "!D":  "0001101",
            "!A":  "0110001",
            "!M":  "1110001",
            "-D":  "0001111",
            "-A":  "0110011",
            "-M":  "1110011",
            "D+1": "0011111",
            "A+1": "0110111",
            "M+1": "1110111",
            "D-1": "0001110",
            "A-1": "0110010",
            "M-1": "1110010",
            "D+A": "0000010",
            "D+M": "1000010",
            "D-A": "0010011",
            "D-M": "1010011",
            "A-D": "0000111",
            "M-D": "1000111",
            "D&A": "0000000",
            "D&M": "1000000",
            "D|A": "0010101",
            "D|M": "1010101"
        }
        for (comp_st, expected) in possibilities.items():
            comp, mode = COMP_ST_TO_BITFIELD[comp_st]
            self.assertEqual(expected, comp.to_machine_code())
            self.assertEqual("11", mode.to_machine_code())

    def test_extended_comp(self):
        # possibilities now include the header(instruction[13] and instruction[14])
        possibilities = {
            #       HHa123456
            "D<<": "010110000",
            "A<<": "010100000",
            "M<<": "011100000",
            "D>>": "010010000",
            "A>>": "010000000",
            "M>>": "011000000"
        }
        for (comp_st, expected) in possibilities.items():
            comp, mode = COMP_ST_TO_BITFIELD[comp_st]
            binary = f"{mode.to_machine_code()}{comp.to_machine_code()}"
            self.assertEqual(expected, binary, msg=f"while checking {comp_st}")

// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)

// The idea is repeated addition, we'll add R0, R1 times. (According to the course site, R0, R1 are
// non-negative. I would've used a shift based algorithm like in the Mul gate, if we had to support
// signed numbers too)

// Pseudocode:
// R2 = 0
// i = 0
// while i != R1:
//   R2 += R0
//   i++

// initialization
@R2
M=0
@i
M=0

// while (i != R1)
(loop)
@i
D=M
@R1
D=D-M
@end
D;JEQ

// R2 += R0
@R0
D=M
@R2
M=M+D

// i++
@i
M=M+1

// end of loop body
@loop
0;JMP

(end)

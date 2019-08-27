// Algorithm that performs R13/R14 = R15 (integer division)
// Where the inputs are positive.

// We'll use a long division method, based on
// https://en.wikipedia.org/wiki/Division_algorithm#Integer_division_(unsigned)_with_remainder
// Here's C code:
//
// unsigned short divide(unsigned short n, unsigned short d){
//   unsigned short q=0;
//   unsigned short r=0;
//   for (short i=15; i>=0; i--){
//     r = r << 1;
//     // we'll set the 1st bit of r, to the i'th bit of
//     // n, in the following way:
//     // first, zero the 1st bit of r
//     r = r & ~(1);
//     // then, if the i'th bit of n exists, 
//     if (n & (1 << (i-1))) {
//       r = r | 1; // we set again the 1st bit of r.
//     }
//     if (r >= d){
//       r = r - d;
//       q = q | (1 << (i-1));
//     }
//   }
//   return q;
// }

// The translation of this to asm is mostly straightforward, except that
// for calculating (1 << (i-1)), since our shift operator doesn't take any parameters
// we'll first calculate 1 << 14 (this is 2^14=16384), and every iteration we'll right
// shift it. (going from 2^14 for the 15th bit, to 2^0=1 for the 1st bit)

// ======================= Initialization of variables =========================
// For readability, I use custom symbols instead of R13/R14/R15, but at the end
// of the program I update R15 to become the quotinent.

@R13
D = M
@n
M = D // dividend

@R14
D = M
@d
M = D // divisor

@q
M = 0 // quotinent

@r
M = 0 // remainder

@15
D = A
@i
M = D // index of bit being operated on, beginning with one digit before the MSB(the 14th)

@16384
D = A
@shiftPattern
M = D // 2^14, this allows us to access the 15th bit



(digitLoop)
  @i
  D = M
  @end
  D; JEQ // while (i != 0)

  @r
  M = M << // left shift r
  
  // we need to set the 1st bit of 'r', to be the i'th bit of 'n'
  // we'll do so as follows: first, we set the 1st bit of 'r' to be 0
  @1
  D = !A // D is bit pattern 1111...110
  @r
  M = M & D // reset the 1st bit of r via anding it with said pattern

  @shiftPattern
  D = M
  @n
  D = M & D // D is not-zero if the i'th bit of 'n' is set(there'll be at least one 1 in the pattern)
  @continue
  D; JEQ // skip setting 'r' if D is 0 (the i'th bit of 'n' isn't set)

  @1
  D = A
  @r
  M = M | D // set the 1st bit of R by doing r = r | 1


  (continue)
    @d
    D = M
    @r
    D = M - D
    @updateQuotinentRemainder
    D; JGE // if r >= d, that is, r - d >= 0

  (advanceLoopVariables)
    @i
    M = M - 1 // i--

    @shiftPattern
    M = M >> // update bit pattern so it will let us access the i'th bit at next iter
    

@digitLoop
0; JMP // end of loop body



(updateQuotinentRemainder)
  @d
  D = M
  @r
  M = M - D // r = r - d

  // set the i'th bit of q
  @shiftPattern
  D = M
  @q
  M = M | D

  @advanceLoopVariables
  0; JMP // go back to the loop


(end)
  // set R15 as quotinent
  @q
  D = M
  @R15
  M = D

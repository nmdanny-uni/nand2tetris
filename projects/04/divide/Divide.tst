// This file is part of www.nand2tetris.org
// written by Oded Wertheimer
// File name: projects/04/divide/Divide.tst

load Divide.asm,
output-file Divide.out,
compare-to Divide.cmp,
output-list RAM[13]%D2.6.2 RAM[14]%D2.6.2 RAM[15]%D2.6.2;

set RAM[13] 100,   // Set test arguments
set RAM[14] 5,
repeat 500 {
  ticktock;
}
output;

set PC 0,
set RAM[13] 101,   // Set test arguments
set RAM[14] 5,
repeat 500 {
  ticktock;
}
output;

set PC 0,
set RAM[13] 33,   // Set test arguments
set RAM[14] 3,
repeat 500 {
  ticktock;
}
output;

set PC 0,
set RAM[13] 33,   // Set test arguments
set RAM[14] 2,
repeat 500 {
  ticktock;
}
output;

set PC 0,
set RAM[13] 23053,   // Set test arguments
set RAM[14] 4123,
repeat 1000 {
  ticktock;
}
output;
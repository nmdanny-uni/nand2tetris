// This file is part of www.nand2tetris.org
// written by Oded Wertheimer
// File name: projects/04/sort/SortSmall.tst

load Sort.asm,
output-file Sort.out,
compare-to SortSmall.cmp,
output-list RAM[14]%D2.6.2 RAM[15]%D2.6.2 RAM[2048]%D2.6.2 RAM[2049]%D2.6.2 RAM[2050]%D2.6.2 RAM[2051]%D2.6.2;

set RAM[14] 2048,   // Set test arguments
set RAM[15] 4,
set RAM[2048] 1;
set RAM[2049] 2;
set RAM[2050] 3;
set RAM[2051] 4;
repeat 1000 {
  ticktock;
}
output;

set PC 0,
set RAM[14] 2048,   // Set test arguments
set RAM[15] 4,
set RAM[2048] 1;
set RAM[2049] 4;
set RAM[2050] 2;
set RAM[2051] 4;
repeat 1000 {
  ticktock;
}
output;

set PC 0,
set RAM[14] 2048,   // Set test arguments
set RAM[15] 4,
set RAM[2048] 0;
set RAM[2049] 2;
set RAM[2050] 3;
set RAM[2051] 1;
repeat 1000 {
  ticktock;
}
output;

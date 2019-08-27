// This file is part of www.nand2tetris.org
// written by Oded Wertheimer
// File name: projects/04/sort/SortLarge.tst

load Sort.asm,
output-file Sort.out,
compare-to SortLarge.cmp,
output-list 
RAM[14]%D2.6.2 
RAM[15]%D2.6.2 
RAM[2048]%D2.6.2 
RAM[2049]%D2.6.2 
RAM[2050]%D2.6.2 
RAM[2051]%D2.6.2 
RAM[2052]%D2.6.2 
RAM[2053]%D2.6.2 
RAM[2054]%D2.6.2 
RAM[2055]%D2.6.2 
RAM[2056]%D2.6.2 
RAM[2057]%D2.6.2 
RAM[2058]%D2.6.2 
RAM[2059]%D2.6.2 
RAM[2060]%D2.6.2 
RAM[2061]%D2.6.2 
RAM[2062]%D2.6.2 
RAM[2063]%D2.6.2 
RAM[2064]%D2.6.2 
RAM[2065]%D2.6.2;

set RAM[14] 2048,   // Set test arguments
set RAM[15] 18,
set RAM[2048] 1;
set RAM[2049] 2;
set RAM[2050] 3;
set RAM[2051] 4;
set RAM[2052] 5;
set RAM[2053] 6;
set RAM[2054] 7;
set RAM[2055] 8;
set RAM[2056] 9;
set RAM[2057] 10;
set RAM[2058] 11;
set RAM[2059] 12;
set RAM[2060] 13;
set RAM[2061] 14;
set RAM[2062] 15;
set RAM[2063] 16;
set RAM[2064] 17;
set RAM[2065] 18;

repeat 50000 {
  ticktock;
}
output;

set PC 0,
set RAM[14] 2048,   // Set test arguments
set RAM[15] 18,
set RAM[2048] 1;
set RAM[2049] 2;
set RAM[2050] 3;
set RAM[2051] 4;
set RAM[2052] 5;
set RAM[2053] 6;
set RAM[2054] 7;
set RAM[2055] 8;
set RAM[2056] 20;
set RAM[2057] 10;
set RAM[2058] 11;
set RAM[2059] 1;
set RAM[2060] 13;
set RAM[2061] 20;
set RAM[2062] 15;
set RAM[2063] 6;
set RAM[2064] 17;
set RAM[2065] 18;
repeat 50000 {
  ticktock;
}
output;


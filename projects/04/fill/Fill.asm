// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.


// Put your code here.

// initialize pressed. 0 means white, -1 means black
@pressed
M = 0

// here we set the END_OF_SCREEN constant, equals SCREEN + 256 rows * 32 words = 24576
// we end one unit before, since
@24576
D = A
@END_OF_SCREEN
M = D

// main program loop
(infiniteLoop)

// inspecting the pressed key
@KBD
D = M
@setPressed
D; JNE // if scan_code != 0, call setPressed
@pressed
M = 0  // otherwise, pressed = 0
(setScreenColor)
// setting screen color

// initialize initial screen index(loop variable)
@SCREEN
D = A
@screenPos
M = D

// while (screenPos != END_OF_SCREEN)
(screenLoop)
@screenPos
D = M
@END_OF_SCREEN
D = D - M
@infiniteLoop
D; JEQ

// set the entire pixel word as required (Screen[screenPos] = pressed)
// remembering that pressed is 0(black) if unpressed, or -1 (white) if pressed
@pressed
D = M
@screenPos
A = M
M = D

// advance screenPos by 32
@1
D = A
@screenPos
M = M + 1

// continue with the screenPos loop
@screenLoop
0; JMP

// continue with our input loop
@infiniteLoop
0; JMP

// pressed = 1
(setPressed)
@pressed
M=-1  // -1 is 1111...11 in bits, allowing us to color 16 bits at once
@setScreenColor
0; JMP

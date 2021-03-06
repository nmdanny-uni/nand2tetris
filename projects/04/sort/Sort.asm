// O(n^2) Sort:
// Given R14 (pointer to array) and R15 (size of array), performs a
// descending sort.
// Treat all numbers as signed, that is, -16384 < x < 16384 forall x in array

// Choice of algorithm:
// * I want it to be in-place, to eliminate copying of the array(shorter ASM code)
// * Non recursive(for simpler implementation)
// * Deterministic
// * Short and simple

// I will use insertion sort.
// For pseudocode, see https://en.wikipedia.org/wiki/Insertion_sort#Algorithm





// ======== Outer loop of sort function
@i
M = 0

// while (i != ARRAY_LENGTH)
(sortOuterLoop)
  @R15
  D = M // ARRAY_LENGTH
  @i
  D = D - M
  @endOuterLoop
  D; JEQ // if i == ARRAY_LENGTH, exit loop(end program)

  // ======== Inner loop of swap function
  @i
  D = M
  @j
  M = D // j = i

  // while ( i > 0 && A[j-1] < A[j])
  (sortInnerLoop)
    // ==== enforcing first loop condition, that i > 0
    @j
    D = M
    @endInnerLoop
    D; JLE  // while (i > 0 && ... ) - if false, finish inner loop

    // ==== calculating pointers for A[j] and A[j-1]
    @R14
    D = M
    @j
    D = D + M
    @jPtr
    M = D // jPtr = R14 + j
    @jMinusPtr
    M = D - 1 // jMinusPtr = R14 + j - 1

    // ==== Dereferencing pointers to get actual values A[j] and A[j-1]
    @jPtr
    A = M
    D = M
    @aj
    M = D // aj = *jPtr = arr[j]

    @jMinusPtr
    A = M
    D = M
    @ajMinus
    M = D // ajMinus = *jMinusPtr = arr[j-1]

    // ===== Enforcing second loop condition, that A[j-1] < A[j] (IFF A[j-1] - A[j] < 0)
    @ajMinus
    D = M
    @aj
    D = D - M // D = A[j-1] - A[j]

    @endInnerLoop
    D; JGE  // continue of while - && A[j-1] - A[j] < 0, otherwise(>=), finish inner loop

    // ===== Loop body, perform swap
    @swap
    0; JMP // swap A[j] and A[j-1]
 
    (afterSwap)
    @j
    M = M - 1 // decrement inner loop index

    @sortInnerLoop
    0; JMP
  (endInnerLoop)

  @i
  M = M + 1 // increment outer loop index

@sortOuterLoop
0; JMP

(endOuterLoop)

// so we won't accidentally enter swap
@endOfProgram
0; JMP

//  ======= Swap function: swapping array[j] and array[j-1], using
//          variables 'jPtr' and 'jMinusPtr' as array pointers
(swap)
  @jPtr
  A = M
  D = M
  @temp
  M = D // temp = *jPtr        IFF  temp = array[j]

  @jMinusPtr
  A = M
  D = M
  @jPtr
  A = M
  M = D // *jPtr = *jMinusPtr  IFF  array[j] = array[j-1]

  @temp
  D = M
  @jMinusPtr
  A = M
  M = D // *jMinusPtr = temp   IFF array[j-1] = temp

  @afterSwap
  0; JMP // go back where we came from


(endOfProgram)

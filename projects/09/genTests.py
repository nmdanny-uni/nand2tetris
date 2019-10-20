
def genRightShiftTest(num, amount):
    expected = num >> amount
    print(f'do assert(Util.rightShift({num}, {amount}) = {expected}, "{num} >> {amount} = {expected}");')

testCases = [
    [5,3], [135, 2], [31, 0], [4641, 3], [0, 5], [16211, 1]
]


def genModulusTests(num, exponent):
    expected = num % (2**exponent)
    print(f'do assert(Util.modulus_exp({num}, {exponent}) = {expected}, "{num} % {2**exponent} = {expected}");')

for [num, amount] in testCases:
    genRightShiftTest(num, amount)

modTestCases = [
    [0, 0], [0, 3], [3, 0], [3, 3], [15, 5], [15, 0], [15, 4], [2, 15], [17, 3], [28, 3],
    [-3, 2], [-3, 4], [-3, 6]
]

for [num, exponent] in modTestCases:
    genModulusTests(num, exponent)


def genPowersOf2():
    for i in range(0, 15):
        print(f"let powersOf2[{i}] = {2**i};")


xorTestCases = [
    [1, 0], [0, 1], [135, 0], [0, 135], [523, 5], [132, 6], [1911, 2412], [-135, -531],
    [-135, 7], [0, -9135], [-1341, 2511], [35416, -41525], [1351, 25945]
]


def genXorTests(a, b):
    expected = a ^ b
    print(f'do assert(Util.xor({a}, {b}) = {expected}, "{a} ^ {b} = {expected}");')

for [a, b] in xorTestCases:
    genXorTests(a, b)

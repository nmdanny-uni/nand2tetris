def createShifts(n):
    print(f"// Shifts for digit {n}")
    for y in range(n-1, -1, -1):
        print(f"ShiftLeft(in=p{n}s{y+1}, out=p{n}s{y});")

for i in range(0, 16):
    createShifts(i)

print(f"//Adding together everything")
# creating adders
for i in range(0, 16):
    print(f"Add16(a=p{i}s0, b=add{i}, out=add{i+1});")

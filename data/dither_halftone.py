import math
import sys
tau=math.pi*2
l=int(sys.argv[1])
a=[round(math.sin(tau*(i%l)/l)+math.sin(tau*(i//l)/l)+2,10)for i in range(l*l)]
b = [sorted(set(a)).index(i)for i in a]
index=0
divisor = max(b) + 1
print(divisor)
for i in range(0,l):
    for j in range(0,l):
        print(f"{b[index]}" , end="")
        if j < l-1:
            print("," , end="")
        index += 1
    print("")

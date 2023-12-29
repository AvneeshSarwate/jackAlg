import random

rows = []
n = 2000




# for i in range(n):
#   offset = (i/(n*2))
#   rows.append(" ".join([str(i), "red", str(0+offset), str(10+offset)]))

# outString = "\n".join(rows)
# open("perfTest0.txt", "w").write(outString)






rows = []
for i in range(n):
  start = random.random()
  offset = random.random()
  rows.append(" ".join([str(i), "red", str(start), str(start+offset)]))

outString = "\n".join(rows)
open("randRanges0.txt", "w").write(outString)
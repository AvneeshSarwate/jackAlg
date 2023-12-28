
rows = []
n = 1000
for i in range(n):
  offset = (i/(n*2))
  rows.append(" ".join([str(i), "red", str(0+offset), str(10+offset)]))

outString = "\n".join(rows)
open("perfTest0.txt", "w").write(outString)

import heapq
import itertools
import intervaltree 


def rangesOverlap(lowA, highA, lowB, highB):
  return lowA <= highB and lowB <= highA 


import heapq

class MaxPriorityQueue:
  def __init__(self):
    self.heap = []
    self.entry_finder = {}  # mapping of items to entries
    self.REMOVED = '<removed-item>'  # placeholder for a removed item
    self.counter = 0  # unique sequence count
  
  def __len__(self):
    return len(self.heap)

  def add_item(self, item, priority=0):
    """Add a new item or update the priority of an existing item"""
    if item in self.entry_finder:
      self.remove_item(item)
    count = self.counter
    entry = [-priority, count, item]  # negative priority for max heap
    self.entry_finder[item] = entry
    heapq.heappush(self.heap, entry)
    self.counter += 1

  def remove_item(self, item):
    """Mark an existing item as REMOVED. Raise KeyError if not found."""
    entry = self.entry_finder.pop(item)
    entry[-1] = self.REMOVED

  def pop_item(self):
    """Remove and return the highest priority item. Raise KeyError if empty."""
    while self.heap:
      priority, count, item = heapq.heappop(self.heap)
      if item is not self.REMOVED:
        del self.entry_finder[item]
        return -priority, item
    raise KeyError('pop from an empty priority queue')

  def reprioritize_item(self, item, new_priority):
    """Change the priority of an existing item. Raise KeyError if not found."""
    if item not in self.entry_finder:
      raise KeyError(f'Item {item} not found')
    self.add_item(item, new_priority)

  def peek(self):
    """Return the highest priority item without removing it. Raise KeyError if empty."""
    while self.heap:
      priority, count, item = self.heap[0]
      if item is not self.REMOVED:
        return -priority, item
      heapq.heappop(self.heap)  # Remove the removed item and continue
    raise KeyError('peek from an empty priority queue')

class CountRangeGreedyAllocator:
  def __init__(self, color, ballRangeTree, intersectRangesTree, intersectRangeCounts, rangePoints, priorityQueue):
    self.color = color
    self.ballRangeTree = ballRangeTree
    self.intersectRangesTree = intersectRangesTree
    self.intersectRangeCounts = intersectRangeCounts
    self.rangePoints = rangePoints
    self.priorityQueue = priorityQueue
  
  def __len__(self):
    return len(self.priorityQueue)
  
  def returnBucketLabel(self):
    # find the (count, dense-range) with the most ball intersections
    # this returns the value, removes it from the heap, and queues up the next-highest value
    (count, ovrg) = self.priorityQueue.pop_item()
    count = -count # return count to it's original positive value

    # get all balls that intersect with the dense range
    overlapBallIntervals = self.ballRangeTree.overlap(ovrg[0], ovrg[1]) #[{begin:number, end:number, data:any}]
    ballIds = [interval.data for interval in overlapBallIntervals]

    # remove all balls that intersect with the dense range
    self.ballRangeTree.remove_overlap(ovrg[0], ovrg[1])

    # TODO - is there a way to make this not n^2?
    for obi in overlapBallIntervals:
      intervalsToDecrement = self.intersectRangesTree.overlap(obi.begin, obi.end)
      for i2d in intervalsToDecrement:
         oldCount = self.intersectRangeCounts[(i2d.begin, i2d.end)]
         newCount = oldCount-1
         self.intersectRangeCounts[(i2d.begin, i2d.end)] = newCount
         print("heap", self.color, self.priorityQueue.heap)
         self.priorityQueue.reprioritize_item((i2d.begin, i2d.end), newCount)

    return (count, self.color, ballIds)
  
  # if you have no ranges left, you should also be out of balls 
  def hasRangesLeft(self):
    return len(self.heap) > 0

  def peek(self):
    return self.priorityQueue.peek()
     


def createBucketAllocator(balls, color): # tuple of (id, color, low, high)
  ballRangeTree = intervaltree.IntervalTree() # the collection of ranges of balls in an efficient data structure
  intersectRangesTree = intervaltree.IntervalTree()
  rangePoints = set() # all of the different points in the ranges of the balls

  # store all of the ball ranges in the range tree
  # extract all of the individual points from all of the ranges
  for b in balls:
    id, color, low, high = b
    rangePoints.add(low)
    rangePoints.add(high)
    ballRangeTree.addi(low, high, id)

  rangePointList = sorted(list(rangePoints))
  overlapRanges = itertools.pairwise(rangePointList) # the "dense" ranges created by overlapping all ball ranges
  intersectRangeCounts = {} # the number of balls that overlap each range of the "dense" range set

  # count the number of balls per "dense" range
  for ovrg in overlapRanges:
    low, high = ovrg
    intersectRangesTree.addi(low, high)
    intersectRangeCounts[ovrg] = len(ballRangeTree.overlap(low, high))
  
  # print(color)
  # for irc in intersectRangeCounts:
  #   print("    ", intersectRangeCounts[irc], irc)
  # print(ballRangeTree)
  # print()

  #create a priority queue so you always know which dense range has the most intersecting balls
  priorityQueue = MaxPriorityQueue()
  for ovrg in intersectRangeCounts:
    count = intersectRangeCounts[ovrg]
    priorityQueue.add_item(ovrg, count)
  
  return CountRangeGreedyAllocator(color, ballRangeTree, intersectRangesTree, intersectRangeCounts, rangePointList, priorityQueue)
  
  
def parseLine(line): #input file is a list of lines (id: int, color: string, start: float, end: float), with blank lines
  split = line.split(" ")
  return (int(split[0]), split[1], float(split[2]), float(split[3]))

def parseBallFile(fileString):
  lines = [parseLine(l) for l in fileString.split("\n") if len(l) > 0]
  return lines


def splitLinesByColor(parsedLines):
  linesByColor = {}
  for pl in parsedLines:
    id, color, low, high = pl
    if not color in linesByColor:
        linesByColor[color] = []
    linesByColor[color].append(pl)

  return linesByColor


def popMaxAllocator(allocatorsByColor):
  maxCount = -1
  maxColor = ""
  maxRange = (0, 0)

  for color in allocatorsByColor:
    allocator = allocatorsByColor[color]
    if len(allocator) == 0:
      continue
    peekCount, peekRange = allocator.peek()
    print("max allocator run", color, peekCount, peekRange, peekCount > maxCount)
    if peekCount > maxCount:
      maxCount = peekCount
      maxColor = color
      maxRange = peekRange
  
  allocatorsByColor[maxColor].returnBucketLabel()
  print("max allocator result", maxCount, maxRange, maxColor)
  return maxCount, maxRange, maxColor
  


def runAllocators(linesByColor, numBuckets):
  allocatorsByColor = {}
  for color in linesByColor:
    allocatorsByColor[color] = createBucketAllocator(linesByColor[color], color)
  allocators = allocatorsByColor.values()

  buckets = []
  for i in range(numBuckets):
    if all([len(al) == 0 for al in allocators]):
      return buckets
    maxCount, maxRange, maxColor = popMaxAllocator(allocatorsByColor)
    print()
    buckets.append((maxColor, (maxRange[1]-maxRange[0])/2, maxCount, maxRange))
  
  return buckets
    


  
   


if __name__ == "__main__":
  inputStr = open("input0.txt").read()
  parsedLines = parseBallFile(inputStr)
  linesByColor = splitLinesByColor(parsedLines)
  buckets = runAllocators(linesByColor, 1)
  print()
  for b in buckets:
    print(b)

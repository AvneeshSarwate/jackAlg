import heapq
import itertools
import intervaltree 

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
    """Mark an existing item as REMOVED and move it to the end of the heap."""
    if item not in self.entry_finder:
      raise KeyError(f'Item {item} not found')
    entry_index = self.heap.index(self.entry_finder[item])
    # Set priority to negative infinity and update in the heap
    self.heap[entry_index][0] = float('-inf')
    self._sift_up(entry_index)
    # Remove the item from the top of the heap and the entry finder
    self.heap.pop(0)
    del self.entry_finder[item]
    # Restore heap order
    if self.heap:
      moved_item = self.heap.pop()
      heapq.heappush(self.heap, moved_item)

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
    entry_index = self.heap.index(self.entry_finder[item])
    self.heap[entry_index][0] = -new_priority  # Update priority
    self._sift_down(entry_index)
    self._sift_up(entry_index)

  def _sift_up(self, idx):
    """Move the item at the given index up to its correct position."""
    item = self.heap[idx]
    while idx > 0:
      parent_idx = (idx - 1) >> 1
      parent = self.heap[parent_idx]
      if parent <= item:
        break
      self.heap[idx] = parent
      idx = parent_idx
    self.heap[idx] = item

  def _sift_down(self, idx):
    """Move the item at the given index down to its correct position."""
    end_idx = len(self.heap)
    start_idx = idx
    item = self.heap[idx]
    child_idx = 2*idx + 1
    while child_idx < end_idx:
      right_idx = child_idx + 1
      if right_idx < end_idx and self.heap[right_idx] < self.heap[child_idx]:
        child_idx = right_idx
      if self.heap[child_idx] >= item:
        break
      self.heap[idx] = self.heap[child_idx]
      idx = child_idx
      child_idx = 2*idx + 1
    self.heap[idx] = item

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
    self.intersectRangesTree.remove_overlap(ovrg[0], ovrg[1])
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
        #  print("heap pre", self.color, self.priorityQueue.heap)
         self.priorityQueue.reprioritize_item((i2d.begin, i2d.end), newCount)
        #  print("heap post", self.color, self.priorityQueue.heap)
        #  print()

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
    # print("max allocator run", color, peekCount, peekRange, peekCount > maxCount)
    if peekCount > maxCount:
      maxCount = peekCount
      maxColor = color
      maxRange = peekRange
  
  topCount, topColor, ballIds = allocatorsByColor[maxColor].returnBucketLabel()
  # print("max allocator result", maxCount, maxRange, maxColor)
  return maxCount, maxRange, maxColor, ballIds
  


def runAllocators(linesByColor, numBuckets):
  allocatorsByColor = {}
  for color in linesByColor:
    allocatorsByColor[color] = createBucketAllocator(linesByColor[color], color)
  allocators = allocatorsByColor.values()

  buckets = []
  for i in range(numBuckets):
    if all([len(al) == 0 for al in allocators]):
      return buckets
    if i == numBuckets: ## todo - not handling allocators with no intervals properly - need to delete items with zero count from the count dict and use it as the __len__ src?
      return buckets
    maxCount, maxRange, maxColor, ballIds = popMaxAllocator(allocatorsByColor)
    # print()
    buckets.append((maxColor, (maxRange[1]-maxRange[0])/2, maxCount, maxRange, ballIds))
  
  return buckets
    


  
   


if __name__ == "__main__":
  inputStr = open("randRanges0.txt").read()
  parsedLines = parseBallFile(inputStr)
  linesByColor = splitLinesByColor(parsedLines)
  buckets = runAllocators(linesByColor, 5)
  print()
  for b in buckets:
    print(b[0:4])

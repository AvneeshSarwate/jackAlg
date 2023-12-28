import heapq
import itertools
import intervaltree 


def rangesOverlap(lowA, highA, lowB, highB):
  return lowA <= highB and lowB <= highA 


class CountRangeGreedyAllocator:
  def __init__(self, color, ballRangeTree, intersectRangesTree, intersectRangeCounts, rangePoints, heap):
    self.color = color
    self.ballRangeTree = ballRangeTree
    self.intersectRangesTree = intersectRangesTree
    self.intersectRangeCounts = intersectRangeCounts
    self.rangePoints = rangePoints
    self.heap = heap
  
  def returnBucketLabel(self):
    (count, ovrg) = heapq.heappop(self.heap)
    ballIds = [interval.dataa for interval in self.ballRangeTree.overlap(ovrg)]
    return (-count, self.color, ballIds)


def createRangeCountDataStructures(balls, color): #tuple of (id, color, low, high)
  ballRangeTree = intervaltree.IntervalTree()
  intersectRangesTree = intervaltree.IntervalTree()
  rangePoints = set()

  for b in balls:
    id, color, low, high = b
    rangePoints.add(low)
    rangePoints.add(high)
    ballRangeTree.addi(low, high, id)

  rangePointList = sorted(list(rangePoints))
  overlapRanges = itertools.pairwise(rangePointList)
  intersectRangeCounts = {}

  for ovrg in overlapRanges:
    low, high = ovrg
    intersectRangesTree.addi(low, high)
    intersectRangeCounts[ovrg] = len(ballRangeTree.overlap(low, high))
  
  heap = []
  for ovrg in intersectRangeCounts:
    count = intersectRangeCounts[ovrg]
    heap.append((-count, ovrg))
  
  heapq.heapify(heap)

  return CountRangeGreedyAllocator(color, ballRangeTree, intersectRangesTree, intersectRangeCounts, rangePointList, heap)
  
  



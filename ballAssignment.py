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
    # find the (count, dense-range) with the most ball intersections
    # this returns the value, removes it from the heap, and queues up the next-highest value
    (count, ovrg) = heapq.heappop(self.heap) 
    count = -count # return count to it's original positive value

    # get all balls that intersect with the dense range
    ballIds = [interval.data for interval in self.ballRangeTree.overlap(ovrg)]

    # remove all balls that intersect with the dense range
    self.ballRangeTree.remove_overlap(ovrg[0], ovrg[1])

    # TODO - need to update the intersectRangeCounts and re-heapify

    return (count, self.color, ballIds)
  
  # if you have no ranges left, you should also be out of balls 
  def hasRangesLeft(self):
    return len(self.heap) > 0


def createRangeCountDataStructures(balls, color): # tuple of (id, color, low, high)
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
  
  #create a priority queue so you always know which dense range has the most intersecting balls
  heap = []
  for ovrg in intersectRangeCounts:
    count = intersectRangeCounts[ovrg]
    heap.append((-count, ovrg)) # store count as negative because python heap is min heap, and we want a max heap
  
  #turn the list into a heap
  heapq.heapify(heap)

  return CountRangeGreedyAllocator(color, ballRangeTree, intersectRangesTree, intersectRangeCounts, rangePointList, heap)
  
  



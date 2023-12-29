use std::collections::{HashMap, HashSet};
use interval_tree::IntervalTree;
use max_priority_queue::MaxPriorityQueue;

struct CountRangeGreedyAllocator<T> {
    color: String,
    ball_range_tree: IntervalTree<f64, T>,
    intersect_ranges_tree: IntervalTree<f64, ()>,
    intersect_range_counts: HashMap<(f64, f64), i32>,
    range_points: Vec<f64>,
    priority_queue: MaxPriorityQueue<(f64, f64), i32>,
}

impl<T> CountRangeGreedyAllocator<T> {
    pub fn new(color: String, ball_range_tree: IntervalTree<f64, T>, intersect_ranges_tree: IntervalTree<f64, ()>, intersect_range_counts: HashMap<(f64, f64), i32>, range_points: Vec<f64>, priority_queue: MaxPriorityQueue<(f64, f64), i32>) -> Self {
        Self {
            color,
            ball_range_tree,
            intersect_ranges_tree,
            intersect_range_counts,
            range_points,
            priority_queue,
        }
    }

    pub fn len(&self) -> usize {
        self.priority_queue.len()
    }

    pub fn return_bucket_label(&mut self) -> (i32, String, Vec<T>) {
        let (count, ovrg) = self.priority_queue.pop().unwrap();
        self.intersect_ranges_tree.remove_overlap(ovrg.0, ovrg.1);
        let count = -count;

        let overlap_ball_intervals = self.ball_range_tree.overlap(ovrg.0, ovrg.1);
        let ball_ids: Vec<T> = overlap_ball_intervals.iter().map(|interval| interval.data.clone()).collect();

        self.ball_range_tree.remove_overlap(ovrg.0, ovrg.1);

        for obi in overlap_ball_intervals {
            let intervals_to_decrement = self.intersect_ranges_tree.overlap(obi.begin, obi.end);
            for i2d in intervals_to_decrement {
                let old_count = *self.intersect_range_counts.get(&(i2d.begin, i2d.end)).unwrap();
                let new_count = old_count - 1;
                self.intersect_range_counts.insert((i2d.begin, i2d.end), new_count);
                self.priority_queue.reprioritize(&(i2d.begin, i2d.end), new_count);
            }
        }

        (count, self.color.clone(), ball_ids)
    }

    pub fn has_ranges_left(&self) -> bool {
        !self.priority_queue.is_empty()
    }

    pub fn peek(&self) -> Option<(&(f64, f64), &i32)> {
        self.priority_queue.peek()
    }
}

fn create_bucket_allocator(balls: Vec<(i32, String, f64, f64)>, color: String) -> CountRangeGreedyAllocator<i32> {
    let mut ball_range_tree = IntervalTree::new();
    let mut intersect_ranges_tree = IntervalTree::new();
    let mut range_points = HashSet::new();
    let mut intersect_range_counts = HashMap::new();

    for (id, _, low, high) in balls {
        range_points.insert(low);
        range_points.insert(high);
        ball_range_tree.insert(low, high, id);
    }

    let range_point_list: Vec<f64> = range_points.into_iter().collect();
    range_point_list.sort_unstable();

    let overlap_ranges = pairwise(range_point_list);

    for (low, high) in overlap_ranges {
        intersect_ranges_tree.insert(low, high, ());
        intersect_range_counts.insert((low, high), ball_range_tree.overlap(low, high).len() as i32);
    }

    let mut priority_queue = MaxPriorityQueue::new();
    for (ovrg, count) in intersect_range_counts.iter() {
        priority_queue.push(*ovrg, *count);
    }

    CountRangeGreedyAllocator::new(
        color,
        ball_range_tree,
        intersect_ranges_tree,
        intersect_range_counts,
        range_point_list,
        priority_queue,
    )
}

fn parse_line(line: &str) -> Option<(i32, String, f64, f64)> {
    let split: Vec<&str> = line.split_whitespace().collect();
    if split.len() != 4 {
        return None;
    }
    let id = split[0].parse().ok()?;
    let color = split[1].to_string();
    let start = split[2].parse().ok()?;
    let end = split[3].parse().ok()?;
    Some((id, color, start, end))
}

fn parse_ball_file(file_string: &str) -> Vec<(i32, String, f64, f64)> {
    file_string.lines()
        .filter_map(|line| parse_line(line))
        .collect()
}

fn split_lines_by_color(parsed_lines: Vec<(i32, String, f64, f64)>) -> HashMap<String, Vec<(i32, String, f64, f64)>> {
    let mut lines_by_color = HashMap::new();
    for (id, color, low, high) in parsed_lines {
        lines_by_color.entry(color).or_insert_with(Vec::new).push((id, color, low, high));
    }
    lines_by_color
}

fn pop_max_allocator(allocators_by_color: &mut HashMap<String, CountRangeGreedyAllocator<i32>>) -> (i32, (f64, f64), String, Vec<i32>) {
    let mut max_count = -1;
    let mut max_color = String::new();
    let mut max_range = (0.0, 0.0);
    let mut max_allocator = None;

    for (color, allocator) in allocators_by_color.iter() {
        if allocator.len() == 0 {
            continue;
        }
        if let Some((peek_range, &peek_count)) = allocator.peek() {
            if peek_count > max_count {
                max_count = peek_count;
                max_color = color.clone();
                max_range = *peek_range;
                max_allocator = Some(allocator);
            }
        }
    }

    let (top_count, top_color, ball_ids) = max_allocator.unwrap().return_bucket_label();
    (top_count, max_range, top_color, ball_ids)
}

fn run_allocators(lines_by_color: HashMap<String, Vec<(i32, String, f64, f64)>>, num_buckets: usize) -> Vec<(String, f64, i32, (f64, f64), Vec<i32>)> {
    let mut allocators_by_color: HashMap<String, CountRangeGreedyAllocator<i32>> = lines_by_color.into_iter()
        .map(|(color, lines)| (color.clone(), create_bucket_allocator(lines, color)))
        .collect();

    let mut buckets = Vec::new();

    for _ in 0..num_buckets {
        if allocators_by_color.values().all(|al| al.len() == 0) {
            return buckets;
        }
        let (max_count, max_range, max_color, ball_ids) = pop_max_allocator(&mut allocators_by_color);
        buckets.push((max_color, (max_range.1 - max_range.0) / 2.0, max_count, max_range, ball_ids));
    }

    buckets
}

fn main() {
    let input_str = std::fs::read_to_string("randRanges0.txt").expect("Error reading file");
    let parsed_lines = parse_ball_file(&input_str);
    let lines_by_color = split_lines_by_color(parsed_lines);
    let buckets = run_allocators(lines_by_color, 5);

    for bucket in buckets.iter() {
        println!("{:?}", bucket.0..3);
    }
}

fn pairwise<T: Clone>(list: Vec<T>) -> Vec<(T, T)> {
    list.windows(2).map(|pair| (pair[0].clone(), pair[1].clone())).collect()
}

import pickle
import random
from copy import deepcopy
from pathlib import Path
from typing import Sequence

from src.shortest_path.graph import Graph, Edge
from src.shortest_path.main import shortest_path


class Solution:
    def __init__(self, stops_sequence: list[str]):
        self.stops = stops_sequence.copy()
        self.paths: list[tuple[int, list[Edge]]] = []
        self.cost = float('inf')

    @property
    def flat_path(self):
        return [edge for _, path in self.paths for edge in path]

    def duplicate(self) -> 'Solution':
        new = Solution(self.stops)
        new.paths = deepcopy(self.paths)
        new.cost = self.cost
        return new

    def calculate_cost(self, graph: Graph, time: int, criterion: str):
        self.paths = []
        self.cost = 0

        for i in range(len(self.stops) - 1):
            start = self.stops[i]
            end = self.stops[i+1]

            path, score, n_lines = shortest_path(
                graph=graph,
                start_stop=start,
                end_stop=end,
                start_time_sec=time,
                criterion=criterion,
            )
            if score is None:
                self.cost = float('inf')
                return

            self.paths.append((score, path))
            self.cost += score
            if path:
                time = path[-1].arrival_sec
            elif criterion == 't':
                time += score


def sample(seq: Sequence, sample_size: int, strategy: str = 'random'):
    if strategy == 'random':
        return random.sample(seq, sample_size)
    elif strategy == 'systematic':
        length = len(seq)
        step = max(1, length // sample_size)
        return [seq[i] for i in range(0, length, step)][:sample_size]

    raise ValueError(f"Unknown sampling strategy: {strategy}")


def swap_segment(stops: list[Edge], start_idx: int, end_idx: int):
    new_stops = stops.copy()
    return (
        new_stops if start_idx >= end_idx
        else new_stops[:start_idx] + new_stops[start_idx:end_idx+1][::-1] + new_stops[end_idx+1:]
    )


def generate_neighbors(solution: Solution):
    stops = solution.stops
    total = len(stops)
    neighbors = []
    for start_idx in range(1, total - 2):
        for end_idx in range(start_idx + 1, total - 1):
            new_stops = swap_segment(stops, start_idx, end_idx)
            neighbors.append((start_idx, end_idx, new_stops))
    return neighbors


def tabu_search(
    graph: Graph,
    initial_solution: Solution,
    start_time_sec: int,
    criterion: str = 't',
    tabu_size_limited: bool = False,
    is_aspirational: bool = False,
    max_iterations: int = 100,
    sample_size: int = None,
    sample_strategy: str = 'random',
) -> Solution:
    current_solution = initial_solution
    current_solution.calculate_cost(graph, start_time_sec, criterion)
    best_solution = current_solution.duplicate()
    best_cost = current_solution.cost
    tabu_limit = max(5, len(current_solution.stops) // 2) if tabu_size_limited else None
    tabu_list = []

    for _ in range(max_iterations):

        # Generate all neighbors possible moves and optional sample them to reduce the search space
        neighbors = generate_neighbors(current_solution)
        if sample_size:
            neighbors = sample(neighbors, sample_size, sample_strategy)
        iteration_best_cost = float('inf')
        iteration_best_solution = None
        chosen_move = None

        for start, end, new_stops in neighbors:
            is_forbidden = ((start, end) in tabu_list) or ((end, start) in tabu_list)
            temp_solution = current_solution.duplicate()
            temp_solution.stops = new_stops
            temp_solution.calculate_cost(graph, start_time_sec, criterion)
            cost = temp_solution.cost
            if cost == float('inf'):
                continue

            # Skip forbidden except aspirational bypass
            if is_forbidden and not (is_aspirational and cost < best_cost):
                continue

            # Update the best solution if the cost is lower than the current best
            if cost < iteration_best_cost:
                iteration_best_cost = cost
                iteration_best_solution = temp_solution
                chosen_move = (start, end)

        if iteration_best_solution is None:
            break

        # Update the best solution if the cost is lower than the current best
        current_solution = iteration_best_solution
        if iteration_best_cost < best_cost:
            best_cost = iteration_best_cost
            best_solution = current_solution.duplicate()

        # Add the move to the tabu list and control its length
        tabu_list.append(chosen_move)
        if tabu_limit is not None and len(tabu_list) > tabu_limit:
            tabu_list.pop(0)  # Remove the oldest move

    return best_solution

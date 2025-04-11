import pickle
import random
from copy import deepcopy
from pathlib import Path
from typing import Sequence

from src.shortest_path.graph import Graph, Edge
from src.shortest_path.main import shortest_path
from src.utils import convert_to_seconds, format_time


class Solution:
    def __init__(self, stops_sequence: list[Edge]):
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


def tabu_search_tsp(
    graph: Graph,
    initial_solution: Solution,
    start_time_sec: int,
    tabu_size_no_limit: bool = True,
    is_aspirational: bool = False,
    max_iterations=100,
    sample_size=None,
    sample_strategy='random',
    criterion='t',
):
    current_solution = initial_solution
    current_solution.calculate_cost(graph, start_time_sec, criterion)
    best_solution = current_solution.duplicate()
    best_cost = current_solution.cost
    tabu_limit = None if tabu_size_no_limit else max(5, len(current_solution.stops) // 2)
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

            if is_forbidden:
                # Aspirational bypass
                if is_aspirational and cost < best_cost:
                    is_forbidden = False
                else:
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


if __name__ == "__main__":
    data_path = Path(__file__).parent.parent.parent / "data"
    with open(data_path / 'graph.pkl', 'rb') as f:
        g = pickle.load(f)


    start_stop = "Dworzec Główny (Dworcowa)".lower()
    stops_to_visit = ["tarczyński arena (lotnicza)", "GALERIA DOMINIKAŃSKA".lower(), "Stadion Olimpijski".lower()]
    criterion = 't'
    start_time = "08:00:00"


    start_time_sec = convert_to_seconds(start_time)

    route_stops = [start_stop] + stops_to_visit + [start_stop]
    initial_sol = Solution(route_stops)

    best_sol_a = tabu_search_tsp(
        g,
        initial_sol,
        tabu_size_no_limit=False,
        max_iterations=200,
        criterion=criterion,
        start_time_sec=start_time_sec
    )

    print("=== (a) Tabu Search bez ograniczenia rozmiaru T ===")
    for x in best_sol_a.flat_path:
        print(f"{x.line}, {format_time(x.departure_sec)}, {x.start_stop_name}, {format_time(x.arrival_sec)}, {x.end_stop_name}")
    print("Całkowity koszt:", best_sol_a.cost)

# best_sol_b = tabu_search_tsp(graph, initial_sol, tabu_version='dynamic', max_iterations=200)
# print("\n=== (b) Tabu Search z dynamicznym doborem rozmiaru T ===")
# for (linia, dep_s, st_pocz, arr_s, st_kon) in best_sol_b.get_flat_path():
#     print(f"{linia}, {Graph.seconds_to_hhmmss(dep_s)}, {st_pocz}, {Graph.seconds_to_hhmmss(arr_s)}, {st_kon}")
# print("Całkowity koszt:", best_sol_b.total_cost)
#
# best_sol_c = tabu_search_tsp(graph, initial_sol, tabu_version='aspiration', max_iterations=200)
# print("\n=== (c) Tabu Search z aspiracją ===")
# for (linia, dep_s, st_pocz, arr_s, st_kon) in best_sol_c.get_flat_path():
#     print(f"{linia}, {Graph.seconds_to_hhmmss(dep_s)}, {st_pocz}, {Graph.seconds_to_hhmmss(arr_s)}, {st_kon}")
# print("Całkowity koszt:", best_sol_c.total_cost)
#
# best_sol_d = tabu_search_tsp(graph, initial_sol, tabu_version='sampling', max_iterations=200, sample_size=30, sample_strategy='random')
# print("\n=== (d) Tabu Search z próbkowaniem sąsiedztwa (30 losowych sąsiadów) ===")
# for (linia, dep_s, st_pocz, arr_s, st_kon) in best_sol_d.get_flat_path():
#     print(f"{linia}, {Graph.seconds_to_hhmmss(dep_s)}, {st_pocz}, {Graph.seconds_to_hhmmss(arr_s)}, {st_kon}")
# print("Całkowity koszt:", best_sol_d.total_cost)
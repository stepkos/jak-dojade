import pickle
import random
from pathlib import Path

from src.shortest_path.main import shortest_path
from src.utils import convert_to_seconds, format_time


class TSPSolution:

    def __init__(self, stops_sequence, start_time_sec, criterion='t'):
        self.stops = stops_sequence[:]       # Kolejność przystanków
        self.paths = []                      # Lista ścieżek między kolejnymi przystankami
        self.total_cost = float('inf')       # Całkowity koszt rozwiązania (czas lub przesiadki)
        self.start_time = start_time_sec     # Czas rozpoczęcia podróży
        self.criterion = criterion           # Kryterium optymalizacji ('t' lub 'p')

    def copy(self):
        new_sol = TSPSolution(self.stops, self.start_time, self.criterion)
        new_sol.paths = self.paths[:]
        new_sol.total_cost = self.total_cost
        return new_sol

    def evaluate(self, graph):
        self.paths = []
        current_time = self.start_time
        total_cost = 0

        for i in range(len(self.stops) - 1):
            src = self.stops[i]
            dst = self.stops[i+1]

            path, score, n_lines = shortest_path(
                graph=graph,
                start_stop=src,
                end_stop=dst,
                start_time_sec=current_time,
                criterion=self.criterion,
            )

            cost_segment = score
            edges_segment = [
                (x.line, x.departure_sec, x.start_stop_name, x.arrival_sec, x.end_stop_name) for x in path
            ]

            if cost_segment is None:
                self.total_cost = float('inf')
                return self.total_cost

            self.paths.append((cost_segment, edges_segment))
            total_cost += cost_segment

            if self.criterion == 't':
                if edges_segment:
                    current_time = edges_segment[-1][3]
                else:
                    current_time += cost_segment
            else:
                if edges_segment:
                    current_time = edges_segment[-1][3]

        self.total_cost = total_cost
        return self.total_cost

    def get_flat_path(self):
        flat_path = []
        for (cost_seg, edges_seg) in self.paths:
            flat_path.extend(edges_seg)
        return flat_path


def sample_neighborhood(neighbors, sample_size=None, strategy='random'):
    # 'systematic': wybiera co n-ty element (równomierne próbkowanie)
    if sample_size is None or sample_size >= len(neighbors):
        return neighbors

    if strategy == 'random':
        return random.sample(neighbors, sample_size)

    elif strategy == 'systematic':
        step = max(1, len(neighbors) // sample_size)
        return [neighbors[i] for i in range(0, len(neighbors), step)][:sample_size]

    else:
        return random.sample(neighbors, sample_size)


def two_opt_swap(stops, i, j):
    if i >= j:
        return stops[:]
    new_stops = stops[:]
    new_stops[i:j+1] = reversed(new_stops[i:j+1])
    return new_stops


def generate_neighbors(solution):
    stops = solution.stops
    n = len(stops)
    nbrs = []

    # Pomiń przystanek początkowy (index 0) oraz końcowy (index n-1) — zakładamy cykl
    for i in range(1, n - 2):
        for j in range(i + 1, n - 1):
            new_stops = two_opt_swap(stops, i, j)
            nbrs.append((i, j, new_stops))

    return nbrs


def calculate_dynamic_tabu_size(num_stops):
    return max(5, num_stops // 2)


def tabu_search_tsp(
    graph,
    initial_sol,
    tabu_version='nolimit',  # 'nolimit', 'dynamic', 'aspiration', 'sampling', ...
    max_iterations=100,
    sample_size=None,
    sample_strategy='random'
):
    """
    Obsługiwane tryby działania:
      (a) 'nolimit'     – brak ograniczenia długości listy Tabu
      (b) 'dynamic'     – długość listy Tabu zależna od liczby przystanków
      (c) 'aspiration'  – dopuszczenie tabu ruchu, jeśli daje najlepszy wynik globalny
      (d) 'sampling'    – ograniczenie liczby sąsiadów analizowanych w każdej iteracji

    :param sample_size: Maksymalna liczba sąsiadów analizowanych w jednej iteracji
    :param sample_strategy: Sposób próbkowania sąsiedztwa ('random' lub 'systematic')
    :return: Najlepsze znalezione rozwiązanie TSPSolution
    """
    current_sol = initial_sol
    current_sol.evaluate(graph)
    best_sol = current_sol.copy()
    best_cost = current_sol.total_cost

    if tabu_version == 'nolimit':
        tabu_size = None
    elif tabu_version == 'dynamic':
        n_stops = len(current_sol.stops)
        tabu_size = calculate_dynamic_tabu_size(n_stops)
    else:
        tabu_size = 7

    tabu_list = []

    for iteration in range(max_iterations):
        all_neighbors = generate_neighbors(current_sol)
        used_neighbors = sample_neighborhood(all_neighbors, sample_size, sample_strategy)

        best_neighbor = None
        best_neighbor_cost = float('inf')
        best_move = None

        for (i, j, new_stops) in used_neighbors:
            move = (i, j)

            is_tabu = (move in tabu_list) or ((j, i) in tabu_list)

            tmp_sol = current_sol.copy()
            tmp_sol.stops = new_stops
            cost_val = tmp_sol.evaluate(graph)
            if cost_val == float('inf'):
                continue  # pomijamy rozwiązania niepełne

            # Reguła aspiracji – dopuszczamy tabu, jeśli ruch poprawia najlepsze globalne rozwiązanie
            if is_tabu:
                if tabu_version == 'aspiration' or tabu_version == 'sampling':
                    if cost_val < best_cost:
                        is_tabu = False
                    else:
                        continue
                else:
                    continue

            # Aktualizacja najlepszego sąsiada w tej iteracji
            if cost_val < best_neighbor_cost:
                best_neighbor_cost = cost_val
                best_neighbor = tmp_sol
                best_move = move

        if best_neighbor is None:
            break  # brak poprawnych sąsiadów – kończymy

        current_sol = best_neighbor

        if best_neighbor_cost < best_cost:
            best_cost = best_neighbor_cost
            best_sol = current_sol.copy()
        tabu_list.append(best_move)
        if tabu_size is not None and len(tabu_list) > tabu_size:
            tabu_list.pop(0)

    return best_sol


if __name__ == "__main__":
    data_path = Path(__file__).parent.parent.parent / "data"
    with open(data_path / 'graph.pkl', 'rb') as f:
        g = pickle.load(f)


    start_stop = "Dworzec Główny (Dworcowa)".lower()
    stops_to_visit = ["tarczyński arena (lotnicza)", "GALERIA DOMINIKAŃSKA".lower(), "Stadion Olimpijski".lower()]
    criterion = 't'
    start_time = "08:00:00"


    start_time_sec = convert_to_seconds(start_time)
    # result = shortest_path(
    #     graph=g,
    #     start_stop=start,
    #     end_stop=end,
    #     start_time_sec=start_time_sec,
    #     criterion=criterion,
    # )

    route_stops = [start_stop] + stops_to_visit + [start_stop]
    initial_sol = TSPSolution(route_stops, start_time_sec, criterion)

    best_sol_a = tabu_search_tsp(g, initial_sol, tabu_version='nolimit', max_iterations=200)
    print("=== (a) Tabu Search bez ograniczenia rozmiaru T ===")
    for (linia, dep_s, st_pocz, arr_s, st_kon) in best_sol_a.get_flat_path():
        print(f"{linia}, {format_time(dep_s)}, {st_pocz}, {format_time(arr_s)}, {st_kon}")
    print("Całkowity koszt:", best_sol_a.total_cost)

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
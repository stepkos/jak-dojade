import pickle
import random
from pathlib import Path

from src.shortest_path.graph import Graph
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


def tabu_search_tsp(
    graph: Graph,
    initial_solution: TSPSolution,
    tabu_size_no_limit: bool = True,
    is_aspirational: bool = False,
    max_iterations=100,
    sample_size=None,
    sample_strategy='random'
):
    # Setup initial solution
    current_solution = initial_solution
    current_solution.evaluate(graph)
    best_solution = current_solution.copy()
    best_cost = current_solution.total_cost

    # Ustalenie limitu dla listy tabu w zależności od strategii
    tabu_limit = None if tabu_size_no_limit else max(5, len(current_solution.stops) // 2)
    tabu_list = []  # lista przechowująca zakazane ruchy

    # Główna pętla przeszukiwania
    for _ in range(max_iterations):
        # Wygeneruj sąsiedztwo danego rozwiązania
        neighbors = generate_neighbors(current_solution)
        sampled_neighbors = sample_neighborhood(neighbors, sample_size, sample_strategy)

        iteration_best_cost = float('inf')
        iteration_best_solution = None
        chosen_move = None

        # Przegląd wszystkich wylosowanych sąsiadów
        for neigh in sampled_neighbors:
            i, j, new_stops = neigh
            proposed_move = (i, j)
            reverse_move = (j, i)

            # Sprawdzenie, czy ruch jest na liście zakazanych
            is_forbidden = (proposed_move in tabu_list) or (reverse_move in tabu_list)

            # Tworzymy kopię bieżącego rozwiązania i aktualizujemy trasę
            temp_solution = current_solution.copy()
            temp_solution.stops = new_stops
            cost = temp_solution.evaluate(graph)
            if cost == float('inf'):
                continue  # pomijamy niedokończone/trudne rozwiązania

            # Reguła aspiracji – jeśli ruch, mimo że zakazany, daje lepsze globalne rozwiązanie,
            # to pozwalamy na jego wykonanie
            if is_forbidden:
                if is_aspirational and cost < best_cost:
                    is_forbidden = False
                else:
                    continue

            # Aktualizacja najlepszego rozwiązania w bieżącej iteracji
            if cost < iteration_best_cost:
                iteration_best_cost = cost
                iteration_best_solution = temp_solution
                chosen_move = proposed_move

        # Jeśli nie znaleziono żadnego poprawnego rozwiązania, kończymy działanie
        if iteration_best_solution is None:
            break

        # Aktualizacja bieżącego i najlepszego globalnego rozwiązania
        current_solution = iteration_best_solution
        if iteration_best_cost < best_cost:
            best_cost = iteration_best_cost
            best_solution = current_solution.copy()

        # Dodanie ruchu do historii tabu i kontrola długości listy
        tabu_list.append(chosen_move)
        if tabu_limit is not None and len(tabu_list) > tabu_limit:
            tabu_list.pop(0)

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
    initial_sol = TSPSolution(route_stops, start_time_sec, criterion)

    best_sol_a = tabu_search_tsp(g, initial_sol, tabu_size_no_limit=False, max_iterations=200)
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
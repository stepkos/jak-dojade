import os
from pathlib import Path

import pandas as pd
import pickle

from src.shortest_path.graph import Graph
from src.traveling_salesman.tabu_search import Solution, tabu_search
from src.utils import convert_to_seconds, format_time


def main():
    data_path = Path(__file__).parent.parent.parent / "data"

    if os.path.exists(data_path / 'graph.pkl'):
        with open(data_path / 'graph.pkl', 'rb') as f:
            g = pickle.load(f)
    else:
        df_ = pd.read_csv(data_path / "wroclaw-mpk.csv", low_memory=False)
        g = Graph.create_from_df(df_)

        with open(data_path / 'graph.pkl', 'wb') as f:
            pickle.dump(g, f)

    # Dane testowe
    # małopanewska
    # Hala Stulecia;Stanki;RACŁAWICKA;Bałtycka;Wyszyńskiego;Stadion Olimpijski
    start_stop = input("Podaj przystanek początkowy: ").strip().lower()
    stops_to_visit_str = input("Podaj przystanki przejściowe rozdzielone średnikiem: ").strip()
    stops_to_visit = [s.lower() for s in stops_to_visit_str.split(';')]
    criterion = input("Podaj kryterium: t/p (czas/przesiadki): ").strip().lower()
    start_time = input("Podaj czas początkowy (HH:MM): ").strip()

    start_time_sec = convert_to_seconds(start_time)
    initial_stops = [start_stop] + stops_to_visit + [start_stop]
    initial_solution = Solution(initial_stops)

    solution = tabu_search(
        g,
        initial_solution,
        start_time_sec=start_time_sec,
        criterion=criterion,
        tabu_size_limited=False,
        is_aspirational=True,
        max_iterations=300,
        sample_size=None,
        sample_strategy='random',
    )

    for edge in solution.flat_path:
        print(
            f"{edge.start_stop_name} -> {edge.end_stop_name}, "
            f"linia {edge.line}, "
            f"{format_time(edge.departure_sec)} -> {format_time(edge.arrival_sec)}"
        )

    print("Całkowity koszt:", solution.cost)


if __name__ == "__main__":
    main()

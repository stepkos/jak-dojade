import os

import pandas as pd
import pickle

from src.algorithms import dijkstra_shortest_travel_time, astar_shortest_travel_time_with_changes
from src.distance import haversine_distance
from src.graph import Graph

CHANGE_LINE_COST = 10000000
HEURISTIC_MULTIPLIER = 1600


def format_time(seconds) -> str:
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours:02d}:{minutes:02d}"


if __name__ == "__main__":

    if os.path.exists('./../graph.pkl'):
        with open('./../graph.pkl', 'rb') as f:
            g = pickle.load(f)
    else:
        df_ = pd.read_csv("./../data.csv", low_memory=False)
        g = Graph.create_from_df(df_)

        with open('./../graph.pkl', 'wb') as f:
            pickle.dump(g, f)

    # Dane testowe: małopanewska, hala stulecia
    start = input("Podaj przystanek początkowy: ").lower()
    end = input("Podaj przystanek końcowy: ").lower()
    criterion = input("Podaj kryterium: t/p (czas/przesiadki): ").lower()
    start_time = input("Podaj czas początkowy (HH:MM): ")

    start_time_sec = (
        int(start_time.split(":")[0]) * 3600 +
        int(start_time.split(":")[1]) * 60
    )

    if criterion == "t":
        result = dijkstra_shortest_travel_time(
            graph=g,
            start_stop=start,
            end_stop=end,
            start_time_sec=start_time_sec,
        )
    else:
        result = astar_shortest_travel_time_with_changes(
            graph=g,
            start_stop=start,
            end_stop=end,
            start_time_sec=start_time_sec,
            heuristic_func=haversine_distance,
            heuristic_multiplier=HEURISTIC_MULTIPLIER,
            change_line_cost=CHANGE_LINE_COST,
        )

    path, arrival_time, n_lines = result

    if path:
        print("Znaleziono ścieżkę:")
        for edge in path:
            print(
                f"{edge.start_stop_name} -> {edge.end_stop_name}, "
                f"linia {edge.line}, "
                f"{format_time(edge.departure_sec)} -> {format_time(edge.arrival_sec)}"
            )
        print(f"Czas dotarcia: {format_time(arrival_time)}")
        print(f"Liczba przejazdow: {n_lines}")
    else:
        print("Brak połączenia")

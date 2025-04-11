import os
from pathlib import Path

import pandas as pd
import pickle

from src.shortest_path.algorithms import dijkstra_shortest_travel_time, astar_shortest_travel
from src.shortest_path.distance import haversine_distance
from src.shortest_path.graph import Graph, Edge
from src.utils import format_time, convert_to_seconds

CHANGE_LINE_COST = 10000000
HEURISTIC_MULTIPLIER = 1600


def shortest_path(
    graph: Graph,
    start_stop: str,
    end_stop: str,
    start_time_sec: int,
    criterion: str,
) -> tuple[list[Edge] | None, int, int]:
    if criterion == "t":
        return dijkstra_shortest_travel_time(
            graph=graph,
            start_stop=start_stop,
            end_stop=end_stop,
            start_time_sec=start_time_sec,
        )
    return astar_shortest_travel(
        graph=graph,
        start_stop=start_stop,
        end_stop=end_stop,
        start_time_sec=start_time_sec,
        heuristic_func=haversine_distance,
        heuristic_multiplier=HEURISTIC_MULTIPLIER,
        change_line_cost=CHANGE_LINE_COST,
    )


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

    # Dane testowe: małopanewska, hala stulecia
    start = input("Podaj przystanek początkowy: ").strip().lower()
    end = input("Podaj przystanek końcowy: ").strip().lower()
    criterion = input("Podaj kryterium: t/p (czas/przesiadki): ").strip().lower()
    start_time = input("Podaj czas początkowy (HH:MM): ")

    start_time_sec = convert_to_seconds(start_time)
    result = shortest_path(
        graph=g,
        start_stop=start,
        end_stop=end,
        start_time_sec=start_time_sec,
        criterion=criterion,
    )

    path, score, n_lines = result

    if path:
        print("Znaleziono ścieżkę:")
        for edge in path:
            print(
                f"{edge.start_stop_name} -> {edge.end_stop_name}, "
                f"linia {edge.line}, "
                f"{format_time(edge.departure_sec)} -> {format_time(edge.arrival_sec)}"
            )
        print(f"Czas dotarcia: {format_time(path[-1].arrival_sec)}")
        print(f"Score: {score}")
        print(f"Liczba przejazdow: {n_lines}")
    else:
        print("Brak połączenia")


if __name__ == "__main__":
    main()

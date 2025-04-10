import os
from pathlib import Path

import pandas as pd
import pickle

from src.shortest_path.graph import Graph
from src.shortest_path.main import shortest_path
from src.utils import convert_to_seconds


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
    # Hala Stulecia;Stanki;RACŁAWICKA;Bałtycka;Wyszyńskiego
    start_stop = input("Podaj przystanek początkowy: ").strip().lower()
    stops_to_visit = [s.lower() for s in input("Podaj przystanki przejściowe: ").strip().split(';')]
    criterion = input("Podaj kryterium: t/p (czas/przesiadki): ").strip().lower()
    start_time = input("Podaj czas początkowy (HH:MM): ").strip()

    start_time_sec = convert_to_seconds(start_time)
    result = shortest_path(
        graph=g,
        start_stop=start,
        end_stop=end,
        start_time_sec=start_time_sec,
        criterion=criterion,
    )


    # path, arrival_time, n_lines = result
    #
    # if path:
    #     print("Znaleziono ścieżkę:")
    #     for edge in path:
    #         print(
    #             f"{edge.start_stop_name} -> {edge.end_stop_name}, "
    #             f"linia {edge.line}, "
    #             f"{format_time(edge.departure_sec)} -> {format_time(edge.arrival_sec)}"
    #         )
    #     print(f"Czas dotarcia: {format_time(arrival_time)}")
    #     print(f"Liczba przejazdow: {n_lines}")
    # else:
    #     print("Brak połączenia")

if __name__ == "__main__":
    main()

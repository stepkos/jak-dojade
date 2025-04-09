import heapq
import pickle
import pandas as pd

from src.graph import Graph, Edge

DAY = 24 * 3600


def dijkstra_shortest_travel_time(graph: Graph, start_stop: str, end_stop: str, start_time_sec: int):
    # Kolejka priorytetowa: (czas dotarcia, nazwa przystanku, ostatnia linia, historia przejazdu)
    queue = [(start_time_sec, start_stop, None, [])]

    # Najlepsze czasy dotarcia do danego przystanku
    best_arrival_times = {stop: float('inf') for stop in graph.nodes}
    best_arrival_times[start_stop] = start_time_sec

    while queue:
        current_time, current_stop, last_line, path = heapq.heappop(queue)

        # Jeśli jesteśmy u celu – koniec
        if current_stop == end_stop:
            return path, current_time

        current_node = graph.nodes[current_stop]

        for edge in current_node.outgoing_edges:
            arrival_time = edge.arrival_sec + ((current_time // DAY) * DAY)
            # Nie możemy jechać wcześniej niż przyjechaliśmy
            if edge.departure_sec < current_time % DAY:
                arrival_time = arrival_time + DAY

            if edge.departure_sec > edge.arrival_sec:
                arrival_time = arrival_time + DAY

            # Jeśli to szybsza droga niż dotychczas znana
            if arrival_time < best_arrival_times[edge.end_stop_name]:
                best_arrival_times[edge.end_stop_name] = arrival_time
                new_path = path + [edge]
                heapq.heappush(queue, (arrival_time, edge.end_stop_name, edge.line, new_path))

    return None, float('inf')  # Brak ścieżki


def format_time(seconds) -> str:
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours:02d}:{minutes:02d}"


if __name__ == "__main__":

    # df_ = pd.read_csv("./../data.csv", low_memory=False)
    # print(1)
    #
    # g = Graph.create_from_df(df_)
    # print(2)
    #
    # with open('graph.pkl', 'wb') as f:
    #     pickle.dump(g, f)

    with open('graph.pkl', 'rb') as f:
        g = pickle.load(f)

    result = dijkstra_shortest_travel_time(
        graph=g,
        start_stop="pl. Bema".lower(),
        end_stop="DWORZEC GŁÓWNY".lower(),
        # start_time_sec=23 * 3600 + 60 * 58  # 8:00 rano
        start_time_sec=60 * 60 * 8
    )
    print(4)
    path, arrival_time = result

    if path:
        print("Znaleziono ścieżkę:")
        for edge in path:
            print(
                f"{edge.start_stop_name} -> {edge.end_stop_name}, "
                f"linia {edge.line}, "
                f"{format_time(edge.departure_sec)} -> {format_time(edge.arrival_sec)}"
            )
        print(f"Czas dotarcia: {format_time(arrival_time)}")
    else:
        print("Brak połączenia")

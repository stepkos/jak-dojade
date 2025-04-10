import heapq
import pickle
from typing import Callable

import pandas as pd

from src.distance import euclides_distance, haversine_distance
from src.graph import Graph, Edge


SECONDS_IN_DAY = 24 * 3600

CONNECTION_COST = 10000000

HEURISTIC_MULTIPLIER = 1600

def dijkstra_shortest_travel_time(
    graph: Graph, start_stop: str, end_stop: str, start_time_sec: int
) -> tuple[list[Edge] | None, int]:
    # Priority queue (start_time, start_stop, last_line, path)
    queue = [(start_time_sec, start_stop, None, [])]

    # The best arrival times to each stop
    best_arrival_times = {stop: float('inf') for stop in graph.nodes}
    best_arrival_times[start_stop] = start_time_sec
    visited = set()

    while queue:
        # Pop the stop with the earliest arrival time
        current_time, current_stop, last_line, path = heapq.heappop(queue)

        # Check if we have already visited this stop
        if current_stop in visited:
            continue
        visited.add(current_stop)

        # End algorithm if we are at the destination
        if current_stop == end_stop:
            return path, current_time

        # Get current node and iterate over all outgoing edges
        current_node = graph.nodes[current_stop]
        for edge in current_node.outgoing_edges:

            # Add one day if we are after midnight
            arrival_time = edge.arrival_sec + ((current_time // SECONDS_IN_DAY) * SECONDS_IN_DAY)

            # We cannot go earlier than we arrived at current stop
            if edge.departure_sec < current_time % SECONDS_IN_DAY:
                arrival_time = arrival_time + SECONDS_IN_DAY

            # If departure time is after arrival time, we know it's midnight case
            if edge.departure_sec > edge.arrival_sec:
                arrival_time = arrival_time + SECONDS_IN_DAY

            # Update best time and push queue if we found a better path
            if arrival_time < best_arrival_times[edge.end_stop_name]:
                best_arrival_times[edge.end_stop_name] = arrival_time
                new_path = path + [edge]
                heapq.heappush(
                    queue,
                    (arrival_time, edge.end_stop_name, edge.line, new_path)
                )

    return None, -1  # No path found


def astar_shortest_travel_time(
    graph: Graph,
    start_stop: str,
    end_stop: str,
    start_time_sec: int,
    heuristic_func: Callable[[Graph, str, str], float | int]
) -> tuple[list[Edge] | None, int, int]:
    # Priority queue (cost, start_stop, last_line, path, lines)
    queue = [
        (
            start_time_sec + heuristic_func(graph, start_stop, end_stop),
            start_time_sec, start_stop, None, [], 0
        )
    ]

    # The best score for each stop
    best_arrival_costs = {stop: float('inf') for stop in graph.nodes}
    best_arrival_costs[start_stop] = start_time_sec + heuristic_func(graph, start_stop, end_stop)
    visited = set()

    while queue:
        # Pop the stop with the earliest arrival time
        score, current_time, current_stop, last_line, path, n_routes = heapq.heappop(queue)

        # Check if we have already visited this stop
        if current_stop in visited:
            continue
        visited.add(current_stop)

        # End algorithm if we are at the destination
        if current_stop == end_stop:
            return path, current_time, n_routes

        # Get current node and iterate over all outgoing edges
        current_node = graph.nodes[current_stop]
        for edge in current_node.outgoing_edges:

            # Add one day if we are after midnight
            arrival_time = edge.arrival_sec + ((current_time // SECONDS_IN_DAY) * SECONDS_IN_DAY)

            # We cannot go earlier than we arrived at current stop
            if edge.departure_sec < current_time % SECONDS_IN_DAY:
                arrival_time = arrival_time + SECONDS_IN_DAY

            # If departure time is after arrival time, we know it's midnight case
            if edge.departure_sec > edge.arrival_sec:
                arrival_time = arrival_time + SECONDS_IN_DAY

            # Update the number of routes if we changed the line
            n_routes_new = n_routes
            if last_line != edge.line or current_time % SECONDS_IN_DAY != edge.departure_sec:
                n_routes_new += 1

            # Calculate the cost
            cost = (
                arrival_time
                + heuristic_func(graph, edge.end_stop_name, end_stop)
                * HEURISTIC_MULTIPLIER
                + n_routes_new * CONNECTION_COST
            )

            # Update best time and push queue if we found a better path
            if cost < best_arrival_costs[edge.end_stop_name]:
                best_arrival_costs[edge.end_stop_name] = cost
                new_path = path + [edge]
                heapq.heappush(
                    queue,
                    (cost, arrival_time, edge.end_stop_name, edge.line, new_path, n_routes_new)
                )

    return None, -1, -1  # No path found



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

    print(1, euclides_distance(g, "małopanewska", "hala stulecia"))
    print(2, haversine_distance(g, "małopanewska", "hala stulecia"))

    result = astar_shortest_travel_time(
    # result = dijkstra_shortest_travel_time(
        graph=g,
        # start_stop="pl. Bema".lower(),
        # end_stop="DWORZEC GŁÓWNY".lower(),
        start_stop="Małopanewska".lower(),
        end_stop="Hala Stulecia".lower(),
        # start_time_sec=23 * 3600 + 60 * 58
        start_time_sec=60 * 60 * 8,
        heuristic_func=haversine_distance
    )
    path, arrival_time, n = result

    if path:
        print("Znaleziono ścieżkę:")
        for edge in path:
            print(
                f"{edge.start_stop_name} -> {edge.end_stop_name}, "
                f"linia {edge.line}, "
                f"{format_time(edge.departure_sec)} -> {format_time(edge.arrival_sec)}"
            )
        print(f"Czas dotarcia: {format_time(arrival_time)}")
        print(f"Liczba przejazdow: {n}")
    else:
        print("Brak połączenia")

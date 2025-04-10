import heapq
from typing import Callable
from src.graph import Graph, Edge

SECONDS_IN_DAY = 24 * 3600


def dijkstra_shortest_travel_time(
    graph: Graph, start_stop: str, end_stop: str, start_time_sec: int
) -> tuple[list[Edge] | None, int, int]:
    # Priority queue (start_time, start_stop, last_line, path, n_lines)
    queue = [(start_time_sec, start_stop, None, [], 0)]

    # The best arrival times to each stop
    best_arrival_times = {stop: float('inf') for stop in graph.nodes}
    best_arrival_times[start_stop] = start_time_sec
    visited = set()

    while queue:
        # Pop the stop with the earliest arrival time
        current_time, current_stop, last_line, path, n_lines = heapq.heappop(queue)

        # Check if we have already visited this stop
        if current_stop in visited:
            continue
        visited.add(current_stop)

        # End algorithm if we are at the destination
        if current_stop == end_stop:
            return path, current_time, n_lines

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
            n_lines_new = n_lines
            if last_line != edge.line or current_time % SECONDS_IN_DAY != edge.departure_sec:
                n_lines_new += 1

            # Update best time and push queue if we found a better path
            if arrival_time < best_arrival_times[edge.end_stop_name]:
                best_arrival_times[edge.end_stop_name] = arrival_time
                new_path = path + [edge]
                heapq.heappush(
                    queue,
                    (arrival_time, edge.end_stop_name, edge.line, new_path, n_lines_new)
                )

    return None, -1, -1  # No path found


def astar_shortest_travel_time(
    graph: Graph,
    start_stop: str,
    end_stop: str,
    start_time_sec: int,
    heuristic_func: Callable[[Graph, str, str], float | int],
    heuristic_multiplier: int,
    change_line_cost: int,
) -> tuple[list[Edge] | None, int, int]:
    # Priority queue (cost, start_stop, last_line, path, n_lines)
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
        score, current_time, current_stop, last_line, path, n_lines = heapq.heappop(queue)

        # Check if we have already visited this stop
        if current_stop in visited:
            continue
        visited.add(current_stop)

        # End algorithm if we are at the destination
        if current_stop == end_stop:
            return path, current_time, n_lines

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
            n_lines_new = n_lines
            if last_line != edge.line or current_time % SECONDS_IN_DAY != edge.departure_sec:
                n_lines_new += 1

            # Calculate the cost
            cost = (
                arrival_time
                + heuristic_func(graph, edge.end_stop_name, end_stop)
                * heuristic_multiplier
                + (n_lines_new - 1) * change_line_cost
            )

            # Update best time and push queue if we found a better path
            if cost < best_arrival_costs[edge.end_stop_name]:
                best_arrival_costs[edge.end_stop_name] = cost
                new_path = path + [edge]
                heapq.heappush(
                    queue,
                    (cost, arrival_time, edge.end_stop_name, edge.line, new_path, n_lines_new)
                )

    return None, -1, -1  # No path found

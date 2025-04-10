from math import radians, sin, cos, sqrt, atan2

from src.graph import Graph


def euclides_distance(graph: Graph, stop: str, end_stop: str):
    lat1 = graph.nodes[stop].latitude
    lon1 = graph.nodes[stop].longitude
    lat2 = graph.nodes[end_stop].latitude
    lon2 = graph.nodes[end_stop].longitude

    distance = ((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2) ** 0.5
    return distance


def haversine_distance(graph: Graph, stop: str, end_stop: str) -> float:
    # Radius of the Earth in kilometers
    earth_radius = 6371.0

    # Convert latitude and longitude from degrees to radians
    lat_1 = radians(graph.nodes[stop].latitude)
    lon_1 = radians(graph.nodes[stop].longitude)
    lat_2 = radians(graph.nodes[end_stop].latitude)
    lon_2 = radians(graph.nodes[end_stop].longitude)

    # Differences
    d_lat = lat_2 - lat_1
    d_lon = lon_2 - lon_1

    # Haversine formula
    a = sin(d_lat / 2)**2 + cos(lat_1) * cos(lat_2) * sin(d_lon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    # Distance in kilometers
    return earth_radius * c

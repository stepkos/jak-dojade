from collections import defaultdict
from dataclasses import dataclass, field
from functools import partial

import pandas as pd


@dataclass
class Edge:
    start_stop_name: int
    end_stop_name: int
    departure_sec: int
    arrival_sec: int
    line: str
    company: str

    @property
    def duration(self) -> int:
        return self.arrival_sec - self.departure_sec


@dataclass
class Node:
    """
    One Node for specific stop name.
    Many variants of the same stop have averaged coordinates.
    """
    stop_name: str
    latitude: float
    longitude: float
    outgoing_edges: list[Edge] = field(default_factory=list)


class Graph:

    def __init__(self, nodes: dict[str, Node]):
        self.nodes = nodes

        # Sort outgoing edges for each node by departure time
        for node in nodes.values():
            node.outgoing_edges = sorted(node.outgoing_edges, key=lambda x: x.departure_sec)

    @staticmethod
    def _normalize_df(df: pd.DataFrame) -> pd.DataFrame:
        seconds_in_a_day = 60 * 60 * 24

        df["line"] = df["line"].astype(str).str.strip().str.lower()
        df["company"] = df["company"].astype(str).str.strip().str.lower()

        df["departure_sec"] = pd.to_timedelta(df["departure_time"]).dt.total_seconds() % seconds_in_a_day
        df["arrival_sec"] = pd.to_timedelta(df["arrival_time"]).dt.total_seconds() % seconds_in_a_day

        df["start_stop"] = df["start_stop"].astype(str).str.strip().str.lower()
        df["end_stop"] = df["end_stop"].astype(str).str.strip().str.lower()

        return df

    @classmethod
    def create_from_df(cls, df: pd.DataFrame):
        df = cls._normalize_df(df)

        nodes_raw = defaultdict(set)
        for _, row in df.iterrows():
            nodes_raw[row['start_stop']].add((row['start_stop_lat'], row['start_stop_lon']))
            nodes_raw[row['end_stop']].add((row['end_stop_lat'], row['end_stop_lon']))

        nodes_avg: dict[str, Node] = {}
        for stop_name, coords_set in nodes_raw.items():
            nodes_avg[stop_name] = Node(
                stop_name=stop_name,
                latitude=sum([c[0] for c in coords_set]) / len(coords_set),
                longitude=sum([c[1] for c in coords_set]) / len(coords_set)
            )

        for _, row in df.iterrows():
            nodes_avg[row['start_stop']].outgoing_edges.append(
                Edge(
                    start_stop_name=row['start_stop'],
                    end_stop_name=row['end_stop'],
                    departure_sec=row['departure_sec'],
                    arrival_sec=row['arrival_sec'],
                    line=row['line'],
                    company=row['company']
                )
            )

        return cls(nodes=nodes_avg)


if __name__ == "__main__":
    df = pd.read_csv("./../data.csv", low_memory=False)
    g = Graph.create_from_df(df)

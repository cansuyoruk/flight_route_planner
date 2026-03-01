from __future__ import annotations
from typing import List
import random
from src.graph_model import FlightGraph, Route, Flight

def find_routes_random(
    graph: FlightGraph,
    origin: str,
    dest: str,
    max_connections: int,
    min_conn_min: int,
    attempts: int = 2000,
    top_n: int = 5,
) -> List[Route]:
    best: List[Route] = []

    def push(r: Route):
        best.append(r)
        # baseline sıralama: toplam süre sonra fiyat
        best.sort(key=lambda x: (x.total_travel_minutes, x.total_price))
        del best[top_n:]

    first_candidates = graph.next_flights(origin)
    if not first_candidates:
        return []

    for _ in range(attempts):
        path: List[Flight] = [random.choice(first_candidates)]

        while path[-1].dest != dest and (len(path) - 1) <= max_connections:
            nxts = graph.feasible_next(path[-1], min_conn_min)
            if not nxts:
                break
            path.append(random.choice(nxts))

        if path[-1].dest == dest and (len(path) - 1) <= max_connections:
            push(Route(path))

    return best
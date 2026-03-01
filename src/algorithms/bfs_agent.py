from __future__ import annotations
from collections import deque
from typing import List, Deque
from src.graph_model import FlightGraph, Route, Flight

def find_routes_bfs(
    graph: FlightGraph,
    origin: str,
    dest: str,
    max_connections: int,
    min_conn_min: int,
    top_n: int = 10,
) -> List[Route]:
    routes: List[Route] = []
    q: Deque[List[Flight]] = deque()

    for f in graph.next_flights(origin):
        q.append([f])

    while q and len(routes) < top_n:
        path = q.popleft()
        last = path[-1]

        if last.dest == dest:
            if (len(path) - 1) <= max_connections:
                routes.append(Route(path))
            continue

        if (len(path) - 1) >= max_connections:
            continue

        for nxt in graph.feasible_next(last, min_conn_min):
            q.append(path + [nxt])

    return routes
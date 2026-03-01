from __future__ import annotations
from typing import List, Dict
from src.graph_model import FlightGraph, Route
from src.algorithms.bfs_agent import find_routes_bfs

def _normalize(vals: List[float]) -> List[float]:
    if not vals:
        return []
    mn = min(vals)
    mx = max(vals)
    if abs(mx - mn) < 1e-9:
        return [0.0 for _ in vals]
    return [(v - mn) / (mx - mn) for v in vals]

def find_routes_greedy(
    graph: FlightGraph,
    origin: str,
    dest: str,
    max_connections: int,
    min_conn_min: int,
    weights: Dict[str, float],
    candidate_top: int = 80,
    top_n: int = 5,
) -> List[Route]:
    # Aday rotaları BFS ile üret (sonra skorlayacağız)
    candidates = find_routes_bfs(
        graph, origin, dest, max_connections, min_conn_min, top_n=candidate_top
    )
    if not candidates:
        return []

    prices = [r.total_price for r in candidates]
    travel = [r.total_travel_minutes for r in candidates]
    layover = [r.total_layover_minutes() for r in candidates]
    conns = [float(r.connections) for r in candidates]

    n_price = _normalize(prices)
    n_travel = _normalize(travel)
    n_lay = _normalize(layover)
    n_conn = _normalize(conns)

    w_price = float(weights.get("price", 1.0))
    w_travel = float(weights.get("travel", 1.0))
    w_lay = float(weights.get("layover", 1.0))
    w_conn = float(weights.get("connections", 1.0))

    scored = []
    for i, r in enumerate(candidates):
        score = (
            w_price * n_price[i]
            + w_travel * n_travel[i]
            + w_lay * n_lay[i]
            + w_conn * n_conn[i]
        )
        scored.append((score, r))

    scored.sort(key=lambda x: x[0])  # küçük skor = iyi
    return [r for _, r in scored[:top_n]]
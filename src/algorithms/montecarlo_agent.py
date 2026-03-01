from __future__ import annotations
from typing import List, Dict, Tuple
import random

from src.graph_model import Route, FlightGraph
from src.algorithms.bfs_agent import find_routes_bfs


def simulate_route(
    route: Route,
    min_conn_min: int,
    n_sims: int = 300,
    delay_mean_min: float = 10.0,
    delay_std_min: float = 15.0,
) -> Tuple[float, float]:
    """
    Returns:
      expected_travel_minutes, missed_connection_rate

    Model:
      - Each flight gets a non-negative Gaussian delay (minutes) applied to ARRIVAL.
      - If any connection becomes infeasible -> missed connection.
      - Missed connection adds a penalty (rebook delay).
    """
    def to_min(ts) -> float:
        # pandas Timestamp -> minutes (float)
        return ts.value / 1e9 / 60.0

    dep0 = to_min(route.flights[0].dep)
    arr_last = to_min(route.flights[-1].arr)
    base_travel = arr_last - dep0

    misses = 0
    total_times: List[float] = []

    for _ in range(n_sims):
        delays = [max(0.0, random.gauss(delay_mean_min, delay_std_min)) for _ in route.flights]

        # delayed arrival time of each flight (minutes)
        delayed_arr_min = [to_min(f.arr) + delays[i] for i, f in enumerate(route.flights)]

        missed = False
        for i in range(len(route.flights) - 1):
            nxt_dep_min = to_min(route.flights[i + 1].dep)
            if nxt_dep_min < (delayed_arr_min[i] + min_conn_min):
                missed = True
                break

        if missed:
            misses += 1
            total_times.append(base_travel + 8 * 60)  # 8 hours penalty
        else:
            total_times.append(base_travel + delays[-1])  # last arrival delay adds to total

    expected_time = sum(total_times) / len(total_times) if total_times else float("inf")
    missed_rate = misses / n_sims if n_sims > 0 else 1.0
    return expected_time, missed_rate


def _normalize(vals: List[float]) -> List[float]:
    if not vals:
        return []
    mn = min(vals)
    mx = max(vals)
    if abs(mx - mn) < 1e-9:
        return [0.0 for _ in vals]
    return [(v - mn) / (mx - mn) for v in vals]


def find_routes_montecarlo(
    graph: FlightGraph,
    origin: str,
    dest: str,
    max_connections: int,
    min_conn_min: int,
    weights: Dict[str, float],
    candidate_top: int = 60,
    top_n: int = 5,
    n_sims: int = 300,
    delay_mean_min: float = 10.0,
    delay_std_min: float = 15.0,
) -> List[Route]:
    candidates = find_routes_bfs(graph, origin, dest, max_connections, min_conn_min, top_n=candidate_top)
    if not candidates:
        return []

    sim_results = [simulate_route(r, min_conn_min, n_sims, delay_mean_min, delay_std_min) for r in candidates]
    exp_times = [et for et, _ in sim_results]
    risks = [rk for _, rk in sim_results]
    prices = [r.total_price for r in candidates]

    n_time = _normalize(exp_times)
    n_risk = _normalize(risks)
    n_price = _normalize(prices)

    w_price = float(weights.get("price", 1.0))
    w_time = float(weights.get("travel", 1.0))
    w_risk = float(weights.get("risk", 1.0))

    scored = []
    for i, r in enumerate(candidates):
        score = w_price * n_price[i] + w_time * n_time[i] + w_risk * n_risk[i]
        scored.append((score, r))

    scored.sort(key=lambda x: x[0])
    return [r for _, r in scored[:top_n]]
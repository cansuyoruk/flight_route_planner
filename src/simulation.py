from __future__ import annotations
from typing import Dict, Any, List, Tuple
import time
import random

from src.graph_model import FlightGraph, Route
from src.algorithms.bfs_agent import find_routes_bfs
from src.algorithms.random_agent import find_routes_random
from src.algorithms.greedy_agent import find_routes_greedy
from src.algorithms.montecarlo_agent import find_routes_montecarlo


def summarize_best(routes: List[Route]) -> Dict[str, Any]:
    if not routes:
        return {
            "found": False,
            "best_price": None,
            "best_travel_min": None,
            "best_layover_min": None,
            "best_connections": None,
            "best_path": None,
        }
    r = routes[0]
    return {
        "found": True,
        "best_price": float(r.total_price),
        "best_travel_min": float(r.total_travel_minutes),
        "best_layover_min": float(r.total_layover_minutes()),
        "best_connections": int(r.connections),
        "best_path": r.path_str(),
    }


def run_algorithm(name: str, fn) -> Dict[str, Any]:
    t0 = time.perf_counter()
    routes = fn()
    t1 = time.perf_counter()
    out = summarize_best(routes)
    out["runtime_ms"] = (t1 - t0) * 1000.0
    out["count"] = len(routes)
    return out


def generate_scenarios(airports: List[str], n: int = 20) -> List[Tuple[str, str]]:
    # unique origin-dest pairs
    pairs = set()
    while len(pairs) < n:
        o = random.choice(airports)
        d = random.choice(airports)
        if o != d:
            pairs.add((o, d))
    return list(pairs)


def run_benchmark(
    graph: FlightGraph,
    scenarios: List[Tuple[str, str]],
    max_connections: int,
    min_conn_min: int,
) -> Dict[str, Any]:
    greedy_weights = {"price": 5.0, "travel": 2.0, "layover": 1.0, "connections": 1.0}
    mc_weights = {"price": 1.0, "travel": 2.0, "risk": 5.0}

    results = { "random": [], "bfs": [], "greedy": [], "montecarlo": [] }

    for (origin, dest) in scenarios:
        # Random
        results["random"].append(run_algorithm("random", lambda: find_routes_random(
            graph, origin, dest, max_connections, min_conn_min, attempts=1500, top_n=5
        )))

        # BFS
        results["bfs"].append(run_algorithm("bfs", lambda: find_routes_bfs(
            graph, origin, dest, max_connections, min_conn_min, top_n=50
        )))

        # Greedy
        results["greedy"].append(run_algorithm("greedy", lambda: find_routes_greedy(
            graph, origin, dest, max_connections, min_conn_min, greedy_weights, candidate_top=80, top_n=5
        )))

        # Monte Carlo (keep n_sims modest for benchmark speed)
        results["montecarlo"].append(run_algorithm("montecarlo", lambda: find_routes_montecarlo(
            graph, origin, dest, max_connections, min_conn_min, mc_weights, candidate_top=60, top_n=5, n_sims=50
        )))

    return results


def aggregate(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    n = len(results)
    found = [r for r in results if r["found"]]
    success_rate = len(found) / n if n else 0.0

    def avg(key):
        vals = [r[key] for r in found if r[key] is not None]
        return sum(vals) / len(vals) if vals else None

    avg_runtime = sum(r["runtime_ms"] for r in results) / n if n else None

    return {
        "scenarios": n,
        "success_rate": success_rate,
        "avg_price": avg("best_price"),
        "avg_travel_min": avg("best_travel_min"),
        "avg_layover_min": avg("best_layover_min"),
        "avg_connections": avg("best_connections"),
        "avg_runtime_ms": avg_runtime,
    }


def print_report(all_results: Dict[str, List[Dict[str, Any]]]) -> None:
    print("\n" + "=" * 60)
    print("ALGORITHM COMPARISON REPORT")
    print("=" * 60)

    for algo in ["random", "bfs", "greedy", "montecarlo"]:
        agg = aggregate(all_results[algo])
        print(f"\n[{algo.upper()}]")
        print(f"  scenarios:      {agg['scenarios']}")
        print(f"  success_rate:   {agg['success_rate']:.2f}")
        print(f"  avg_price:      {agg['avg_price']}")
        print(f"  avg_travel_min: {agg['avg_travel_min']}")
        print(f"  avg_layover:    {agg['avg_layover_min']}")
        print(f"  avg_conn:       {agg['avg_connections']}")
        print(f"  avg_runtime_ms: {agg['avg_runtime_ms']:.2f}")


def list_airports(graph: FlightGraph) -> List[str]:
    airports = set()
    for f in graph.flights:
        airports.add(f.origin)
        airports.add(f.dest)
    return sorted(list(airports))
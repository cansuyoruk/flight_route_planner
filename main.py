from src.data_loader import load_flights_csv
from src.graph_model import FlightGraph
from src.algorithms.bfs_agent import find_routes_bfs
from src.algorithms.random_agent import find_routes_random
from src.algorithms.greedy_agent import find_routes_greedy
from src.algorithms.montecarlo_agent import find_routes_montecarlo

# Benchmark helpers
from src.simulation import (
    list_airports,
    generate_scenarios,
    run_benchmark,
    print_report,
)


def print_routes(title, routes):
    print("\n" + "=" * 20)
    print(title)
    print("=" * 20)
    print(f"Found {len(routes)} routes")
    for i, r in enumerate(routes, 1):
        print(
            f"#{i} {r.path_str()}  "
            f"price={r.total_price:.2f} "
            f"travel_min={r.total_travel_minutes:.1f} "
            f"layover={r.total_layover_minutes():.1f} "
            f"conn={r.connections}"
        )


def main():
    # Load data + build graph
    df = load_flights_csv("data/flights.csv")
    graph = FlightGraph(df)

    # Query
    origin = "IST"
    dest = "ADA"
    max_connections = 2
    min_conn_min = 45

    # BFS
    bfs_routes = find_routes_bfs(
        graph, origin, dest,
        max_connections=max_connections,
        min_conn_min=min_conn_min,
        top_n=10
    )

    # Random
    rnd_routes = find_routes_random(
        graph, origin, dest,
        max_connections=max_connections,
        min_conn_min=min_conn_min,
        attempts=2000,
        top_n=5
    )

    # Greedy (weighted scoring)
    greedy_weights = {
        "price": 5.0,
        "travel": 2.0,
        "layover": 1.0,
        "connections": 1.0,
    }

    greedy_routes = find_routes_greedy(
        graph, origin, dest,
        max_connections=max_connections,
        min_conn_min=min_conn_min,
        weights=greedy_weights,
        candidate_top=80,
        top_n=5
    )

    # Monte Carlo (price + expected time + risk)
    mc_weights = {"price": 1.0, "travel": 2.0, "risk": 5.0}
    mc_routes = find_routes_montecarlo(
        graph, origin, dest,
        max_connections=max_connections,
        min_conn_min=min_conn_min,
        weights=mc_weights,
        candidate_top=60,
        top_n=5,
        n_sims=200  # hızlı test için; finalde 200-500 daha iyi
    )

    # Print route results
    print_routes("BFS", bfs_routes)
    print_routes("RANDOM", rnd_routes)
    print_routes("GREEDY", greedy_routes)
    print_routes("MONTE CARLO", mc_routes)

    # ====================
    # BENCHMARK REPORT
    # ====================
    airports = list_airports(graph)
    scenarios = generate_scenarios(airports, n=20)  # istersen 50 yap
    all_results = run_benchmark(graph, scenarios, max_connections, min_conn_min)
    print_report(all_results)


if __name__ == "__main__":
    main()
import time
import random
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from src.data_loader import load_flights_csv
from src.graph_model import FlightGraph
from src.simulation import list_airports

from src.algorithms.random_agent import find_routes_random
from src.algorithms.bfs_agent import find_routes_bfs
from src.algorithms.greedy_agent import find_routes_greedy
from src.algorithms.montecarlo_agent import find_routes_montecarlo

st.set_page_config(page_title="Benchmark", layout="wide")
st.title("📊 Benchmark (Algorithm Comparison)")

flights_path = st.session_state.get("flights_path", "data/flights.csv")
df = load_flights_csv(flights_path)
graph = FlightGraph(df)
airports = list_airports(graph)

with st.sidebar:
    st.header("Benchmark Settings")
    n_scenarios = st.slider("scenarios", 5, 200, 20, 5)
    max_conn = st.slider("max_connections", 0, 3, 2)
    min_conn = st.slider("min_connection (min)", 0, 180, 45)

    mc_sims = st.slider("MC n_sims", 10, 300, 50, 10)

    st.header("Weights")
    greedy_w = {
        "price": st.slider("G price", 0.0, 10.0, 5.0, 0.5),
        "travel": st.slider("G travel", 0.0, 10.0, 2.0, 0.5),
        "layover": st.slider("G layover", 0.0, 10.0, 1.0, 0.5),
        "connections": st.slider("G conn", 0.0, 10.0, 1.0, 0.5),
    }
    mc_w = {
        "price": st.slider("MC price", 0.0, 10.0, 1.0, 0.5),
        "travel": st.slider("MC travel", 0.0, 10.0, 2.0, 0.5),
        "risk": st.slider("MC risk", 0.0, 10.0, 5.0, 0.5),
    }

def sample_scenarios():
    pairs = set()
    while len(pairs) < n_scenarios:
        o = random.choice(airports)
        d = random.choice(airports)
        if o != d:
            pairs.add((o, d))
    return list(pairs)

def best_metrics(routes):
    if not routes:
        return None
    r = routes[0]
    return {
        "price": float(r.total_price),
        "travel_min": float(r.total_travel_minutes),
        "layover_min": float(r.total_layover_minutes()),
        "connections": int(r.connections)
    }

run = st.button("Run Benchmark", type="primary")
if run:
    scenarios = sample_scenarios()
    rows = []

    for (o, d) in scenarios:
        # RANDOM
        t0 = time.perf_counter()
        r_routes = find_routes_random(graph, o, d, max_conn, min_conn, attempts=1500, top_n=5)
        rt = (time.perf_counter() - t0) * 1000
        bm = best_metrics(r_routes)
        rows.append({"algo":"random","origin":o,"dest":d,"found":bm is not None,"runtime_ms":rt, **(bm or {})})

        # BFS
        t0 = time.perf_counter()
        b_routes = find_routes_bfs(graph, o, d, max_conn, min_conn, top_n=50)
        rt = (time.perf_counter() - t0) * 1000
        bm = best_metrics(b_routes)
        rows.append({"algo":"bfs","origin":o,"dest":d,"found":bm is not None,"runtime_ms":rt, **(bm or {})})

        # GREEDY
        t0 = time.perf_counter()
        g_routes = find_routes_greedy(graph, o, d, max_conn, min_conn, greedy_w, candidate_top=80, top_n=5)
        rt = (time.perf_counter() - t0) * 1000
        bm = best_metrics(g_routes)
        rows.append({"algo":"greedy","origin":o,"dest":d,"found":bm is not None,"runtime_ms":rt, **(bm or {})})

        # MC
        t0 = time.perf_counter()
        m_routes = find_routes_montecarlo(graph, o, d, max_conn, min_conn, mc_w, candidate_top=60, top_n=5, n_sims=mc_sims)
        rt = (time.perf_counter() - t0) * 1000
        bm = best_metrics(m_routes)
        rows.append({"algo":"montecarlo","origin":o,"dest":d,"found":bm is not None,"runtime_ms":rt, **(bm or {})})

    df_res = pd.DataFrame(rows)

    st.subheader("Raw Results")
    st.dataframe(df_res, use_container_width=True)

    st.subheader("Summary by Algorithm")
    summary = (
        df_res.groupby("algo")
        .agg(
            scenarios=("origin","count"),
            success_rate=("found","mean"),
            avg_price=("price","mean"),
            avg_travel_min=("travel_min","mean"),
            avg_layover_min=("layover_min","mean"),
            avg_conn=("connections","mean"),
            avg_runtime_ms=("runtime_ms","mean"),
        )
        .reset_index()
    )
    st.dataframe(summary, use_container_width=True)

    # simple plot
    fig = plt.figure(figsize=(7,4))
    plt.bar(summary["algo"], summary["avg_runtime_ms"])
    plt.title("Average Runtime (ms)")
    plt.xlabel("Algorithm")
    plt.ylabel("ms")
    st.pyplot(fig, clear_figure=True)
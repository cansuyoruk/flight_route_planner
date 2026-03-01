import time
import streamlit as st
import pandas as pd

from src.data_loader import load_flights_csv
from src.graph_model import FlightGraph
from src.simulation import list_airports

from src.algorithms.bfs_agent import find_routes_bfs
from src.algorithms.random_agent import find_routes_random
from src.algorithms.greedy_agent import find_routes_greedy
from src.algorithms.montecarlo_agent import find_routes_montecarlo


st.set_page_config(page_title="Route Planner", layout="wide")
st.title("🧠 Route Planner")

@st.cache_data
def load_data(flights_path: str):
    df = load_flights_csv(flights_path)
    return df

@st.cache_resource
def build_graph(df: pd.DataFrame):
    return FlightGraph(df)

def routes_to_df(routes):
    rows = []
    for i, r in enumerate(routes, 1):
        rows.append({
            "rank": i,
            "route": r.path_str(),
            "price": float(r.total_price),
            "travel_min": float(r.total_travel_minutes),
            "layover_min": float(r.total_layover_minutes()),
            "connections": int(r.connections),
            "flights": ", ".join(f.flight_no for f in r.flights),
        })
    return pd.DataFrame(rows)

with st.sidebar:
    st.header("Dataset")
    flights_path = st.text_input("flights.csv path", "data/flights.csv")
    st.caption("CSV: flight_no, origin_airport, destination_airport, departure_datetime, arrival_datetime, price")

    st.header("Query")
    df = load_data(flights_path)
    graph = build_graph(df)
    airports = list_airports(graph)

    origin = st.selectbox("Origin", airports, index=airports.index("IST") if "IST" in airports else 0)
    dest = st.selectbox("Destination", airports, index=airports.index("ADA") if "ADA" in airports else min(1, len(airports)-1))

    max_conn = st.slider("Max connections", 0, 3, 2)
    min_conn_min = st.slider("Min connection (min)", 0, 180, 45)

    st.header("Algorithm")
    algo = st.selectbox("Method", ["random", "bfs", "greedy", "montecarlo"], index=2)
    top_n = st.slider("Top-N", 1, 20, 5)

    st.header("Weights")
    w_price = st.slider("price", 0.0, 10.0, 5.0, 0.5)
    w_travel = st.slider("travel", 0.0, 10.0, 2.0, 0.5)
    w_layover = st.slider("layover", 0.0, 10.0, 1.0, 0.5)
    w_connections = st.slider("connections", 0.0, 10.0, 1.0, 0.5)
    w_risk = st.slider("risk (MC)", 0.0, 10.0, 5.0, 0.5)

    st.header("Monte Carlo")
    mc_sims = st.slider("n_sims", 10, 800, 50, 10)
    delay_mean = st.slider("delay_mean (min)", 0.0, 60.0, 10.0, 1.0)
    delay_std = st.slider("delay_std (min)", 0.0, 60.0, 15.0, 1.0)

run = st.button("🚀 Generate Routes", type="primary")

if run:
    if origin == dest:
        st.error("Origin ve destination farklı olmalı.")
        st.stop()

    t0 = time.perf_counter()

    if algo == "random":
        routes = find_routes_random(graph, origin, dest, max_conn, min_conn_min, attempts=2500, top_n=top_n)
    elif algo == "bfs":
        routes = find_routes_bfs(graph, origin, dest, max_conn, min_conn_min, top_n=max(50, top_n))
    elif algo == "greedy":
        weights = {"price": w_price, "travel": w_travel, "layover": w_layover, "connections": w_connections}
        routes = find_routes_greedy(graph, origin, dest, max_conn, min_conn_min, weights, candidate_top=80, top_n=top_n)
    else:
        weights = {"price": w_price, "travel": w_travel, "risk": w_risk}
        routes = find_routes_montecarlo(
            graph, origin, dest, max_conn, min_conn_min,
            weights=weights, candidate_top=60, top_n=top_n,
            n_sims=mc_sims, delay_mean_min=delay_mean, delay_std_min=delay_std
        )

    dt_ms = (time.perf_counter() - t0) * 1000.0

    st.subheader(f"Results ({algo})")
    st.caption(f"Computed in {dt_ms:.1f} ms")

    if not routes:
        st.warning("No feasible routes found.")
        st.stop()

    out_df = routes_to_df(routes[:top_n])
    st.dataframe(out_df, use_container_width=True)

    # Detail viewer
    st.subheader("Route Detail")
    sel_rank = st.number_input("Select rank", min_value=1, max_value=int(out_df["rank"].max()), value=1, step=1)
    r = routes[int(sel_rank) - 1]
    st.write(f"**Route:** {r.path_str()}")
    st.write(f"- Total price: `{r.total_price:.2f}`")
    st.write(f"- Travel min: `{r.total_travel_minutes:.1f}`")
    st.write(f"- Layover min: `{r.total_layover_minutes():.1f}`")
    st.write(f"- Connections: `{r.connections}`")

    st.write("**Segments**")
    for f in r.flights:
        st.write(f"- `{f.flight_no}`: {f.origin} → {f.dest} | dep={f.dep} | arr={f.arr} | price={f.price:.2f}")

    # share selection with other pages
    st.session_state["selected_route"] = r
    st.session_state["selected_origin"] = origin
    st.session_state["selected_dest"] = dest
    st.session_state["flights_path"] = flights_path
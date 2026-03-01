import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

from src.data_loader import load_flights_csv

st.set_page_config(page_title="Network Graph", layout="wide")
st.title("🕸️ Network Graph (Airports as nodes, flights as directed edges)")

flights_path = st.session_state.get("flights_path", "data/flights.csv")
df = load_flights_csv(flights_path)

G = nx.DiGraph()
for _, r in df.iterrows():
    o = str(r["origin_airport"])
    d = str(r["destination_airport"])
    if G.has_edge(o, d):
        G[o][d]["count"] += 1
    else:
        G.add_edge(o, d, count=1)

pos = nx.spring_layout(G, seed=42)

fig = plt.figure(figsize=(9, 6))
nx.draw_networkx_nodes(G, pos, node_size=1200)
nx.draw_networkx_labels(G, pos, font_size=10)
nx.draw_networkx_edges(G, pos, arrows=True, arrowstyle="-|>", arrowsize=18, width=1.6)

edge_labels = {(u, v): f"x{G[u][v]['count']}" for u, v in G.edges()}
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=9)

plt.title("Flight Network Graph")
plt.axis("off")
st.pyplot(fig, clear_figure=True)
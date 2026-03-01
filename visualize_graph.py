import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

CSV_PATH = "data/flights.csv"

def main():
    df = pd.read_csv(CSV_PATH)

    # Graph: airports are nodes, flights are directed edges
    G = nx.DiGraph()

    # Add edges (aggregate multiple flights between same airports)
    for _, r in df.iterrows():
        o = str(r["origin_airport"])
        d = str(r["destination_airport"])

        # If multiple flights on same route, count them
        if G.has_edge(o, d):
            G[o][d]["count"] += 1
        else:
            G.add_edge(o, d, count=1)

    # Layout (spring gives nice looking network)
    pos = nx.spring_layout(G, seed=42)

    # Draw nodes + labels
    plt.figure(figsize=(10, 7))
    nx.draw_networkx_nodes(G, pos, node_size=1200)
    nx.draw_networkx_labels(G, pos, font_size=10)

    # Draw edges with arrows
    nx.draw_networkx_edges(G, pos, arrows=True, arrowstyle="-|>", arrowsize=20, width=1.5)

    # Edge labels = count of flights
    edge_labels = {(u, v): f"x{G[u][v]['count']}" for u, v in G.edges()}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=9)

    plt.title("Flight Network Graph (Airports as nodes, flights as directed edges)")
    plt.axis("off")
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

from src.data_loader import load_flights_csv

st.set_page_config(page_title="Map View", layout="wide")
st.title("🗺️ Map View (Dark Map)")

# Paths
flights_path = st.session_state.get("flights_path", "data/flights.csv")
airports_path = st.text_input("airports.csv path", "data/airports.csv")

# Load data
try:
    flights = load_flights_csv(flights_path)
except Exception as e:
    st.error(f"Cannot load flights: {e}")
    st.stop()

try:
    airports = pd.read_csv(airports_path).set_index("airport")
    for col in ["lat", "lon"]:
        if col not in airports.columns:
            raise ValueError("airports.csv must have columns: airport,lat,lon")
except Exception as e:
    st.error(f"Cannot load airports: {e}")
    st.stop()

# Dark map
m = folium.Map(
    location=[39.0, 35.0],
    zoom_start=6,
    tiles="CartoDB dark_matter"
)

# Airport markers
for code, row in airports.iterrows():
    folium.CircleMarker(
        location=[float(row["lat"]), float(row["lon"])],
        radius=7,
        popup=code,
        color="#2E86FF",
        fill=True,
        fill_opacity=0.85,
    ).add_to(m)

# All flight edges (neon turquoise)
for _, r in flights.iterrows():
    o, d = r["origin_airport"], r["destination_airport"]
    if o not in airports.index or d not in airports.index:
        continue

    o_lat, o_lon = airports.loc[o, ["lat", "lon"]]
    d_lat, d_lon = airports.loc[d, ["lat", "lon"]]

    folium.PolyLine(
        locations=[[float(o_lat), float(o_lon)], [float(d_lat), float(d_lon)]],
        tooltip=f"{r['flight_no']} | {o}->{d} | price={r['price']}",
        color="#00FFCC",   # neon turquoise
        weight=3,
        opacity=0.70,
    ).add_to(m)

# Highlight selected route (from Route Planner)
sel = st.session_state.get("selected_route", None)
if sel is not None:
    coords = []
    ok = True

    for f in sel.flights:
        if f.origin not in airports.index or f.dest not in airports.index:
            ok = False
            break

        o_lat, o_lon = airports.loc[f.origin, ["lat", "lon"]]
        d_lat, d_lon = airports.loc[f.dest, ["lat", "lon"]]

        coords.append([float(o_lat), float(o_lon)])
        coords.append([float(d_lat), float(d_lon)])

    if ok and coords:
        # Remove consecutive duplicates
        clean = [coords[0]]
        for c in coords[1:]:
            if c != clean[-1]:
                clean.append(c)

        folium.PolyLine(
            clean,
            color="#FFFF00",   # neon yellow
            weight=7,
            opacity=0.95,
            tooltip="SELECTED ROUTE"
        ).add_to(m)

        st.success(f"Selected route highlighted: {sel.path_str()}")
    else:
        st.warning("Selected route cannot be highlighted (missing coords).")
else:
    st.info("No selected route yet. Go to Route Planner and generate/select a route.")

# Render map
st_folium(m, width=1100, height=620)
st.caption("Neon turkuaz: tüm uçuşlar | Neon sarı: seçili rota (Route Planner’dan).")
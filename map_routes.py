import pandas as pd
import folium

FLIGHTS = "data/flights.csv"
AIRPORTS = "data/airports.csv"

def main():
    flights = pd.read_csv(FLIGHTS)
    airports = pd.read_csv(AIRPORTS).set_index("airport")

    m = folium.Map(location=[39.0, 35.0], zoom_start=6)

    # Airport nodes
    for code, row in airports.iterrows():
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=7,
            popup=code,
            color="blue",
            fill=True,
            fill_opacity=0.7
        ).add_to(m)

    # Flight edges
    for _, r in flights.iterrows():
        o = r["origin_airport"]
        d = r["destination_airport"]

        if o not in airports.index or d not in airports.index:
            continue

        o_lat, o_lon = airports.loc[o, ["lat", "lon"]]
        d_lat, d_lon = airports.loc[d, ["lat", "lon"]]

        folium.PolyLine(
            locations=[[o_lat, o_lon], [d_lat, d_lon]],
            tooltip=f"{r['flight_no']} | {o}->{d} | price={r['price']}",
            color="red",
            weight=2,
            opacity=0.8
        ).add_to(m)

    m.save("flight_map.html")
    print("Saved: flight_map.html")

if __name__ == "__main__":
    main()
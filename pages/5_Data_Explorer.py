import streamlit as st
import pandas as pd

st.set_page_config(page_title="Data Explorer", layout="wide")
st.title("📁 Data Explorer")

flights_path = st.text_input("flights.csv path", st.session_state.get("flights_path", "data/flights.csv"))
airports_path = st.text_input("airports.csv path", "data/airports.csv")

col1, col2 = st.columns(2)

with col1:
    st.subheader("flights.csv")
    try:
        flights = pd.read_csv(flights_path)
        st.dataframe(flights, use_container_width=True)
        st.caption(f"Rows: {len(flights)}")
    except Exception as e:
        st.error(str(e))

with col2:
    st.subheader("airports.csv")
    try:
        airports = pd.read_csv(airports_path)
        st.dataframe(airports, use_container_width=True)
        st.caption(f"Rows: {len(airports)}")
    except Exception as e:
        st.error(str(e))
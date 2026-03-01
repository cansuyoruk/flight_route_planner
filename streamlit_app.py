import streamlit as st

st.set_page_config(page_title="Flight Decision Support", layout="wide")

st.title("✈️ Flight Decision Support Dashboard")
st.write(
    """
Bu dashboard projenin demo arayüzüdür.

Sol menüden sayfalar:
- **Route Planner:** Algoritma seç + ağırlıklar + Top-N rota
- **Map View:** Harita üzerinde uçuşlar ve seçili rota highlight
- **Network Graph:** Airport graph görselleştirmesi
- **Benchmark:** Algoritma karşılaştırma tablosu + grafik
- **Data Explorer:** flights.csv / airports.csv inceleme
"""
)

st.info("Başlamak için sol menüden **Route Planner** sayfasına geç.")
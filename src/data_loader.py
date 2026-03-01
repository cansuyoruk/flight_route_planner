import pandas as pd

REQUIRED_COLS = [
    "flight_no",
    "origin_airport",
    "destination_airport",
    "departure_datetime",
    "arrival_datetime",
    "price",
]

def load_flights_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"CSV missing columns: {missing}")

    df["departure_datetime"] = pd.to_datetime(df["departure_datetime"])
    df["arrival_datetime"] = pd.to_datetime(df["arrival_datetime"])
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df.dropna(subset=["price"]).copy()

    df = df[df["arrival_datetime"] >= df["departure_datetime"]].copy()

    df["duration_minutes"] = (df["arrival_datetime"] - df["departure_datetime"]).dt.total_seconds() / 60.0
    return df
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict
import pandas as pd

@dataclass(frozen=True)
class Flight:
    flight_no: str
    origin: str
    dest: str
    dep: pd.Timestamp
    arr: pd.Timestamp
    price: float
    duration_min: float

    @staticmethod
    def from_row(r: pd.Series) -> "Flight":
        return Flight(
            flight_no=str(r["flight_no"]),
            origin=str(r["origin_airport"]),
            dest=str(r["destination_airport"]),
            dep=pd.Timestamp(r["departure_datetime"]),
            arr=pd.Timestamp(r["arrival_datetime"]),
            price=float(r["price"]),
            duration_min=float(r["duration_minutes"]),
        )

@dataclass
class Route:
    flights: List[Flight]

    @property
    def connections(self) -> int:
        return max(0, len(self.flights) - 1)

    @property
    def total_price(self) -> float:
        return sum(f.price for f in self.flights)

    @property
    def total_travel_minutes(self) -> float:
        return (self.flights[-1].arr - self.flights[0].dep).total_seconds() / 60.0

    def total_layover_minutes(self) -> float:
        if len(self.flights) <= 1:
            return 0.0
        lay = 0.0
        for i in range(len(self.flights) - 1):
            lay += (self.flights[i+1].dep - self.flights[i].arr).total_seconds() / 60.0
        return lay

    def path_str(self) -> str:
        airports = [self.flights[0].origin] + [f.dest for f in self.flights]
        return " → ".join(airports)

class FlightGraph:
    def __init__(self, df: pd.DataFrame):
        self.flights = [Flight.from_row(r) for _, r in df.iterrows()]
        self.by_origin: Dict[str, List[Flight]] = {}
        for f in self.flights:
            self.by_origin.setdefault(f.origin, []).append(f)
        for k in self.by_origin:
            self.by_origin[k].sort(key=lambda x: x.dep)

    def next_flights(self, origin: str) -> List[Flight]:
        return self.by_origin.get(origin, [])

    @staticmethod
    def can_connect(prev: Flight, nxt: Flight, min_conn_min: int) -> bool:
        return nxt.dep >= prev.arr + pd.Timedelta(minutes=min_conn_min)

    def feasible_next(self, prev: Flight, min_conn_min: int) -> List[Flight]:
        threshold = prev.arr + pd.Timedelta(minutes=min_conn_min)
        return [f for f in self.next_flights(prev.dest) if f.dep >= threshold]
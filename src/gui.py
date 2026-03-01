from __future__ import annotations

import os
import time
import tkinter as tk
from tkinter import ttk, messagebox

from src.data_loader import load_flights_csv
from src.graph_model import FlightGraph, Route
from src.algorithms.bfs_agent import find_routes_bfs
from src.algorithms.random_agent import find_routes_random
from src.algorithms.greedy_agent import find_routes_greedy
from src.algorithms.montecarlo_agent import find_routes_montecarlo
from src.simulation import list_airports


def _fmt_min(x: float) -> str:
    return f"{x:.1f}"


def _fmt_money(x: float) -> str:
    return f"{x:.2f}"


class ProFlightGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI-Assisted Multi-Connection Flight Planner")
        self.geometry("1100x650")
        self.minsize(980, 600)

        # State
        self.csv_path = tk.StringVar(value="data/flights.csv")

        self.origin = tk.StringVar(value="IST")
        self.dest = tk.StringVar(value="ADA")

        self.max_connections = tk.IntVar(value=2)
        self.min_conn_min = tk.IntVar(value=45)

        self.algorithm = tk.StringVar(value="greedy")
        self.top_n = tk.IntVar(value=5)

        # Weights
        self.w_price = tk.DoubleVar(value=5.0)
        self.w_travel = tk.DoubleVar(value=2.0)
        self.w_layover = tk.DoubleVar(value=1.0)
        self.w_connections = tk.DoubleVar(value=1.0)
        self.w_risk = tk.DoubleVar(value=5.0)

        # Monte Carlo params
        self.mc_sims = tk.IntVar(value=50)
        self.mc_delay_mean = tk.DoubleVar(value=10.0)
        self.mc_delay_std = tk.DoubleVar(value=15.0)

        # Runtime
        self.graph: FlightGraph | None = None
        self.airports: list[str] = []
        self.current_routes: list[Route] = []
        self.last_runtime_ms: float | None = None

        self._build_style()
        self._build_layout()
        self.safe_load_data(startup=True)

    # ---------------- UI BUILD ----------------
    def _build_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("aqua")
        except Exception:
            pass

        style.configure("Header.TLabel", font=("Helvetica", 14, "bold"))
        style.configure("Small.TLabel", font=("Helvetica", 10))
        style.configure("Treeview.Heading", font=("Helvetica", 11, "bold"))
        style.configure("TButton", padding=6)

    def _build_layout(self):
        root = ttk.Frame(self, padding=10)
        root.pack(fill="both", expand=True)

        root.columnconfigure(0, weight=0)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(0, weight=1)

        left = ttk.Frame(root)
        left.grid(row=0, column=0, sticky="nsw", padx=(0, 10))

        right = ttk.Frame(root)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        # ---------- LEFT: Tabs ----------
        ttk.Label(left, text="Controls", style="Header.TLabel").pack(anchor="w", pady=(0, 8))

        nb = ttk.Notebook(left)
        nb.pack(fill="both", expand=True)

        tab_query = ttk.Frame(nb, padding=10)
        tab_weights = ttk.Frame(nb, padding=10)
        tab_mc = ttk.Frame(nb, padding=10)
        tab_export = ttk.Frame(nb, padding=10)

        nb.add(tab_query, text="Query")
        nb.add(tab_weights, text="Weights")
        nb.add(tab_mc, text="Monte Carlo")
        nb.add(tab_export, text="Export")

        # --- Dataset + Query tab
        ds = ttk.LabelFrame(tab_query, text="Dataset", padding=10)
        ds.pack(fill="x", pady=(0, 10))

        ttk.Label(ds, text="CSV Path").grid(row=0, column=0, sticky="w")
        ttk.Entry(ds, textvariable=self.csv_path, width=34).grid(row=1, column=0, sticky="we", pady=(2, 6))
        ttk.Button(ds, text="Load Data", command=self.safe_load_data).grid(row=2, column=0, sticky="we")

        q = ttk.LabelFrame(tab_query, text="Route Search", padding=10)
        q.pack(fill="x")

        ttk.Label(q, text="Origin").grid(row=0, column=0, sticky="w")
        self.origin_cb = ttk.Combobox(q, textvariable=self.origin, width=12, state="readonly")
        self.origin_cb.grid(row=1, column=0, sticky="w", pady=(2, 8))

        ttk.Label(q, text="Destination").grid(row=2, column=0, sticky="w")
        self.dest_cb = ttk.Combobox(q, textvariable=self.dest, width=12, state="readonly")
        self.dest_cb.grid(row=3, column=0, sticky="w", pady=(2, 8))

        row = ttk.Frame(q)
        row.grid(row=4, column=0, sticky="we", pady=(2, 0))
        ttk.Label(row, text="Max Connections").grid(row=0, column=0, sticky="w")
        ttk.Spinbox(row, from_=0, to=3, textvariable=self.max_connections, width=5).grid(row=0, column=1, sticky="e", padx=(8, 0))

        row2 = ttk.Frame(q)
        row2.grid(row=5, column=0, sticky="we", pady=(6, 0))
        ttk.Label(row2, text="Min Connection (min)").grid(row=0, column=0, sticky="w")
        ttk.Spinbox(row2, from_=0, to=180, textvariable=self.min_conn_min, width=5).grid(row=0, column=1, sticky="e", padx=(8, 0))

        alg = ttk.LabelFrame(tab_query, text="Algorithm", padding=10)
        alg.pack(fill="x", pady=(10, 0))

        ttk.Label(alg, text="Method").grid(row=0, column=0, sticky="w")
        ttk.Combobox(
            alg,
            textvariable=self.algorithm,
            state="readonly",
            values=["random", "bfs", "greedy", "montecarlo"],
            width=16,
        ).grid(row=1, column=0, sticky="w", pady=(2, 8))

        row3 = ttk.Frame(alg)
        row3.grid(row=2, column=0, sticky="we")
        ttk.Label(row3, text="Top-N").grid(row=0, column=0, sticky="w")
        ttk.Spinbox(row3, from_=1, to=20, textvariable=self.top_n, width=5).grid(row=0, column=1, sticky="e", padx=(8, 0))

        self.btn_generate = ttk.Button(alg, text="Generate Routes", command=self.generate_routes)
        self.btn_generate.grid(row=3, column=0, sticky="we", pady=(10, 0))

        # --- Weights tab
        wbox = ttk.LabelFrame(tab_weights, text="Scoring Weights", padding=10)
        wbox.pack(fill="x")

        self._kv_row(wbox, "price", self.w_price, 0)
        self._kv_row(wbox, "travel", self.w_travel, 1)
        self._kv_row(wbox, "layover", self.w_layover, 2)
        self._kv_row(wbox, "connections", self.w_connections, 3)
        self._kv_row(wbox, "risk (MC)", self.w_risk, 4)

        ttk.Label(
            tab_weights,
            text="Tip: Greedy uses price/travel/layover/connections.\nMonte Carlo uses price/travel/risk.",
            style="Small.TLabel",
        ).pack(anchor="w", pady=(10, 0))

        # --- Monte Carlo tab
        mcbox = ttk.LabelFrame(tab_mc, text="Delay Model", padding=10)
        mcbox.pack(fill="x")

        self._kv_row(mcbox, "n_sims", self.mc_sims, 0, width=10)
        self._kv_row(mcbox, "delay_mean (min)", self.mc_delay_mean, 1, width=10)
        self._kv_row(mcbox, "delay_std (min)", self.mc_delay_std, 2, width=10)

        ttk.Label(
            tab_mc,
            text="Higher n_sims = more stable but slower.\nTry 50 for demo, 200-500 for final.",
            style="Small.TLabel",
        ).pack(anchor="w", pady=(10, 0))

        # --- Export tab
        exbox = ttk.LabelFrame(tab_export, text="Export", padding=10)
        exbox.pack(fill="x")
        ttk.Button(exbox, text="Export Selected Route", command=self.export_selected).pack(fill="x")

        ttk.Label(
            tab_export,
            text="Exports to: results/selected_route.txt",
            style="Small.TLabel",
        ).pack(anchor="w", pady=(10, 0))

        # ---------- RIGHT: Results ----------
        ttk.Label(right, text="Results", style="Header.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 8))

        table_frame = ttk.Frame(right)
        table_frame.grid(row=1, column=0, sticky="nsew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        cols = ("rank", "path", "price", "travel", "layover", "conn")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=12)
        self.tree.grid(row=0, column=0, sticky="nsew")

        self.tree.heading("rank", text="#")
        self.tree.heading("path", text="Route")
        self.tree.heading("price", text="Price")
        self.tree.heading("travel", text="Travel (min)")
        self.tree.heading("layover", text="Layover (min)")
        self.tree.heading("conn", text="Conn")

        self.tree.column("rank", width=40, anchor="center")
        self.tree.column("path", width=440, anchor="w")
        self.tree.column("price", width=100, anchor="e")
        self.tree.column("travel", width=110, anchor="e")
        self.tree.column("layover", width=120, anchor="e")
        self.tree.column("conn", width=70, anchor="center")

        sb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=sb.set)
        sb.grid(row=0, column=1, sticky="ns")

        self.tree.bind("<<TreeviewSelect>>", self.on_select_route)

        detail = ttk.LabelFrame(right, text="Route Details", padding=10)
        detail.grid(row=2, column=0, sticky="nsew", pady=(10, 0))
        detail.columnconfigure(0, weight=1)

        self.detail_text = tk.Text(detail, height=9)
        self.detail_text.grid(row=0, column=0, sticky="nsew")

        self.status = tk.StringVar(value="Ready.")
        ttk.Label(right, textvariable=self.status, style="Small.TLabel").grid(row=3, column=0, sticky="we", pady=(8, 0))

    def _kv_row(self, parent, label: str, var, r: int, width: int = 8):
        row = ttk.Frame(parent)
        row.grid(row=r, column=0, sticky="we", pady=2)
        ttk.Label(row, text=label).grid(row=0, column=0, sticky="w")
        ttk.Entry(row, textvariable=var, width=width).grid(row=0, column=1, sticky="e", padx=(8, 0))

    # ---------------- DATA ----------------
    def safe_load_data(self, startup: bool = False):
        try:
            self.load_data()
        except Exception as e:
            if startup:
                self.status.set("Ready. (Set CSV path and click Load Data)")
            else:
                messagebox.showerror("Load Error", str(e))
                self.status.set("Load failed.")

    def load_data(self):
        path = self.csv_path.get().strip()
        if not path:
            raise ValueError("CSV path is empty.")
        if not os.path.exists(path):
            raise FileNotFoundError(f"CSV not found: {path}")

        df = load_flights_csv(path)
        self.graph = FlightGraph(df)
        self.airports = list_airports(self.graph)

        self.origin_cb["values"] = self.airports
        self.dest_cb["values"] = self.airports

        if self.airports:
            if self.origin.get() not in self.airports:
                self.origin.set(self.airports[0])
            if self.dest.get() not in self.airports:
                self.dest.set(self.airports[-1])

        self.status.set(f"Loaded {len(self.graph.flights)} flights, {len(self.airports)} airports.")

    # ---------------- ROUTES ----------------
    def _validate_inputs(self):
        if self.graph is None:
            raise ValueError("Load data first.")
        o = self.origin.get().strip()
        d = self.dest.get().strip()
        if not o or not d:
            raise ValueError("Origin/Destination required.")
        if o == d:
            raise ValueError("Origin and Destination must be different.")
        if int(self.top_n.get()) < 1:
            raise ValueError("Top-N must be >= 1.")

    def generate_routes(self):
        try:
            self._validate_inputs()
        except Exception as e:
            messagebox.showerror("Input Error", str(e))
            return

        self.btn_generate.configure(state="disabled")
        self.status.set("Computing routes...")
        self.update_idletasks()

        t0 = time.perf_counter()

        o = self.origin.get().strip()
        d = self.dest.get().strip()
        max_conn = int(self.max_connections.get())
        min_conn = int(self.min_conn_min.get())
        top_n = int(self.top_n.get())
        algo = self.algorithm.get()

        try:
            if algo == "random":
                routes = find_routes_random(self.graph, o, d, max_conn, min_conn, attempts=2500, top_n=top_n)
            elif algo == "bfs":
                routes = find_routes_bfs(self.graph, o, d, max_conn, min_conn, top_n=max(50, top_n))
            elif algo == "greedy":
                weights = {
                    "price": float(self.w_price.get()),
                    "travel": float(self.w_travel.get()),
                    "layover": float(self.w_layover.get()),
                    "connections": float(self.w_connections.get()),
                }
                routes = find_routes_greedy(self.graph, o, d, max_conn, min_conn, weights, candidate_top=80, top_n=top_n)
            else:
                weights = {
                    "price": float(self.w_price.get()),
                    "travel": float(self.w_travel.get()),
                    "risk": float(self.w_risk.get()),
                }
                routes = find_routes_montecarlo(
                    self.graph, o, d, max_conn, min_conn,
                    weights=weights,
                    candidate_top=60,
                    top_n=top_n,
                    n_sims=int(self.mc_sims.get()),
                    delay_mean_min=float(self.mc_delay_mean.get()),
                    delay_std_min=float(self.mc_delay_std.get()),
                )

            self.last_runtime_ms = (time.perf_counter() - t0) * 1000.0
            self.current_routes = routes
            self._render_routes()

            if not routes:
                self.status.set(f"No feasible routes found. ({algo}) time={self.last_runtime_ms:.1f} ms")
            else:
                self.status.set(f"Found {len(routes)} routes. ({algo}) time={self.last_runtime_ms:.1f} ms")

        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.status.set("Error while computing routes.")
        finally:
            self.btn_generate.configure(state="normal")

    def _render_routes(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.detail_text.delete("1.0", tk.END)

        routes = self.current_routes[: int(self.top_n.get())]
        for i, r in enumerate(routes, 1):
            self.tree.insert(
                "",
                "end",
                iid=str(i - 1),
                values=(
                    i,
                    r.path_str(),
                    _fmt_money(r.total_price),
                    _fmt_min(r.total_travel_minutes),
                    _fmt_min(r.total_layover_minutes()),
                    r.connections,
                ),
            )

        if routes:
            self.tree.selection_set("0")
            self.on_select_route()

    def on_select_route(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        if idx < 0 or idx >= len(self.current_routes):
            return
        self._render_detail(self.current_routes[idx])

    def _render_detail(self, r: Route):
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.insert(tk.END, f"Route: {r.path_str()}\n")
        self.detail_text.insert(tk.END, f"Total price: {_fmt_money(r.total_price)}\n")
        self.detail_text.insert(tk.END, f"Total travel (min): {_fmt_min(r.total_travel_minutes)}\n")
        self.detail_text.insert(tk.END, f"Total layover (min): {_fmt_min(r.total_layover_minutes())}\n")
        self.detail_text.insert(tk.END, f"Connections: {r.connections}\n\n")
        self.detail_text.insert(tk.END, "Segments:\n")
        for f in r.flights:
            self.detail_text.insert(
                tk.END,
                f"  - {f.flight_no}: {f.origin}->{f.dest}  dep={f.dep}  arr={f.arr}  price={_fmt_money(f.price)}\n"
            )

    def export_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Export", "Select a route first.")
            return
        idx = int(sel[0])
        if idx < 0 or idx >= len(self.current_routes):
            messagebox.showerror("Export", "Invalid selection.")
            return

        r = self.current_routes[idx]
        os.makedirs("results", exist_ok=True)
        out_path = os.path.join("results", "selected_route.txt")

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(f"Route: {r.path_str()}\n")
            f.write(f"Total price: {_fmt_money(r.total_price)}\n")
            f.write(f"Total travel (min): {_fmt_min(r.total_travel_minutes)}\n")
            f.write(f"Total layover (min): {_fmt_min(r.total_layover_minutes())}\n")
            f.write(f"Connections: {r.connections}\n\n")
            for fl in r.flights:
                f.write(f"{fl.flight_no}: {fl.origin}->{fl.dest} dep={fl.dep} arr={fl.arr} price={_fmt_money(fl.price)}\n")

        messagebox.showinfo("Export", f"Saved to {out_path}")
        self.status.set(f"Exported selected route to {out_path}")


def run_gui():
    app = ProFlightGUI()
    app.mainloop()
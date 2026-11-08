"""
compare_tableau_python.py — Task 3.10

Reads the Tableau Prep outputs (data/processed/*.hyper) and the Python outputs
(data/processed/2025/*.csv) and compares them row by row.

Run from the repo root (needs: pip install tableauhyperapi):
    python src/compare_tableau_python.py
"""

from pathlib import Path

import pandas as pd
from tableauhyperapi import Connection, HyperProcess, TableName, Telemetry

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
COLUMNS = [  # (Python column, Tableau column)
    ("bikes_total", "bikes_total"), ("is_missing", "is_missing"), ("is_outage", "is_outage"),
    ("is_zero", "is_zero"), ("is_outlier", "is_outlier"), ("is_weekend", "is_weekend"),
    ("is_holiday", "is_holiday"), ("is_rainy", "is_rainy"), ("temp_mean_c", "temp_mean_c"),
    ("precip_mm", "precipitation_mm"),
]


def read_hyper(path):
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper, Connection(hyper.endpoint, path) as con:
        table = TableName("Extract", "Extract")
        cols = [c.name.unescaped for c in con.catalog.get_table_definition(table).columns]
        return pd.DataFrame(con.execute_list_query(f"SELECT * FROM {table}"), columns=cols)


def as_number(s):
    return pd.to_numeric(s.astype(object).map(lambda v: int(v) if isinstance(v, bool) else v), errors="coerce").astype(float)


def main():
    tab_daily = read_hyper(PROCESSED / "bike_counts_daily_weather.hyper")
    tab_weekly = read_hyper(PROCESSED / "bike_counts_weekly_aggregated.hyper")
    py_daily = pd.read_csv(PROCESSED / "2025" / "model_table.csv", dtype={"site_id": str})
    py_weekly = pd.read_csv(PROCESSED / "2025" / "weekly_counts.csv")

    tab_daily["date"] = pd.to_datetime(tab_daily["date"].astype(str))
    py_daily["date"] = pd.to_datetime(py_daily["date"])
    both = py_daily.merge(tab_daily, on=["site_id", "date"], how="outer", suffixes=("_py", "_tab"), indicator=True)

    print(f"{'':32}{'Python':>12}{'Tableau':>12}")
    print(f"{'Daily rows':32}{len(py_daily):>12,}{len(tab_daily):>12,}")
    for flag in ["is_missing", "is_outage", "is_zero", "is_outlier"]:
        print(f"{flag:32}{int(py_daily[flag].sum()):>12,}{int(tab_daily[flag].astype(bool).sum()):>12,}")
    print(f"{'Weekly rows':32}{len(py_weekly):>12,}{len(tab_weekly):>12,}")
    print(f"{'Weekly total (sum of bikes)':32}{int(py_weekly['bikes_total'].sum()):>12,}{int(tab_weekly['bikes_total'].sum()):>12,}")

    print(f"\nRows only in one tool: {(both['_merge'] != 'both').sum()}")
    total = 0
    for py_col, tab_col in COLUMNS:
        a = as_number(both[py_col + "_py" if py_col + "_py" in both else py_col])
        b = as_number(both[tab_col + "_tab" if tab_col + "_tab" in both else tab_col])
        diff = int((~((a == b) | (a.isna() & b.isna()) | ((a - b).abs() < 1e-6))).sum())
        total += diff
        print(f"  {py_col:16} differences: {diff}")
    print("\nResult:", "Tableau = Python, 0 differences" if total == 0 else f"{total} differences")


if __name__ == "__main__":
    main()
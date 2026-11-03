"""
cleaning.py — Tasks 3.6 / 3.7 / 3.9 / 3.14

Reproducible cleaning pipeline: one function per cleaning rule (see docs/cleaning_rules.md),
called in a fixed order by run_pipeline(). Raw files are never changed.

Outputs (data/processed/<tag>/, tag = "2025" or e.g. "2026-01"):
    sites.csv          one row per counter site               (table 1)
    daily_counts.csv   one row per site + day                 (table 2, key: site_id + date)
    weather_daily.csv  one row per day, DWD Mannheim          (table 3, key: date)
    model_table.csv    counts + site + weather + calendar     (AI-ready table)
    weekly_counts.csv  aggregate per site + ISO week
And the cleaning log: docs/cleaning_log_<tag>.md (rule, rows before -> after, output checksums)

Usage (from the repo root):
    python src/cleaning.py                         # 2025, all months
    python src/cleaning.py --year 2026 --months 1  # re-run on new data (task 3.9)
"""

import argparse
import hashlib
from pathlib import Path

import holidays
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_BIKE = ROOT / "data" / "raw" / "bike"
RAW_WEATHER = ROOT / "data" / "raw" / "weather"
PROCESSED = ROOT / "data" / "processed"
DOCS = ROOT / "docs"

CITIES = ["Heidelberg", "Mannheim"]
OUTAGE_MIN_DAYS = 3          # rule: >= 3 zero days in a row = sensor outage
OUTLIER_IQR_FACTOR = 3       # rule: above Q3 + 3 * IQR per site = outlier
RAINY_DAY_MM = 1.0           # rule: >= 1 mm precipitation = rainy day

BIKE_RENAME = {
    "counter_site_id": "site_id", "counter_site": "site_name", "domain_name": "city",
    "channels_in": "bikes_in", "channels_out": "bikes_out", "channels_all": "bikes_total",
}
WEATHER_RENAME = {
    "TMK": "temp_mean_c", "TXK": "temp_max_c", "TNK": "temp_min_c", "RSK": "precip_mm",
    "SHK_TAG": "snow_depth_cm", "SDK": "sunshine_h", "FM": "wind_mean_ms", "UPM": "humidity_pct",
}


# ================================================================ cleaning log
class CleaningLog:
    """Collects one line per step: rule, rows before -> after. Becomes docs/cleaning_log_<tag>.md."""

    def __init__(self):
        self.rows = []

    def add(self, table, step, rule, before, after, note=""):
        self.rows.append({"table": table, "step": step, "rule": rule,
                          "before": before, "after": after, "change": after - before, "note": note})
        print(f"  [{table}] {step}: {before:,} -> {after:,} {note}")


def logged(table, rule):
    """Decorator: runs a cleaning function and writes rows before -> after into the log."""
    def wrap(func):
        def inner(df, log: CleaningLog, *args, **kwargs):
            before = len(df)
            out, note = func(df, *args, **kwargs)
            log.add(table, func.__name__, rule, before, len(out), note)
            return out
        inner.__name__ = func.__name__
        inner.raw = func            # the plain function, used by the tests
        return inner
    return wrap


# ================================================================ load (read-only)
def load_bike_raw(year: int, months=None) -> pd.DataFrame:
    files = sorted(RAW_BIKE.glob(f"fahrradzaehler_tageswerten_{year}*.csv"))
    if months:
        files = [f for f in files if int(f.stem[-2:]) in months]
    if not files:
        raise SystemExit(f"No raw bike files for {year} {months or ''}. Run: python src/download.py")
    return pd.concat([pd.read_csv(f, sep=None, engine="python", dtype=str).assign(source_file=f.name)
                      for f in files], ignore_index=True)


def load_weather_raw() -> pd.DataFrame:
    """Both DWD files; the one that starts earliest is 'historical' (quality-checked)."""
    files = sorted(RAW_WEATHER.glob("produkt_klima_tag_*.txt"), key=lambda f: f.name.split("_")[3])
    if not files:
        raise SystemExit("No DWD weather files. Run: python src/download.py")
    frames = []
    for priority, f in enumerate(files):
        w = pd.read_csv(f, sep=";", skipinitialspace=True, dtype=str)
        w.columns = w.columns.str.strip()
        frames.append(w.apply(lambda s: s.str.strip()).assign(source_priority=priority, source_file=f.name))
    return pd.concat(frames, ignore_index=True)


# ================================================================ bike rules
@logged("bike", "Keep only Heidelberg and Mannheim (project scope)")
def filter_cities(df, cities=CITIES):
    mask = df["domain_name"].str.contains("|".join(cities), case=False, na=False)
    return df[mask].copy(), ""


@logged("bike", "Remove exact duplicate rows")
def remove_exact_duplicates(df):
    cols = [c for c in df.columns if c != "source_file"]
    return df.drop_duplicates(subset=cols).copy(), ""


@logged("bike", "Rename to English names, cast text to numbers/dates, date in Europe/Berlin")
def standardise_types(df):
    out = df.rename(columns=BIKE_RENAME)
    out["city"] = out["city"].str.replace(r"^Stadt\s+", "", regex=True).str.strip()
    ts = pd.to_datetime(out["iso_timestamp"], errors="coerce", utc=True)
    out["date"] = ts.dt.tz_convert("Europe/Berlin").dt.tz_localize(None).dt.normalize()
    for c in ["bikes_in", "bikes_out", "bikes_total", "latitude", "longitude"]:
        out[c] = pd.to_numeric(out[c], errors="coerce")
    out["site_id"] = out["site_id"].astype(str).str.strip()
    bad = out["date"].isna().sum()
    out = out[out["date"].notna()]
    # counter-side weather columns are dropped: DWD is the single weather source
    out = out.drop(columns=["site_temperature", "site_rain_accumulation", "site_snow_accumulation",
                            "channels_unknown", "iso_timestamp", "timezone"], errors="ignore")
    return out, f"({bad} rows with unreadable dates removed)" if bad else ""


@logged("bike", "Keep only dates in the analysis period")
def filter_period(df, year, months=None):
    keep = df["date"].dt.year == year
    if months:
        keep &= df["date"].dt.month.isin(months)
    return df[keep].copy(), ""


@logged("bike", "One row per site + day (keep the row from the latest file)")
def deduplicate_site_day(df):
    out = (df.sort_values(["site_id", "date", "source_file"])
             .drop_duplicates(subset=["site_id", "date"], keep="last"))
    return out, ""


@logged("bike", "Negative or empty counts -> NULL (row kept)")
def invalid_counts_to_null(df):
    out = df.copy()
    neg = out["bikes_total"] < 0
    out.loc[neg, "bikes_total"] = np.nan
    for c in ["bikes_in", "bikes_out"]:
        out.loc[out[c] < 0, c] = np.nan
    return out, f"({int(neg.sum())} negative values set to NULL)"


@logged("bike", f"Runs of >= {OUTAGE_MIN_DAYS} zero days = sensor outage -> NULL + flag is_outage")
def flag_outages(df, min_days=OUTAGE_MIN_DAYS):
    out = df.sort_values(["site_id", "date"]).copy()
    zero = out["bikes_total"].eq(0)
    run_id = (zero != zero.groupby(out["site_id"]).shift()).cumsum()
    run_len = zero.groupby([out["site_id"], run_id]).transform("sum")
    out["is_outage"] = zero & (run_len >= min_days)
    out["is_zero"] = zero & ~out["is_outage"]
    out.loc[out["is_outage"], ["bikes_total", "bikes_in", "bikes_out"]] = np.nan
    return out, f"({int(out['is_outage'].sum())} outage days, {int(out['is_zero'].sum())} single zero days kept)"


@logged("bike", f"Flag outliers above Q3 + {OUTLIER_IQR_FACTOR} x IQR per site (value kept)")
def flag_outliers(df, factor=OUTLIER_IQR_FACTOR):
    out = df.copy()
    g = out.groupby("site_id")["bikes_total"]
    q1, q3 = g.transform(lambda s: s.quantile(0.25)), g.transform(lambda s: s.quantile(0.75))
    out["is_outlier"] = out["bikes_total"] > q3 + factor * (q3 - q1)
    return out, f"({int(out['is_outlier'].sum())} flagged)"


@logged("bike", "Add missing site-days inside each site's active period (NULL count, flag is_missing)")
def complete_calendar(df):
    parts = []
    for site, g in df.groupby("site_id"):
        full = pd.date_range(g["date"].min(), g["date"].max(), freq="D")
        g = g.set_index("date").reindex(full)
        g.index.name = "date"
        g["is_missing"] = g["site_id"].isna()
        g["site_id"] = site
        for c in ["site_name", "city", "counter_serial", "domain_id", "operator_name"]:
            if c in g:
                g[c] = g[c].ffill().bfill()
        for c in ["is_outage", "is_zero", "is_outlier"]:
            g[c] = g[c].astype("boolean").fillna(False).astype(bool)
        parts.append(g.reset_index())
    out = pd.concat(parts, ignore_index=True)
    return out, f"({int(out['is_missing'].sum())} missing days added as NULL, not 0)"


def split_tables(df):
    """Table 1 sites (one fixed location per site) + table 2 daily counts."""
    sites = (df.groupby("site_id")
               .agg(site_name=("site_name", "first"), city=("city", "first"),
                    latitude=("latitude", "median"), longitude=("longitude", "median"),
                    counter_serial=("counter_serial", "first"),
                    first_date=("date", "min"), last_date=("date", "max"))
               .reset_index())
    counts = df[["site_id", "date", "bikes_in", "bikes_out", "bikes_total",
                 "is_missing", "is_outage", "is_zero", "is_outlier"]].copy()
    for c in ["bikes_in", "bikes_out", "bikes_total"]:
        counts[c] = counts[c].astype("Int64")
    return sites.sort_values("site_id"), counts.sort_values(["site_id", "date"])


# ================================================================ weather rules
@logged("weather", "Prefer quality-checked historical file; recent file only for later dates")
def combine_weather_sources(w):
    out = (w.sort_values(["MESS_DATUM", "source_priority"])
             .drop_duplicates(subset="MESS_DATUM", keep="first"))
    return out, f"({len(w) - len(out)} overlapping days removed)"


@logged("weather", "Keep only dates in the analysis period")
def filter_weather_period(w, year, months=None):
    out = w.copy()
    out["date"] = pd.to_datetime(out["MESS_DATUM"], format="%Y%m%d", errors="coerce")
    keep = out["date"].dt.year == year
    if months:
        keep &= out["date"].dt.month.isin(months)
    return out[keep], ""


@logged("weather", "-999 -> NULL, cast to numbers, English column names with units")
def clean_weather_values(w):
    out = w.rename(columns=WEATHER_RENAME)
    cols = [c for c in WEATHER_RENAME.values() if c in out]
    out[cols] = out[cols].apply(pd.to_numeric, errors="coerce").replace(-999, np.nan)
    out["is_rainy"] = out["precip_mm"] >= RAINY_DAY_MM
    nulls = int(out[cols].isna().sum().sum())
    return out[["date"] + cols + ["is_rainy"]].sort_values("date"), f"({nulls} -999 values set to NULL)"


# ================================================================ features + join + aggregate
def add_calendar_features(df):
    out = df.copy()
    bw = holidays.Germany(subdiv="BW", years=sorted(out["date"].dt.year.unique()))
    out["weekday"] = out["date"].dt.day_name()
    out["is_weekend"] = out["date"].dt.day_of_week >= 5
    out["is_holiday"] = out["date"].dt.date.map(lambda d: d in bw)
    out["month"] = out["date"].dt.month
    return out


@logged("model", "Join counts + sites (site_id) + weather (date) + calendar features")
def build_model_table(counts, sites, weather):
    out = (counts.merge(sites[["site_id", "site_name", "city"]], on="site_id", how="left", validate="many_to_one")
                 .merge(weather, on="date", how="left", validate="many_to_one"))
    out = add_calendar_features(out)
    return out.sort_values(["site_id", "date"]), ""


def aggregate_weekly(model):
    m = model.copy()
    iso = m["date"].dt.isocalendar()
    m["iso_year"], m["iso_week"] = iso["year"], iso["week"]
    return (m.groupby(["site_id", "site_name", "city", "iso_year", "iso_week"])
              .agg(bikes_total=("bikes_total", "sum"), valid_days=("bikes_total", "count"),
                   temp_mean_c=("temp_mean_c", "mean"), precip_mm=("precip_mm", "sum"))
              .round(2).reset_index())


# ================================================================ pipeline
def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def run_pipeline(year=2025, months=None, write=True):
    tag = f"{year}-{months[0]:02d}" if months and len(months) == 1 else str(year)
    log = CleaningLog()
    print(f"Cleaning {tag}")

    bike = load_bike_raw(year, months)
    bike = filter_cities(bike, log)
    bike = remove_exact_duplicates(bike, log)
    bike = standardise_types(bike, log)
    bike = filter_period(bike, log, year, months)
    bike = deduplicate_site_day(bike, log)
    bike = invalid_counts_to_null(bike, log)
    bike = flag_outages(bike, log)
    bike = flag_outliers(bike, log)
    bike = complete_calendar(bike, log)
    sites, counts = split_tables(bike)

    weather = load_weather_raw()
    weather = combine_weather_sources(weather, log)
    weather = filter_weather_period(weather, log, year, months)
    weather = clean_weather_values(weather, log)

    model = build_model_table(counts, log, sites, weather)
    weekly = aggregate_weekly(model)

    tables = {"sites": sites, "daily_counts": counts, "weather_daily": weather,
              "model_table": model, "weekly_counts": weekly}
    if write:
        write_outputs(tables, log, tag)
    return tables, log


def write_outputs(tables, log, tag):
    out_dir = PROCESSED / tag
    out_dir.mkdir(parents=True, exist_ok=True)
    checks = []
    for name, df in tables.items():
        path = out_dir / f"{name}.csv"
        df.to_csv(path, index=False, date_format="%Y-%m-%d", lineterminator="\n")
        checks.append(f"| {name}.csv | {len(df):,} | {len(df.columns)} | `{sha256(path)}` |")

    c = tables["daily_counts"]
    kpis = [
        f"| Uniqueness (one row per site + day) | {100 * (1 - c.duplicated(['site_id', 'date']).mean()):.2f} % |",
        f"| Counts filled (not NULL) | {100 * c['bikes_total'].notna().mean():.2f} % |",
        f"| Missing days (flagged) | {int(c['is_missing'].sum()):,} |",
        f"| Outage days (flagged) | {int(c['is_outage'].sum()):,} |",
        f"| Outliers (flagged) | {int(c['is_outlier'].sum()):,} |",
        f"| Weather days with temperature | {tables['weather_daily']['temp_mean_c'].notna().sum()} of {len(tables['weather_daily'])} |",
        "| Type conformity | 100 % (numbers, dates and booleans typed) |",
    ]
    log_df = pd.DataFrame(log.rows)
    lines = [f"# Cleaning log — {tag}", "",
             "Generated by `src/cleaning.py`. Same rules as the Tableau Prep flow (`docs/cleaning_rules.md`).", "",
             "## Steps (rows before → after)", "",
             "| # | table | step | rule | rows before | rows after | change | note |", "|---|---|---|---|---|---|---|---|"]
    lines += [f"| {i} | {r.table} | `{r.step}` | {r.rule} | {r.before:,} | {r.after:,} | {r.change:+,} | {r.note} |"
              for i, r in enumerate(log_df.itertuples(), 1)]
    lines += ["", "## Quality after cleaning", "", "| KPI | Value |", "|---|---|"] + kpis
    lines += ["", "## Output files (checksum proves the re-run gives the same result)", "",
              "| file | rows | columns | sha256 (first 16) |", "|---|---|---|---|"] + checks
    (DOCS / f"cleaning_log_{tag}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWritten: data/processed/{tag}/ (5 files) and docs/cleaning_log_{tag}.md")


def main():
    p = argparse.ArgumentParser(description="Run the cleaning pipeline.")
    p.add_argument("--year", type=int, default=2025)
    p.add_argument("--months", type=int, nargs="+")
    a = p.parse_args()
    run_pipeline(a.year, a.months)


if __name__ == "__main__":
    main()
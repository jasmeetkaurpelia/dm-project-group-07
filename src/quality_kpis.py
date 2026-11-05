"""
quality_kpis.py — Task 3.15

Measures the same quality KPIs on the RAW data and on the CLEANED data (data/processed/2025/)
and writes the before -> after comparison for slides and report:
    docs/quality_before_after.md     KPI table: before, after, what changed
    docs/quality_before_after.png    six before -> after tiles (for the slides)

Run from the repo root, after download.py and cleaning.py:
    python src/quality_kpis.py
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cleaning as c  # noqa: E402  same loaders and rules as the pipeline

ROOT = c.ROOT
PROCESSED = ROOT / "data" / "processed" / "2025"
DOCS = ROOT / "docs"
YEAR = 2025
PLACEHOLDERS = {"na", "n/a", "nan", "null", "none", "-999"}
WEATHER_COLS = list(c.WEATHER_RENAME)          # DWD columns we keep (TMK, RSK, ...)
FLAG_COLS = ["is_missing", "is_outage", "is_zero", "is_outlier"]


def pct(part, whole):
    return round(100 * part / whole, 2) if whole else 0.0


def count_placeholders(df):
    """Cells that hold text meaning 'no value' instead of being empty."""
    return int(df.apply(lambda s: s.astype(str).str.strip().str.lower().isin(PLACEHOLDERS)).sum().sum())


# ---------------------------------------------------------------- BEFORE (raw)
def measure_before():
    raw = c.load_bike_raw(YEAR)
    bike = raw[raw["domain_name"].str.contains("|".join(c.CITIES), case=False, na=False)]
    data_cols = [col for col in bike.columns if col != "source_file"]
    n = len(bike)

    # parse a copy only to find what the raw values really are (raw files unchanged)
    typed, _ = c.standardise_types.raw(bike)
    flagged, _ = c.flag_outages.raw(typed)
    fake_zeros = int(flagged["is_outage"].sum())          # zeros that are really sensor outages
    both = typed["bikes_in"].notna() & typed["bikes_out"].notna()
    consistent = (typed.loc[both, "bikes_in"] + typed.loc[both, "bikes_out"] == typed.loc[both, "bikes_total"]).sum()

    w = c.load_weather_raw()
    w25 = w[w["MESS_DATUM"].str.startswith(str(YEAR))]
    weather_placeholders = count_placeholders(w25[[col for col in WEATHER_COLS if col in w25]])

    return {
        "rows": n,
        "site_day_unique": pct(n - typed.duplicated(["site_id", "date"]).sum(), n),
        "placeholders": count_placeholders(bike[data_cols]) + weather_placeholders,
        "fake_zeros": fake_zeros,
        "target_filled": pct(typed["bikes_total"].notna().sum(), n),
        "consistency": pct(consistent, both.sum()),
        "weather_rows": len(w25),
        "weather_unique": pct(w25["MESS_DATUM"].nunique(), len(w25)),
        "documented": 0.0,       # source data dictionary: names only, every column typed "text"
        "flag_cols": 0,
    }


# ---------------------------------------------------------------- AFTER (cleaned)
def measure_after():
    tables = {f.stem: pd.read_csv(f, dtype=str, keep_default_na=False) for f in sorted(PROCESSED.glob("*.csv"))}
    if "daily_counts" not in tables:
        raise SystemExit("No cleaned data. Run: python src/cleaning.py")
    counts = pd.read_csv(PROCESSED / "daily_counts.csv", parse_dates=["date"])
    sites = pd.read_csv(PROCESSED / "sites.csv", parse_dates=["first_date", "last_date"])
    weather = pd.read_csv(PROCESSED / "weather_daily.csv")

    expected = int(((sites["last_date"] - sites["first_date"]).dt.days + 1).sum())
    both = counts["bikes_in"].notna() & counts["bikes_out"].notna()
    consistent = (counts.loc[both, "bikes_in"] + counts.loc[both, "bikes_out"] == counts.loc[both, "bikes_total"]).sum()

    dictionary = (DOCS / "data_dictionary.md").read_text(encoding="utf-8") if (DOCS / "data_dictionary.md").exists() else ""
    columns = {col for t in tables.values() for col in t.columns}
    documented = sum(f"`{col}`" in dictionary for col in columns)

    return {
        "rows": len(counts),
        "expected_rows": expected,
        "site_day_unique": pct(len(counts) - counts.duplicated(["site_id", "date"]).sum(), len(counts)),
        "placeholders": sum(count_placeholders(t) for t in tables.values()),
        "fake_zeros": int((counts["is_outage"] & counts["bikes_total"].eq(0)).sum()),
        "target_filled": pct(counts["bikes_total"].notna().sum(), len(counts)),
        "consistency": pct(consistent, both.sum()),
        "weather_rows": len(weather),
        "weather_unique": pct(weather["date"].nunique(), len(weather)),
        "documented": pct(documented, len(columns)),
        "flag_cols": sum(col in counts for col in FLAG_COLS),
    }


# ---------------------------------------------------------------- report
def build_rows(b, a):
    calendar_before = pct(b["rows"], a["expected_rows"])
    calendar_after = pct(a["rows"], a["expected_rows"])
    return [
        # KPI, dimension, before, after, what we did, show in chart (percent)
        ("Documented data types (columns in data dictionary)", "Interpretability",
         f"{b['documented']} %", f"{a['documented']} %", "Data dictionary with type, unit, meaning per column", (b["documented"], a["documented"])),
        ("Weather: one row per date (2025)", "Uniqueness",
         f"{b['weather_unique']} % ({b['weather_rows']} rows)", f"{a['weather_unique']} % ({a['weather_rows']} rows)",
         "Historical file kept, duplicate dates from recent file removed (W1)", (b["weather_unique"], a["weather_unique"])),
        ("Site-days present in each site's active period", "Completeness (rows)",
         f"{calendar_before} %", f"{calendar_after} %", "Missing days added as NULL rows with `is_missing` (B9)", (calendar_before, calendar_after)),
        ("Bike counts filled (not NULL)", "Completeness (values)",
         f"{b['target_filled']} %", f"{a['target_filled']} %",
         "Goes DOWN on purpose: fake zeros and missing days are now honest NULLs", (b["target_filled"], a["target_filled"])),
        ("Hidden missing values (text 'na', -999)", "Validity",
         f"{b['placeholders']:,}", f"{a['placeholders']:,}", "Read as NULL (B3, W3)", None),
        ("Zero counts that are really sensor outages", "Accuracy / plausibility",
         f"{b['fake_zeros']:,}", f"{a['fake_zeros']:,}", "Set to NULL + `is_outage` flag (B7)", None),
        ("Quality flag columns", "Transparency",
         f"{b['flag_cols']}", f"{a['flag_cols']}", "`is_missing`, `is_outage`, `is_zero`, `is_outlier`", None),
        ("One row per site + day", "Uniqueness",
         f"{b['site_day_unique']} %", f"{a['site_day_unique']} %",
         "Checked (B5), already clean" if b["site_day_unique"] == 100 else "Duplicates removed (B2, B5)", None),
        ("IN + OUT = ALL", "Consistency",
         f"{b['consistency']} %", f"{a['consistency']} %",
         "Checked, already clean" if b["consistency"] == 100 else "Checked; ALL is used as the target", None),
        ("Rows (Heidelberg + Mannheim)", "Volume",
         f"{b['rows']:,}", f"{a['rows']:,}", "+ missing days added as NULL rows", None),
    ]


def write_markdown(rows):
    lines = ["# Quality KPIs — before vs after cleaning", "",
             "Generated by `src/quality_kpis.py`. Before = raw files (`data/raw/`), after = cleaned files "
             "(`data/processed/2025/`). Same definitions on both sides.", "",
             "| KPI | Quality dimension | Before (raw) | After (cleaned) | What we did |",
             "|---|---|---|---|---|"]
    lines += [f"| {k} | {d} | {b} | {a} | {w} |" for k, d, b, a, w, _ in rows]
    lines += ["", "**Read this first:** completeness of bike counts goes *down* slightly. That is the point: "
              "before, broken-sensor days looked like real data (0 bikes); after, they are marked as unknown.",
              "", "FAIR score before → after: see `docs/fair_score.md`.", ""]
    (DOCS / "quality_before_after.md").write_text("\n".join(lines), encoding="utf-8")


def draw_tiles(b, a):
    """Six before -> after tiles for the slide: grey = raw, blue = cleaned."""
    grey, blue, ink, muted, line = "#8a8984", "#2a78d6", "#0b0b0b", "#52514e", "#dcdbd6"
    gaps_before = a["expected_rows"] - b["rows"]
    tiles = [
        (f"{b['placeholders']:,}", f"{a['placeholders']:,}", "hidden missing values", "text 'na' and -999 now read as NULL"),
        (f"{b['fake_zeros']:,}", f"{a['fake_zeros']:,}", "zero counts that were sensor outages", "set to NULL + flag is_outage"),
        (f"{b['weather_rows'] - round(b['weather_rows'] * b['weather_unique'] / 100):,}",
         f"{a['weather_rows'] - round(a['weather_rows'] * a['weather_unique'] / 100):,}",
         "duplicate weather days (2025)", "historical file kept"),
        (f"{gaps_before:,}", "0", "silent gaps (site-days with no row)", "added as NULL rows + flag is_missing"),
        (f"{b['documented']:g} %", f"{a['documented']:g} %", "columns with type, unit, meaning", "data dictionary"),
        (f"{b['target_filled']:g} %", f"{a['target_filled']:g} %", "bike counts filled",
         "lower on purpose: unknown no longer shown as 0"),
    ]
    fig = plt.figure(figsize=(13.33, 6.9), dpi=150)
    fig.patch.set_facecolor("white")
    fig.text(0.04, 0.93, "Data quality before and after cleaning", fontsize=22, fontweight="bold", color=ink)
    fig.text(0.04, 0.885, "Heidelberg + Mannheim bike counts and DWD weather, 2025 · grey = raw data, blue = cleaned data",
             fontsize=12.5, color=muted)
    cols, w, h, x0, y_top, gx, gy = 3, 0.29, 0.31, 0.04, 0.82, 0.035, 0.06
    for i, (before, after, label, note) in enumerate(tiles):
        r, col = divmod(i, cols)
        x, y = x0 + col * (w + gx), y_top - (r + 1) * h - r * gy
        ax = fig.add_axes([x, y, w, h]); ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
        ax.plot([0, 1], [1, 1], color=line, lw=1.2)
        t = ax.text(0, 0.62, before, fontsize=30, fontweight="bold", color=grey, va="center")
        fig.canvas.draw()
        end = ax.transAxes.inverted().transform(t.get_window_extent().corners()[-1])[0]   # right edge of number
        ax.annotate("", xy=(end + 0.13, 0.62), xytext=(end + 0.04, 0.62), xycoords="axes fraction",
                    arrowprops=dict(arrowstyle="-|>", color=muted, lw=1.6))
        ax.text(end + 0.17, 0.62, after, fontsize=30, fontweight="bold", color=blue, va="center")
        ax.text(0, 0.30, label, fontsize=14, color=ink, va="center")
        ax.text(0, 0.13, note, fontsize=11.5, color=muted, va="center", style="italic")
    fig.savefig(DOCS / "quality_before_after.png", facecolor="white")


def main():
    before, after = measure_before(), measure_after()
    rows = build_rows(before, after)
    write_markdown(rows)
    draw_tiles(before, after)
    for k, _, b, a, _, _ in rows:
        print(f"  {k}: {b} -> {a}")
    print("\nWritten: docs/quality_before_after.md and docs/quality_before_after.png")


if __name__ == "__main__":
    main()
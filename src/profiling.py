"""
profiling.py — Tasks 2.1 / 2.2 / 2.3

Profiles the RAW data (read-only, nothing is changed) and writes the profiling log:
    docs/profiling_report.md        quality KPIs, column profile, issues, proposed cleaning rules
    docs/column_profile_bike.csv    column profile as a table (for slides)

Usage (from the repo root, after download.py):
    python src/profiling.py
"""

from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BIKE_DIR = ROOT / "data" / "raw" / "bike"
WEATHER_DIR = ROOT / "data" / "raw" / "weather"
DOCS = ROOT / "docs"
REPORT = DOCS / "profiling_report.md"

CITIES = ["Heidelberg", "Mannheim"]
NA_TOKENS = {"", "na", "n/a", "nan", "null", "none"}   # text that really means "no value"
YEAR = 2025
NUMERIC_BIKE = ["channels_in", "channels_out", "channels_unknown", "channels_all",
                "site_temperature", "site_rain_accumulation", "site_snow_accumulation", "longitude", "latitude"]


# ---------------------------------------------------------------- helpers
def md_table(df: pd.DataFrame) -> str:
    """DataFrame -> markdown table (no extra package needed)."""
    cols = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join("" if pd.isna(v) else str(v) for v in row) + " |")
    return "\n".join(lines)


def pct(part, whole) -> float:
    return round(100 * part / whole, 2) if whole else 0.0


def column_profile(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for c in df.columns:
        s = df[c]
        blank = s.isna() | s.astype(str).str.strip().str.lower().isin(NA_TOKENS)
        num = pd.to_numeric(s, errors="coerce")
        non_blank = (~blank).sum()
        rows.append({
            "column": c,
            "stored as": str(s.dtype) if pd.api.types.is_numeric_dtype(s) else "text",
            "missing %": pct(blank.sum(), len(s)),
            "distinct": s.nunique(dropna=True),
            "numeric %": pct(num.notna().sum(), non_blank),
            "min": num.min() if num.notna().any() else "",
            "max": num.max() if num.notna().any() else "",
            "example": s.dropna().iloc[0] if s.notna().any() else "",
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- load raw data
def load_bike() -> pd.DataFrame:
    files = sorted(BIKE_DIR.glob(f"fahrradzaehler_tageswerten_{YEAR}*.csv"))
    if not files:
        raise SystemExit("No bike CSV files found. Run: python src/download.py")
    df = pd.concat([pd.read_csv(f, sep=None, engine="python", dtype=str).assign(source_file=f.name)
                    for f in files], ignore_index=True)
    return df, files


def load_weather() -> dict:
    """Two DWD files: the one that starts earliest is 'historical', the other 'recent'."""
    files = sorted(WEATHER_DIR.glob("produkt_klima_tag_*.txt"), key=lambda f: f.name.split("_")[3])
    out = {}
    for kind, f in zip(["historical", "recent"], files):
        w = pd.read_csv(f, sep=";", skipinitialspace=True, dtype=str)
        w.columns = w.columns.str.strip()
        w = w.apply(lambda s: s.str.strip())
        out[kind] = (f.name, w)
    return out


# ---------------------------------------------------------------- main
def main() -> None:
    DOCS.mkdir(exist_ok=True)
    raw, files = load_bike()
    total_all = len(raw)
    city = raw["domain_name"].str.contains("|".join(CITIES), case=False, na=False)
    bike = raw[city].copy()
    n = len(bike)

    # parse what we need for checks (only in memory)
    ts = pd.to_datetime(bike["iso_timestamp"], errors="coerce", utc=True)
    bike["_date"] = ts.dt.tz_convert("Europe/Berlin").dt.date
    for c in NUMERIC_BIKE:
        if c in bike:
            bike["_" + c] = pd.to_numeric(bike[c], errors="coerce")

    prof = column_profile(bike.drop(columns=[c for c in bike.columns if c.startswith("_")] + ["source_file"]))
    prof.to_csv(DOCS / "column_profile_bike.csv", index=False)

    # ---- checks
    bad_dates = ts.isna().sum()
    out_of_year = (ts.notna() & (pd.to_datetime(bike["_date"]).dt.year != YEAR)).sum()
    dup_rows = bike.duplicated(subset=[c for c in raw.columns if c != "source_file"]).sum()
    dup_keys = bike.duplicated(subset=["counter_site_id", "_date"]).sum()
    all_missing = bike["_channels_all"].isna().sum()
    negative = (bike["_channels_all"] < 0).sum()
    zero = (bike["_channels_all"] == 0).sum()
    both = bike["_channels_in"].notna() & bike["_channels_out"].notna() & bike["_channels_all"].notna()
    unknown = bike["_channels_unknown"].fillna(0) if "_channels_unknown" in bike else 0
    mismatch = (both & (bike["_channels_in"] + bike["_channels_out"] + unknown != bike["_channels_all"])).sum()

    data_cols = [c for c in raw.columns if c != "source_file"]
    na_text = int(bike[data_cols].apply(lambda col: col.astype(str).str.strip().str.lower().isin(NA_TOKENS - {""})).sum().sum())
    na_rows_direction = int(bike["channels_in"].astype(str).str.strip().str.lower().isin(NA_TOKENS).sum())
    names = bike["counter_site"].astype(str).drop_duplicates()
    odd_names = names[names.str.contains(r"\.\s*$|\s{2,}|^\s|\s$", regex=True)]

    # outliers per site: above Q3 + 3*IQR
    g = bike.groupby("counter_site_id")["_channels_all"]
    q1, q3 = g.transform(lambda s: s.quantile(0.25)), g.transform(lambda s: s.quantile(0.75))
    outliers = (bike["_channels_all"] > q3 + 3 * (q3 - q1)).sum()

    # coverage: days per site out of the year
    days_in_year = 366 if YEAR % 4 == 0 else 365
    sites = (bike.groupby(["domain_name", "counter_site_id", "counter_site"])
                 .agg(days=("_date", "nunique"), first=("_date", "min"), last=("_date", "max"),
                      zero_days=("_channels_all", lambda s: int((s == 0).sum())),
                      mean_per_day=("_channels_all", "mean"))
                 .reset_index())
    sites["mean_per_day"] = sites["mean_per_day"].round(0)
    sites["missing_days"] = days_in_year - sites["days"]
    expected = len(sites) * days_in_year
    site_coords = bike.groupby("counter_site_id")[["longitude", "latitude"]].nunique().max(axis=1)
    moved_sites = int((site_coords > 1).sum())

    # ---- weather
    weather = load_weather()
    w_lines, w_issues = [], []
    year_frames = {}
    for kind, (fname, w) in weather.items():
        w_year = w[w["MESS_DATUM"].str.startswith(str(YEAR))]
        year_frames[kind] = w_year
        miss = {c: pct((w_year[c] == "-999").sum(), len(w_year)) for c in w_year.columns
                if c not in ("STATIONS_ID", "MESS_DATUM", "eor")}
        worst = ", ".join(f"{c} {v}%" for c, v in sorted(miss.items(), key=lambda x: -x[1]) if v > 0) or "none"
        w_lines.append(f"| {kind} | {fname} | {len(w):,} | {w['MESS_DATUM'].min()}–{w['MESS_DATUM'].max()} | "
                       f"{len(w_year)} | {worst} |")
    overlap = conflicts = 0
    if {"historical", "recent"} <= year_frames.keys():
        h = year_frames["historical"].set_index("MESS_DATUM")
        r = year_frames["recent"].set_index("MESS_DATUM")
        common = h.index.intersection(r.index)
        overlap = len(common)
        cols = [c for c in ["TMK", "RSK", "SHK_TAG"] if c in h.columns and c in r.columns]
        conflicts = int((h.loc[common, cols] != r.loc[common, cols]).any(axis=1).sum()) if overlap else 0
    weather_days = len(pd.concat(year_frames.values())["MESS_DATUM"].unique()) if year_frames else 0

    # ---- KPIs
    key_cols = ["counter_site_id", "iso_timestamp", "channels_all"]
    key_missing = sum((bike[c].isna() | (bike[c].astype(str).str.strip() == "")).sum() for c in key_cols)
    kpis = pd.DataFrame([
        ["Completeness (key fields filled)", f"{100 - pct(key_missing, n * len(key_cols))} %", "counter_site_id, iso_timestamp, channels_all not empty"],
        ["Coverage (site-days present)", f"{pct(n - dup_keys, expected)} %", f"{n - dup_keys:,} of {expected:,} = {len(sites)} sites × {days_in_year} days"],
        ["Uniqueness (one row per site + day)", f"{100 - pct(dup_keys, n)} %", f"{dup_keys} duplicate site-days"],
        ["Validity (count is a number ≥ 0, valid date)", f"{100 - pct(all_missing + negative + bad_dates, n)} %", f"{all_missing} empty, {negative} negative, {bad_dates} bad dates"],
        ["Consistency (IN + OUT + unknown = ALL)", f"{100 - pct(mismatch, both.sum())} %", f"{mismatch} of {both.sum():,} rows do not add up"],
        ["Type conformity (numbers stored as numbers)", "0 %", "all columns arrive as text"],
        ["Weather timeliness / completeness", f"{pct(weather_days, days_in_year)} %", f"{weather_days} of {days_in_year} days of {YEAR} available"],
    ], columns=["KPI", "Raw value", "How measured"])

    issues = pd.DataFrame([
        ["Missing site-days", f"{expected - (n - dup_keys):,}", "Counters off, installed or removed during the year", "Keep, flag `is_missing`; do not fill with 0"],
        ["Zero-count days", f"{zero:,}", "Sensor outage or real closure (construction)", "Flag; treat runs of ≥ 3 zero days as outage → NULL"],
        ["Outliers (> Q3 + 3×IQR per site)", f"{outliers:,}", "Events, sensor errors", "Flag `is_outlier`, check top 10 by hand"],
        ["Duplicate site-days", f"{dup_keys:,}", "Same day in two monthly files / time zone shift", "Keep one row per site + day"],
        ["Exact duplicate rows", f"{dup_rows:,}", "Repeated export", "Remove"],
        ["IN + OUT ≠ ALL", f"{mismatch:,}", "Direction channels incomplete", "Use `channels_all` as the target"],
        ["Empty / negative counts", f"{all_missing + negative:,}", "Missing value or error", "Set to NULL"],
        ["Dates outside {0}".format(YEAR), f"{out_of_year:,}", "Time zone (UTC vs Berlin)", "Convert to Europe/Berlin date first"],
        ["Sites with changing coordinates", f"{moved_sites}", "Counter moved / reconfigured", "Use one fixed location per site in sites table"],
        ["Text 'na' used instead of an empty value", f"{na_text:,} cells ({na_rows_direction:,} rows without direction counts)",
         "Export writes 'na' when a channel does not exist", "Read 'na' as NULL"],
        ["Inconsistent site names", f"{len(odd_names)} names", "Typed by hand: trailing dots, typos, mixed spelling",
         "Strip trailing dots/spaces; keep site_id as the key"],
        ["All columns stored as text", f"{len(raw.columns) - 1}", "CSV export", "Cast to int / float / date"],
        ["Weather -999 codes", "see weather table", "DWD code for 'no value'", "Replace -999 with NULL"],
        ["Weather files overlap", f"{overlap} days ({conflicts} with different values)", "historical + recent both cover the same dates", "Keep historical (quality-checked), recent only for later dates"],
        ["Weather column names padded", "all", "Fixed-width DWD format", "Strip spaces, rename to English"],
    ], columns=["Issue", "Count", "Likely cause", "Proposed cleaning rule"])

    # ---- keep hand-written key findings from the previous report
    findings = "- \n- \n- \n"
    if REPORT.exists():
        old = REPORT.read_text(encoding="utf-8")
        if "## Key findings" in old:
            block = old.split("## Key findings", 1)[1]
            block = block.split("\n## ", 1)[0]
            findings = block.split("\n", 1)[1].strip("\n") + "\n"

    # ---- write report
    r = []
    r.append(f"# Profiling report — raw data\n\nGenerated by `src/profiling.py` on {datetime.now():%d %b %Y %H:%M}. Raw files are not changed.\n")
    r.append("## Key findings\n\n" + findings)
    r.append("## Dataset size\n")
    r.append(md_table(pd.DataFrame([
        ["Bike files", len(files), f"{files[0].name} … {files[-1].name}"],
        ["Rows, all Baden-Württemberg", f"{total_all:,}", ""],
        ["Rows, Heidelberg + Mannheim", f"{n:,}", "scope of this project"],
        ["Rows per city", "", " / ".join(f"{k}: {v:,}" for k, v in bike['domain_name'].value_counts().items())],
        ["Counter sites", len(sites), ""],
        ["Columns", len(raw.columns) - 1, ""],
        ["Date range", f"{min(d for d in bike['_date'] if pd.notna(d))} – {max(d for d in bike['_date'] if pd.notna(d))}", ""],
    ], columns=["Measure", "Value", "Note"])) + "\n")
    r.append("## Quality KPIs (raw)\n")
    r.append(md_table(kpis) + "\n")
    r.append("## Issues found and proposed cleaning rules\n\nCopy the agreed rules into `docs/cleaning_rules.md`.\n")
    r.append(md_table(issues) + "\n")
    r.append("## Column profile — bike counts (Heidelberg + Mannheim)\n")
    r.append(md_table(prof) + "\n")
    r.append("## Coverage per counter site\n")
    r.append(md_table(sites.sort_values(["missing_days", "zero_days"], ascending=False)
                      .rename(columns={"domain_name": "city"})) + "\n")
    r.append("## Weather (DWD, station Mannheim)\n")
    r.append(f"| file | name | rows (all years) | date range | rows in {YEAR} | -999 share in {YEAR} |\n|---|---|---|---|---|---|")
    r.append("\n".join(w_lines) + "\n")
    r.append(f"Overlap of historical and recent in {YEAR}: **{overlap} days**, of which **{conflicts}** have different values "
             f"(temperature, rain or snow).\n")
    REPORT.write_text("\n".join(r), encoding="utf-8")

    print(f"Rows HD + MA: {n:,} | sites: {len(sites)} | duplicates: {dup_keys} | zero days: {zero} | "
          f"missing site-days: {expected - (n - dup_keys):,} | weather overlap: {overlap} days")
    print(f"Written: {REPORT.relative_to(ROOT)} and docs/column_profile_bike.csv")


if __name__ == "__main__":
    main()
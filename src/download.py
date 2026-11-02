"""
download.py — Task 1.1 / 1.2 / 1.4

Downloads the raw data for the project into data/raw/ without changing it:
  1. Bike counts (MobiData BW, Eco-Counter, daily values) — one file per month
  2. Daily weather for the DWD station Mannheim (Deutscher Wetterdienst, "kl" daily climate data)

It also writes data/raw/download_log.json (URL, file, size, SHA-256, time) for lineage and FAIR.

Usage (from the repo root):
    python src/download.py                  # year 2025, all 12 months + weather
    python src/download.py --year 2026 --months 1      # one new month (for the re-run test)
    python src/download.py --force          # download again even if files exist

Licences:
    Bike counts: MobiData BW / NVBW — Datenlizenz Deutschland – Namensnennung 2.0
    Weather:     Deutscher Wetterdienst (DWD) — CC BY 4.0
"""

import argparse
import gzip
import hashlib
import json
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

# ---------------------------------------------------------------- settings
BIKE_URL = "https://mobidata-bw.de/daten/eco-counter/v2/fahrradzaehler_tageswerten_{yyyymm}.csv.gz"
DWD_BASE = "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/daily/kl/"
DWD_STATION_LIST = "KL_Tageswerte_Beschreibung_Stationen.txt"
WEATHER_STATION_NAME = "Mannheim"
CITIES = ["Heidelberg", "Mannheim"]          # used only for the row-count check

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
BIKE_DIR = RAW / "bike"
WEATHER_DIR = RAW / "weather"
LOG_FILE = RAW / "download_log.json"

session = requests.Session()
session.headers["User-Agent"] = "SRH-DataManagement-student-project"


# ---------------------------------------------------------------- helpers
def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, target: Path, force: bool, log: list) -> bool:
    """Download url to target. Returns False if the file does not exist online (404)."""
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not force:
        print(f"  skip (already there): {target.relative_to(ROOT)}")
    else:
        resp = session.get(url, timeout=60, stream=True)
        if resp.status_code == 404:
            print(f"  not available yet: {url}")
            return False
        resp.raise_for_status()
        with open(target, "wb") as f:
            for chunk in resp.iter_content(1 << 20):
                f.write(chunk)
        print(f"  downloaded: {target.relative_to(ROOT)}")
    log.append({
        "url": url,
        "file": str(target.relative_to(ROOT)).replace("\\", "/"),
        "bytes": target.stat().st_size,
        "sha256": sha256(target),
        "downloaded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })
    return True


def unzip_gz(gz_path: Path) -> Path:
    """Unpack .csv.gz to .csv next to it (Tableau Prep cannot read .gz). Content is unchanged."""
    csv_path = gz_path.with_suffix("")
    with gzip.open(gz_path, "rb") as src, open(csv_path, "wb") as dst:
        shutil.copyfileobj(src, dst)
    return csv_path


# ---------------------------------------------------------------- 1. bike counts
def download_bike(year: int, months: list, force: bool, log: list) -> list:
    print(f"\n[1] Bike counts {year}, months {months}")
    csv_files = []
    for m in months:
        yyyymm = f"{year}{m:02d}"
        gz = BIKE_DIR / f"fahrradzaehler_tageswerten_{yyyymm}.csv.gz"
        if download(BIKE_URL.format(yyyymm=yyyymm), gz, force, log):
            csv_files.append(unzip_gz(gz))
    return csv_files


def check_bike_rows(csv_files: list) -> None:
    """Task 1.3: count rows for Heidelberg + Mannheim (read-only check, nothing is changed)."""
    if not csv_files:
        return
    frames = [pd.read_csv(f, sep=None, engine="python", dtype=str) for f in csv_files]
    df = pd.concat(frames, ignore_index=True)
    city_col = next((c for c in ["domain_name", "operator_name"] if c in df.columns), None)
    print(f"\n  Total rows (all of Baden-Württemberg): {len(df):,}")
    print(f"  Columns: {list(df.columns)}")
    if city_col is None:
        print("  ! No domain_name / operator_name column found — check the columns above.")
        return
    mask = df[city_col].str.contains("|".join(CITIES), case=False, na=False)
    sub = df[mask]
    print(f"  Rows for {' + '.join(CITIES)}: {len(sub):,}   (needs >= 1,000)")
    print(f"  Counter sites: {sub['counter_site'].nunique() if 'counter_site' in sub else 'n/a'}")
    print("  Rows per city:")
    print(sub[city_col].value_counts().to_string())


# ---------------------------------------------------------------- 2. weather
def find_station_id(name: str, force: bool, log: list) -> str:
    """Read the DWD station list and return the 5-digit id of the active station with this name."""
    path = WEATHER_DIR / DWD_STATION_LIST
    download(DWD_BASE + "recent/" + DWD_STATION_LIST, path, force, log)
    candidates = []
    for line in path.read_text(encoding="latin-1").splitlines():
        parts = line.split()
        if parts and parts[0].isdigit() and name.lower() in line.lower():
            # columns: Stations_id von_datum bis_datum Stationshoehe geoBreite geoLaenge Stationsname Bundesland ...
            candidates.append((parts[2], parts[0].zfill(5), line.strip()))
    if not candidates:
        raise SystemExit(f"No DWD station with '{name}' in the name found in {path}")
    candidates.sort(reverse=True)               # newest bis_datum first = still active
    print("  Matching stations (newest first):")
    for _, _, line in candidates:
        print("   ", line)
    return candidates[0][1]


def list_dir(url: str) -> str:
    resp = session.get(url, timeout=60)
    resp.raise_for_status()
    return resp.text


def extract_produkt(zip_path: Path) -> Path:
    """Extract the data file produkt_klima_tag_*.txt (semicolon separated, -999 = missing)."""
    with zipfile.ZipFile(zip_path) as z:
        name = next(n for n in z.namelist() if n.startswith("produkt_klima_tag"))
        target = WEATHER_DIR / name
        with z.open(name) as src, open(target, "wb") as dst:
            shutil.copyfileobj(src, dst)
    print(f"  extracted: {target.relative_to(ROOT)}")
    return target


def download_weather(force: bool, log: list) -> list:
    print(f"\n[2] DWD daily weather, station '{WEATHER_STATION_NAME}'")
    sid = find_station_id(WEATHER_STATION_NAME, force, log)
    print(f"  Using station id {sid}")
    files = []

    # historical = checked data up to the end of last year (file name contains the date range)
    hist_name = re.search(rf"tageswerte_KL_{sid}_\d{{8}}_\d{{8}}_hist\.zip", list_dir(DWD_BASE + "historical/"))
    if hist_name:
        z = WEATHER_DIR / hist_name.group(0)
        if download(DWD_BASE + "historical/" + z.name, z, force, log):
            files.append(extract_produkt(z))
    else:
        print("  ! no historical file found for this station")

    # recent = about the last 500 days, not yet fully quality-checked (overlaps with historical!)
    z = WEATHER_DIR / f"tageswerte_KL_{sid}_akt.zip"
    if download(DWD_BASE + "recent/" + z.name, z, force, log):
        files.append(extract_produkt(z))

    for f in files:
        df = pd.read_csv(f, sep=";", skipinitialspace=True, dtype=str)
        df.columns = df.columns.str.strip()
        print(f"  {f.name}: {len(df):,} rows, {df['MESS_DATUM'].min()} to {df['MESS_DATUM'].max()}")
    return files


# ---------------------------------------------------------------- main
def main() -> None:
    parser = argparse.ArgumentParser(description="Download raw bike count and weather data.")
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--months", type=int, nargs="+", default=list(range(1, 13)))
    parser.add_argument("--skip-weather", action="store_true")
    parser.add_argument("--force", action="store_true", help="download again even if files exist")
    args = parser.parse_args()

    log: list = []
    bike_files = download_bike(args.year, args.months, args.force, log)
    check_bike_rows(bike_files)
    if not args.skip_weather:
        download_weather(args.force, log)

    old = json.loads(LOG_FILE.read_text()) if LOG_FILE.exists() else []
    LOG_FILE.write_text(json.dumps(old + log, indent=2))
    print(f"\nDone. {len(log)} files logged in {LOG_FILE.relative_to(ROOT)}")
    print("Write the download date and the row count from above into README.md (tasks 1.3 + 1.4).")


if __name__ == "__main__":
    main()
import os
import sys
from pathlib import Path
import pandas as pd

current_dir = Path(__file__).resolve().parent
repo_root = None

for parent in [current_dir, *current_dir.parents]:
    if (parent / "src" / "cleaning.py").is_file():
        repo_root = parent
        break

if repo_root is not None:
    src_path = str(repo_root / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
else:
    cwd_src = Path.cwd() / "src"
    if cwd_src.is_dir() and str(cwd_src) not in sys.path:
        sys.path.insert(0, str(cwd_src))

import cleaning as c

# Fallback stubs for linter
if "prep_string" not in globals():
    def prep_string(): return ["prep_string_type"]
    def prep_decimal(): return ["prep_decimal_type"]
    def prep_bool(): return ["prep_bool_type"]


# Tableau Prep Step Function (Rules B7 & B8)
def flag_rules(df: pd.DataFrame) -> pd.DataFrame:
    # 1. Clean incoming date string (strip trailing 'Z')
    if "date" in df.columns:
        clean_date_str = df["date"].astype(str).str.rstrip("Z")
        df["date"] = pd.to_datetime(clean_date_str, errors="coerce")

    # 2. Run outage and outlier logic from src/cleaning.py
    out, _ = c.flag_outages.raw(df)
    out, _ = c.flag_outliers.raw(out)

    # 3. JSON-safe string conversion (bypasses Timestamp JSON serializability error)
    out["site_id"] = out["site_id"].astype(str)
    out["date"] = pd.to_datetime(out["date"].astype(str).str.rstrip("Z"), errors="coerce").dt.strftime("%Y-%m-%d")

    # Ensure floats for numeric fields
    for col in ["bikes_in", "bikes_out", "bikes_total"]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").astype(float)
        else:
            out[col] = None

    # Ensure python bools
    for col in ["is_outage", "is_zero", "is_outlier"]:
        if col in out.columns:
            out[col] = out[col].fillna(False).astype(bool)
        else:
            out[col] = False

    schema_cols = [
        "site_id",
        "date",
        "bikes_in",
        "bikes_out",
        "bikes_total",
        "is_outage",
        "is_zero",
        "is_outlier",
    ]
    return out[schema_cols]

# Output Schema (date returned as prep_string to match JSON serialization)
def get_output_schema():
    return pd.DataFrame({
        "site_id": prep_string(),
        "date": prep_string(),
        "bikes_in": prep_decimal(),
        "bikes_out": prep_decimal(),
        "bikes_total": prep_decimal(),
        "is_outage": prep_bool(),
        "is_zero": prep_bool(),
        "is_outlier": prep_bool(),
    })
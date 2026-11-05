# Cleaning rules

Agreed rules for **both** tools. Python (`src/cleaning.py`) and Tableau Prep (`tableau/flow.tflx`) apply the same rules in the same order, so the row counts must match (task 3.10).

Source of each rule: issues found in `docs/profiling_report.md`.
**Golden rule:** never edit `data/raw/`. Missing or broken values become **NULL**, never 0.

## Settings

| Setting | Value | Used in rule |
|---|---|---|
| Cities | Heidelberg, Mannheim | B1 |
| Period | 1 Jan – 31 Dec 2025 | B4, W2 |
| Outage | ≥ 3 zero days in a row (per site) | B7 |
| Outlier | above Q3 + 3 × IQR (per site) | B8 |
| Rainy day | ≥ 1.0 mm precipitation | W3 |

## Bike counts

| # | Rule | Why (issue from profiling) | Type | Python function | Tableau Prep step |
|---|---|---|---|---|---|
| B1 | Keep only rows where `domain_name` contains Heidelberg or Mannheim | Raw files cover all of Baden-Württemberg | removes rows | `filter_cities` | **Clean step** → Filter → Calculated: `CONTAINS([domain_name],"Heidelberg") OR CONTAINS([domain_name],"Mannheim")` |
| B2 | Remove exact duplicate rows | Repeated export rows | removes rows | `remove_exact_duplicates` | **Aggregate step**: group by all columns (except the file name) |
| B3 | Rename to English, cast types: counts → whole number, lat/long → decimal, `iso_timestamp` → date in Europe/Berlin; remove the `Stadt ` prefix ("Stadt Heidelberg" → "Heidelberg"); drop counter-side weather columns | All columns stored as text; German names; DWD is our single weather source | changes values | `standardise_types` | **Clean step**: change data types, rename fields, `REPLACE([domain_name],"Stadt ","")`, `DATE(LEFT([iso_timestamp],10))`, remove fields |
| B4 | Keep only dates in 2025 | Time zone shift can push rows into another year | removes rows | `filter_period` | **Clean step** → Filter → Range of dates |
| B5 | One row per `site_id` + `date`; if two, keep the row from the later monthly file | Duplicate site-days | removes rows | `deduplicate_site_day` | **Aggregate step**: group by `site_id`, `date`; MAX of the file name; join back |
| B6 | Negative counts → NULL (row kept) | Invalid values | changes values | `invalid_counts_to_null` | **Clean step** → Calculated: `IF [bikes_total] < 0 THEN NULL ELSE [bikes_total] END` |
| B7 | ≥ 3 zero days in a row = sensor outage → count NULL + flag `is_outage`; single zero days kept + flag `is_zero` | Zero-count days | changes values + flag | `flag_outages` | **Script step** calling the Python function (see below) |
| B8 | Flag outliers above Q3 + 3 × IQR per site; value kept | Extreme days (events, errors) | flag only | `flag_outliers` | **Script step** (same script) |
| B9 | Add missing days inside each site's active period (first → last date) with NULL count + flag `is_missing` | Missing site-days | adds rows | `complete_calendar` | **New Rows step** on `date`, grouped by `site_id` (or Script step) |
| B10 | Split into **sites** (one row per site, median lat/long) and **daily_counts** (site + day) | Need two related tables, one fixed location per site | restructure | `split_tables` | **Aggregate step** by `site_id` → sites output; second branch → daily_counts output |

## Weather (DWD Mannheim, station 05906)

| # | Rule | Why | Type | Python function | Tableau Prep step |
|---|---|---|---|---|---|
| W1 | Strip spaces from column names and values; **historical file first**, recent file only for dates not in historical | Padded fixed-width format; files overlap (May–Dec 2025) | removes rows | `combine_weather_sources` | **Union step** of both files + field `source_priority` (0 = historical, 1 = recent) → **Aggregate** by date, MIN(priority) → join back |
| W2 | Keep only dates in 2025 (`MESS_DATUM` yyyymmdd → date) | File goes back to 1781 | removes rows | `filter_weather_period` | **Clean step**: `DATEPARSE("yyyyMMdd",[MESS_DATUM])`, filter range |
| W3 | `-999` → NULL; rename: TMK → temp_mean_c, TXK → temp_max_c, TNK → temp_min_c, RSK → precip_mm, SHK_TAG → snow_depth_cm, SDK → sunshine_h, FM → wind_mean_ms, UPM → humidity_pct; add `is_rainy` | DWD code for "no value"; cryptic names | changes values | `clean_weather_values` | **Clean step**: Replace -999 with NULL (or calc `IF [TMK] = -999 THEN NULL ELSE [TMK] END`), rename, calc `[precip_mm] >= 1` |

## Join, features, aggregate

| # | Rule | Python function | Tableau Prep step |
|---|---|---|---|
| J1 | daily_counts **left join** sites on `site_id`, then **left join** weather on `date` (rows must not change) | `build_model_table` | **Join steps** (left), check row count stays the same |
| J2 | Calendar features: `weekday`, `is_weekend`, `is_holiday` (Baden-Württemberg public holidays), `month` | `add_calendar_features` | **Clean step** calcs: `DATENAME('weekday',[date])`, `DATEPART('weekday',[date]) IN (1,7)`; holidays via a small holiday CSV joined on date |
| J3 | Weekly totals per site (sum of counts, number of valid days, mean temperature, total rain); **total is NULL if no valid day** | `aggregate_weekly` | **Aggregate step** by `site_id`, ISO week |

## Script step for B7 + B8 (Tableau Prep)

Rules B7 and B8 compare a row with the rows before it, which is hard to build with normal Prep steps. Use a **Script step** that calls the same Python functions, so both tools give exactly the same result. This also shows "cleaning functions inside Tableau Prep's Script step".

Needs TabPy: `pip install tabpy` → run `tabpy` → in Prep: Help → Settings and Performance → Manage Analytics Extension Connection → TabPy, localhost, port 9004.

```python
# tableau/prep_script.py  — Script step, function name: flag_rules
import sys
sys.path.insert(0, r"C:\path\to\repo\src")     # change to your repo path
import cleaning as c

def flag_rules(df):
    out, _ = c.flag_outages.raw(df)
    out, _ = c.flag_outliers.raw(out)
    return out

def get_output_schema():
    import pandas as pd
    return pd.DataFrame({
        "site_id": prep_string(), "date": prep_date(),
        "bikes_in": prep_decimal(), "bikes_out": prep_decimal(), "bikes_total": prep_decimal(),
        "is_outage": prep_bool(), "is_zero": prep_bool(), "is_outlier": prep_bool(),
    })
```

## Change log of the rules

| Date | Who | Change |
|---|---|---|
| 3 Nov 2026 | Jasmeet | First version, from profiling report |
| 5 Nov 2026 | Keshav (found), Jasmeet (fixed) | J3: weekly `bikes_total` is NULL when `valid_days` = 0 (was 0). Found in governance review, test added |
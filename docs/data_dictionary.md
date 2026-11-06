# Data dictionary

Data product: **Bike counts + weather, Heidelberg and Mannheim, 2025** (Group 07).
Files: `data/processed/2025/` · created by `src/cleaning.py` (rules in `docs/cleaning_rules.md`).
Written by: Keshav Sain · 5 Nov 2026

**Conventions**
- Dates are `YYYY-MM-DD`, local time Europe/Berlin.
- Empty cell = **NULL** (no valid value). NULL is never the same as 0.
- Booleans are `True` / `False`.
- Keys: `site_id` links counts to sites; `date` links counts to weather.

---

## 1. `sites.csv` — one row per counter site (30 rows)

| Column | Type | Meaning | Unit | Example |
|---|---|---|---|---|
| `site_id` | integer | Unique ID of the counter site (from Eco-Counter). **Primary key** | – | 100012161 |
| `site_name` | text | Name of the counting location | – | Plöck |
| `city` | text | City of the site: Heidelberg or Mannheim | – | Heidelberg |
| `latitude` | decimal | Latitude of the site (median of all reported positions) | degrees (WGS 84) | 49.40913 |
| `longitude` | decimal | Longitude of the site (median of all reported positions) | degrees (WGS 84) | 8.698543 |
| `counter_serial` | text | Serial number of the counting device | – | Y2H22032496 |
| `first_date` | date | First day with data in 2025 | date | 2025-01-01 |
| `last_date` | date | Last day with data in 2025 | date | 2025-12-31 |

## 2. `daily_counts.csv` — one row per site per day (10,874 rows)

Primary key: `site_id` + `date`.

| Column | Type | Meaning | Unit | Example |
|---|---|---|---|---|
| `site_id` | integer | Counter site. **Foreign key** → `sites.site_id` | – | 100012161 |
| `date` | date | Day of the count | date | 2025-01-01 |
| `bikes_in` | whole number | Bikes counted in direction "in". NULL if the counter has no direction or the day is missing / an outage | bikes per day | 385 |
| `bikes_out` | whole number | Bikes counted in direction "out". NULL as for `bikes_in` | bikes per day | 453 |
| `bikes_total` | whole number | All bikes counted that day (both directions). NULL if the day is missing or an outage | bikes per day | 838 |
| `is_missing` | boolean | `True` = day had no data and was added by rule B9 (count is NULL) | – | False |
| `is_outage` | boolean | `True` = part of ≥ 3 zero days in a row → sensor outage, count set to NULL (rule B7) | – | False |
| `is_zero` | boolean | `True` = single zero day (fewer than 3 in a row); value 0 kept (rule B7) | – | False |
| `is_outlier` | boolean | `True` = count above Q3 + 3 × IQR of that site; value kept (rule B8) | – | False |

## 3. `weather_daily.csv` — one row per day (365 rows)

Source: DWD station 05906 Mannheim (used for both cities). Primary key: `date`.

| Column | Type | Meaning | Unit | Example |
|---|---|---|---|---|
| `date` | date | Day of the measurement | date | 2025-01-01 |
| `temp_mean_c` | decimal | Daily mean air temperature (DWD `TMK`) | °C | 3.8 |
| `temp_max_c` | decimal | Daily maximum air temperature (DWD `TXK`) | °C | 9.0 |
| `temp_min_c` | decimal | Daily minimum air temperature (DWD `TNK`) | °C | -0.9 |
| `precip_mm` | decimal | Daily precipitation (DWD `RSK`) | mm | 1.0 |
| `snow_depth_cm` | whole number | Snow depth (DWD `SHK_TAG`) | cm | 0 |
| `sunshine_h` | decimal | Sunshine duration (DWD `SDK`) | hours | 4.5 |
| `wind_mean_ms` | decimal | Daily mean wind speed (DWD `FM`). NULL on 3 days (DWD value -999) | m/s | 4.7 |
| `humidity_pct` | decimal | Daily mean relative humidity (DWD `UPM`). NULL on 3 days (DWD value -999) | % | 69.0 |
| `is_rainy` | boolean | `True` = precipitation ≥ 1.0 mm (rule W3) | – | True |

## 4. `model_table.csv` — AI-ready table (10,874 rows)

`daily_counts` + `site_name`, `city` from `sites` + all columns of `weather_daily` (joined on `date`) + the calendar columns below (rule J1, J2). Same rows as `daily_counts`.

| Column | Type | Meaning | Unit | Example |
|---|---|---|---|---|
| `weekday` | text | Name of the weekday | – | Wednesday |
| `is_weekend` | boolean | `True` = Saturday or Sunday | – | False |
| `is_holiday` | boolean | `True` = public holiday in Baden-Württemberg (Python package `holidays`) | – | True |
| `month` | whole number | Month of the year (1–12) | – | 1 |

All other columns: see tables 1–3.

## 5. `weekly_counts.csv` — one row per site per ISO week (1,580 rows)

Primary key: `site_id` + `iso_year` + `iso_week` (rule J3).

| Column | Type | Meaning | Unit | Example |
|---|---|---|---|---|
| `site_id`, `site_name`, `city` | – | See `sites.csv` | – | 100012161, Plöck, Heidelberg |
| `iso_year` | whole number | ISO year of the week. 29–31 Dec 2025 belong to ISO week 1 of **2026** | – | 2025 |
| `iso_week` | whole number | ISO week number (1–52) | – | 1 |
| `bikes_total` | whole number | Sum of valid daily counts in the week (NULL days are skipped). **NULL if `valid_days` = 0** (rule J3, fixed 5 Nov) | bikes per week | 7181 |
| `valid_days` | whole number | Number of days with a valid count (0–7). Use it to judge a weekly total | days | 5 |
| `temp_mean_c` | decimal | Mean of the daily mean temperatures | °C | 2.88 |
| `precip_mm` | decimal | Total precipitation in the week | mm | 22.1 |

---

**Note for AI use:** filter or weight by `is_missing`, `is_outage` and `valid_days`. A NULL count means "unknown", never "no bikes".

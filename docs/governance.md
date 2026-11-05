# Data governance

Data product: **Bike counts + weather, Heidelberg and Mannheim, 2025** (Group 07).
Written by: Keshav Sain (FAIR and governance lead) · 5 Nov 2026

Governance answers three questions: **who is responsible**, **where the data comes from and what happened to it**, and **what can go wrong when an AI model uses it**.

---

## 1. Roles

| Role | Who | Responsibility |
|---|---|---|
| **Data owner (source)** | MobiData BW / NVBW (bike counts); Deutscher Wetterdienst (weather) | Own the original data and set the licence. We do not change their files (`data/raw/` is never edited). |
| **Data owner (product)** | Group 07, represented by Jasmeet Kaur (group lead) | Decides what the cleaned data product contains, approves changes to `main` (Pull Requests). |
| **Data steward** | Keshav Sain | Keeps the metadata, data dictionary, FAIR score and licence attribution correct and up to date; checks that every change is documented. |
| **Data custodians / engineers** | Jasmeet Kaur (download, architecture), Shashank Kenkere Sridhar (Python pipeline, tests), Vivek Sawant (Tableau Prep flow) | Build and run the pipeline; make sure Python and Tableau Prep give the same result. |
| **Data quality analyst** | Yash Chinnannavar | Measures quality KPIs before and after cleaning; reports issues. |
| **Data users** | Mobility departments of Heidelberg and Mannheim (bike lane planning, winter maintenance, events); MobiData BW; analysts training a forecasting model | Use the data within the licence, cite the sources, respect the known limitations (section 4). |

**Decision rules**
- Cleaning rules are changed only in `docs/cleaning_rules.md`, agreed by the whole team, and recorded in its change log.
- Every change goes through a branch and a Pull Request; the group lead merges into `main`.
- A NULL value is never replaced with 0 without a written rule.

---

## 2. Lineage (where the data comes from and what happened to it)

```
MobiData BW (12 monthly .csv.gz, 2025)      DWD station 05906 Mannheim (hist + recent .zip)
              │                                           │
              └──────────── src/download.py ──────────────┘
                     (URLs, file sizes, SHA-256 in data/raw/download_log.json)
                                     │
                              data/raw/   ← never edited
                                     │
          cleaning rules B1–B10, W1–W3, J1–J3 (docs/cleaning_rules.md)
          run in BOTH  src/cleaning.py  and  tableau/flow.tflx
                                     │
                  docs/cleaning_log_2025.md (rows before → after per step)
                                     │
                          data/processed/2025/
     sites.csv · daily_counts.csv · weather_daily.csv · model_table.csv · weekly_counts.csv
                (row counts + SHA-256 checksums in docs/metadata.json)
                                     │
                     AI model (forecast daily bike counts per site)
```

| Stage | Rows | Evidence |
|---|---|---|
| Raw bike data, all of Baden-Württemberg | 57,341 | `docs/cleaning_log_2025.md`, step 1 |
| After city filter (Heidelberg + Mannheim) | 10,839 | step 1 |
| After adding missing site-days as NULL | 10,874 | step 9 |
| Raw weather rows (1781–2025, two files) | 34,884 | step 10 |
| Weather 2025 after cleaning | 365 | steps 10–12 |
| Final model table | 10,874 | step 13 (join did not add or lose rows) |

**Reproducibility:** `python src/download.py` then `python src/cleaning.py` rebuilds every file. The SHA-256 checksums in the cleaning log prove a re-run gives the same output. `pytest` checks the rules (no duplicates, no -999, valid dates).

---

## 3. Licences and attribution

| Source | Licence | What we must do |
|---|---|---|
| MobiData BW / NVBW bike counts | Datenlizenz Deutschland – Namensnennung 2.0 | Name the source and licence wherever the data or results are shown |
| DWD weather | CC BY 4.0 | Name DWD and the licence |

Attribution text (README, slides, report): *Bicycle count data: MobiData BW / NVBW, Datenlizenz Deutschland – Namensnennung 2.0. Weather data: Deutscher Wetterdienst (DWD), CC BY 4.0.*

**Privacy:** counters record only the number of bikes per day. No people, images or devices are identified, so there is no personal data (GDPR not affected).

---

## 4. AI risks and how we handle them

| # | Risk | Why it matters for a model | What we did / recommend |
|---|---|---|---|
| 1 | **Missing data read as zero** | A model would learn "no bikes" on days the sensor was off | 35 missing days and 77 outage days are NULL with flags `is_missing`, `is_outage`. Users must drop or mask them. |
| 2 | **Weekly total of 0 that means "unknown"** | 10 weeks in `weekly_counts.csv` have `valid_days` = 0 and show `bikes_total` = 0 | Use `valid_days`; ignore weeks with 0 valid days. Possible fix: write NULL instead of 0 (future work). |
| 3 | **Outliers** | 10 extreme days (events or sensor errors) can distort training | Flagged `is_outlier`, value kept. The user decides: keep for events, remove for "normal day" models. |
| 4 | **One weather station for two cities** | Heidelberg weather may differ from Mannheim (about 20 km) | Documented in metadata. Possible improvement: add a Heidelberg station. |
| 5 | **Short history (one year)** | Only one winter and one summer; seasonal effects are weakly learned | Train on 2025, test on 2026 data (pipeline can re-run on a new month, task 3.9). |
| 6 | **Counter setup can change** | Operator may move or reconfigure a counter without notice → sudden jump in counts | `counter_serial`, `first_date`, `last_date` in `sites.csv`; check for breaks before training. |
| 7 | **Missing direction** | `bikes_in` / `bikes_out` empty for 2 sites | Use `bikes_total` as the target. |
| 8 | **Bias between sites** | Busy city-centre sites dominate the totals | Train per site or normalise counts per site. |
| 9 | **Misuse of forecasts** | A forecast is not a measurement; wrong decisions on lane closures | Report forecast error and the data limitations together with any forecast. |

---

## 5. Data quality checks (before → after)

See `docs/profiling_report.md` (before) and `docs/cleaning_log_2025.md` (after). Main change: type conformity 0 % → 100 %; missing and outage days are now flagged instead of hidden.

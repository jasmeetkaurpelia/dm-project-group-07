# Bike Counts + Weather — FAIR, AI-ready Data Product

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24058368.svg)](https://doi.org/10.5281/zenodo.24058368)

**Data Management — Group Project** · SRH University of Applied Sciences Heidelberg · Prof. Dr. Mehrdad Jalali

> **Key question:** Can this data be trusted, reused and fed into an AI model — and how do we prove it?

## Problem statement

How strongly do weather and calendar effects (weekday, holidays, semester) drive daily bicycle traffic in **Heidelberg and Mannheim** — and can this data be trusted enough to train a model that forecasts daily bike counts per counting site?

**For whom:** the cities' mobility departments (bike lane planning, winter maintenance, events) and the regional open-data platform MobiData BW.

## Team

| Name | Role | Part |
|---|---|---|
| Jasmeet Kaur | Group lead + Data Engineer | Dataset, architecture, conclusion, final ZIP |
| Yash Chinnannavar | Data Quality Analyst | Profiling (quality KPIs, issues) |
| Vivek Sawant | Tableau Prep lead | Cleaning and transformation flow |
| Shashank Kenkere Sridhar | Pipeline Engineer | Python cleaning functions, tests |
| Keshav Sain | FAIR and Governance lead | FAIR score, metadata, data dictionary, governance |

Task tracking: see **[TASKS.md](TASKS.md)**.

## Data sources

| Table | Source | Licence |
|---|---|---|
| Counter sites | [MobiData BW — Eco-Counter bike counts](https://mobidata-bw.de/en/dataset/eco-counter-fahrradzahler) | [Datenlizenz Deutschland – Namensnennung 2.0](https://www.govdata.de/dl-de/by-2-0) |
| Daily bike counts | MobiData BW, monthly files `fahrradzaehler_tageswerten_{yyyymm}.csv.gz` | Datenlizenz Deutschland – Namensnennung 2.0 |
| Daily weather | [Deutscher Wetterdienst (DWD), Climate Data Center](https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/daily/kl/) | [CC BY 4.0](https://opendata.dwd.de/climate_environment/CDC/Terms_of_use.pdf) |

**Scope:** Heidelberg + Mannheim · one year (2025) · daily values.
**Download date:** 2 Nov 2026 (run `python src/download.py`, log in `data/raw/download_log.json`)
**Size:** 10,839 rows for Heidelberg + Mannheim (30 counter sites, 2025), out of 57,341 rows for all of Baden-Württemberg. After cleaning: 10,874 rows (35 missing days added as NULL).
**Weather:** DWD station 05906 Mannheim, daily values, historical file (to 31 Dec 2025) + recent file (from 1 May 2025).

**Attribution:** Bicycle count data: MobiData BW / NVBW, Datenlizenz Deutschland – Namensnennung 2.0. Weather data: Deutscher Wetterdienst (DWD), CC BY 4.0.

## Repository structure

```
├── README.md              this file
├── TASKS.md               task tracker (write your name when done)
├── requirements.txt       Python packages
├── data/
│   ├── raw/               original downloads — never edit
│   └── processed/         cleaned output
├── notebooks/             effect_analysis.ipynb (weather + calendar effects, answers the problem statement)
├── src/                   download.py, profiling.py, cleaning.py, quality_kpis.py
├── tests/                 test_cleaning.py
├── tableau/               flow.tflx (packaged flow), bike_cleaning_pipeline.tfl, prep_script.py (Script step)
├── docs/                  metadata.json, data_dictionary.md, cleaning_rules.md,
│                          cleaning_log_2025.md, fair_score.md, governance.md,
│                          quality_before_after.md, profiling_report.md, architecture.png
├── slides/
└── report/
```

## How to run

```bash
git clone https://github.com/jasmeetkaurpelia/dm-project-group-07.git
cd dm-project-group-07
python -m venv .venv
# Windows: .venv\Scripts\activate   |   Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt

python src/download.py       # downloads raw data into data/raw/
python src/profiling.py      # profiles the raw data -> docs/profiling_report.md
python src/cleaning.py       # writes cleaned data into data/processed/2025/ + docs/cleaning_log_2025.md
python src/quality_kpis.py   # quality KPIs before vs after -> docs/quality_before_after.md
pytest                       # runs the tests
```

Re-run on a new month (shows the pipeline is reproducible, output goes to `data/processed/2026-01/`):

```bash
python src/download.py --year 2026 --months 1
python src/cleaning.py --year 2026 --months 1
```

### Tableau Prep

The flow `tableau/flow.tflx` is packaged (data included). Its Script step calls the same Python functions as `cleaning.py`, through TabPy.

1. Start TabPy **from the repo folder** so it can import `src/cleaning.py` (Windows PowerShell shown):
   ```powershell
   pip install tabpy pandas numpy holidays
   cd <path-to>/dm-project-group-07
   $env:PYTHONPATH = "$PWD\src"          # Mac/Linux: export PYTHONPATH=$PWD/src
   tabpy                                 # answer y; leave this window open
   ```
2. In Tableau Prep Builder: Help → Settings and Performance → Manage Analytics Extension Connection → TabPy, `localhost`, port `9004`.
3. Open `tableau/flow.tflx`. Point the 3 Output steps to your own `data/processed/` folder, then **Run**.

## Expected results (check your run)

Python (`data/processed/2025/`) and Tableau (`data/processed/*.hyper`) must give the same numbers:

| Check | Result |
|---|---|
| Rows Heidelberg + Mannheim (raw → filtered) | 57,341 → 10,839 |
| Missing site-days added as NULL rows (`is_missing`) | 35 → **10,874 daily rows** |
| Sensor outages (≥ 3 zero days) set to NULL (`is_outage`) | 77 |
| Single zero days kept (`is_zero`) / outliers flagged (`is_outlier`) | 20 / 10 |
| Weather days 2025 (245 duplicate days removed) | 365 |
| Weekly rows (site × Monday week) | 1,580 |
| Tests (`pytest`) | 15 passed |

Checksums of every output file are in `docs/cleaning_log_2025.md`.

## How we work

1. **Never edit `data/raw/`.** All changes happen in Tableau Prep or Python and are written in `docs/cleaning_log_2025.md`.
2. **One branch per person** (e.g. `yash-profiling`). Open a Pull Request; `main` is protected (no direct pushes, no force pushes).
3. **Same rules in both tools:** Tableau Prep and Python use the rules in `docs/cleaning_rules.md`, so the row counts must match.
4. **Show numbers:** rows before → after, % missing before → after, FAIR score before → after.
5. **Do not upload large files.** Keep raw data out of Git if it is bigger than 50 MB; `download.py` can rebuild it.

## How to cite

Kaur, J., Chinnannavar, Y., Sawant, V., Kenkere Sridhar, S., & Sain, K. (2026). *Bike counts and weather, Heidelberg + Mannheim 2025: a FAIR, AI-ready data product* [Data set]. Zenodo. https://doi.org/10.5281/zenodo.24058368

Please also credit the sources: MobiData BW / NVBW (Datenlizenz Deutschland – Namensnennung 2.0) and Deutscher Wetterdienst (CC BY 4.0).
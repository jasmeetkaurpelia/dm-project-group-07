# Bike Counts + Weather — FAIR, AI-ready Data Product

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
**Size:** 10,839 rows for Heidelberg + Mannheim (30 counter sites, 2025), out of 57,341 rows for all of Baden-Württemberg.
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
├── notebooks/             (optional demos)
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

Tableau Prep: open `tableau/flow.tflx` in Tableau Prep Builder. The Script step needs TabPy (`pip install tabpy`, then run `tabpy`). Before running, point the two Output steps to your own `data/processed/` folder.

## How we work

1. **Never edit `data/raw/`.** All changes happen in Tableau Prep or Python and are written in `docs/cleaning_log_2025.md`.
2. **One branch per person** (e.g. `yash-profiling`). Open a Pull Request; `main` is protected (no direct pushes, no force pushes).
3. **Same rules in both tools:** Tableau Prep and Python use the rules in `docs/cleaning_rules.md`, so the row counts must match.
4. **Show numbers:** rows before → after, % missing before → after, FAIR score before → after.
5. **Do not upload large files.** Keep raw data out of Git if it is bigger than 50 MB; `download.py` can rebuild it.
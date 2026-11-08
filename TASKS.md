# Task Tracker

**How to use:**
- **Your own task:** when done, change ⬜ to ✅ and write the date (e.g. `3 Nov`) in the **Date** column.
- **Shared task** (several names): tick only your own name. Write the date **only when everyone is ✅**.
- Commit with a message like `done: task 2.3`. Always `git pull` before you start and before you push.

Status: ⬜ to do · 🔄 in progress · ✅ done · ⚠️ blocked (write the reason in Notes)

**Timeline:** Day 1 = Mon 2 Nov · Day 7 = Sun 8 Nov · Presentation: **Mon 9 Nov** · Report due: 1 week after the presentation

---

## Phase 0 — Setup (Day 1) · must be done first

| # | Task | Owner | Status | Date |
|---|---|---|---|---|
| 0.1 | Create GitHub repo, add README, TASKS, requirements | Jasmeet | ✅ | 2 Nov |
| 0.2 | Invite all 4 teammates as collaborators | Jasmeet | ✅ | 2 Nov |
| 0.3 | Create folders: `data/raw`, `data/processed`, `notebooks`, `src`, `tests`, `tableau`, `docs`, `slides`, `report` | Jasmeet | ✅ | 2 Nov |
| 0.4 | Clone repo + `pip install -r requirements.txt` | Everyone | Jasmeet ✅, Yash ✅, Vivek ✅, Shashank ✅, Keshav ✅ | |
| 0.5 | Install Tableau Prep Builder (free student licence) | Everyone | Jasmeet ✅, Yash ✅, Vivek ✅, Shashank ✅, Keshav ✅ | |
| 0.6 | Share SRH slide template in `slides/` | Jasmeet | ✅ | |

## Phase 1 — Get the data (Day 1)

| # | Task | Owner | Status | Date |
|---|---|---|---|---|
| 1.1 | Write `src/download.py`: download 12 monthly files for 2025 (`fahrradzaehler_tageswerten_2025MM.csv.gz`) and unzip | Jasmeet | ✅ | 2 Nov |
| 1.2 | Find the Mannheim station ID in the DWD station list and download its daily `kl` file | Jasmeet | ✅ | 2 Nov |
| 1.3 | Check rows for Heidelberg + Mannheim (must be ≥ 1,000) and write the number in the README | Jasmeet | ✅ | 2 Nov |
| 1.4 | Write the download date + file names in the README | Jasmeet | ✅ | 2 Nov |

## Phase 2 — Understand the data (Day 2)

| # | Task | Owner | Status | Date |
|---|---|---|---|---|
| 2.1 | Profiling: rows, columns, data types, % missing, duplicates, min/max (`src/profiling.py`) | Jasmeet + Yash | Jasmeet ✅, Yash ✅ | |
| 2.2 | Find the main issues: zero days (outages), -999 values, text-typed numbers, duplicate dates, IN/OUT/ALL double count | Jasmeet + Yash | Jasmeet ✅, Yash ✅ | |
| 2.3 | Calculate the quality KPIs on raw data (completeness, validity, uniqueness, consistency) | Jasmeet + Yash | Jasmeet ✅, Yash ✅ | |
| 2.4 | FAIR score of the original dataset (F, A, I, R, each scored) → `docs/fair_score.md` | Jasmeet + Keshav | Jasmeet ✅, Keshav ✅ |5 Nov |
| 2.5 | Architecture sketch: source → raw → Tableau Prep / Python → processed → AI model (ETL) → `docs/architecture.png` | Jasmeet | ✅ | 3 Nov |
| 2.6 | Agree on the cleaning rules → `docs/cleaning_rules.md` (draft ready: read it and tick your name) | Everyone | Jasmeet ✅, Yash ✅, Vivek ✅, Shashank ✅, Keshav ✅ |  |

> ⚠️ Phase 3 starts only after 2.6 is done.

## Phase 3 — Build (Day 3–4)

| # | Task | Owner | Status | Date |
|---|---|---|---|---|
| 3.1 | Tableau Prep: input + union of 12 months | Vivek | ✅ | 6 Nov |
| 3.2 | Tableau Prep: clean steps (types, filter HD + MA, fix -999, duplicates, outage days) | Vivek | ✅ | 6 Nov |
| 3.3 | Tableau Prep: split into sites table + daily counts table, join weather on date | Vivek | ✅ | 6 Nov |
| 3.4 | Tableau Prep: calculated fields (weekday, weekend, holiday, rain yes/no) | Vivek | ✅ | 6 Nov |
| 3.5 | Tableau Prep: aggregate (per site per week) + output, note rows before → after per step | Vivek | ✅ | 6 Nov |
| 3.6 | Python: one function per cleaning rule in `src/cleaning.py` | Shashank | Jasmeet ✅ (written), Shashank review ⬜ | |
| 3.7 | Python: `run_pipeline()` that calls all functions in order | Shashank | Jasmeet ✅ (written), Shashank review ⬜ | |
| 3.8 | Python: tests in `tests/test_cleaning.py` (no duplicates, no -999, valid dates) | Shashank | ✅ 15 tests pass (10 Jasmeet, 5 Yash in PR #7) | 8 Nov |
| 3.9 | Python: re-run on a new month (e.g. Jan 2026) and show the same result | Shashank | ✅ | |
| 3.10 | Compare row counts between Tableau and Python (must match) | Vivek + Shashank | ✅ Tableau = Python: 10,874 rows, 35 missing days, 77 outages, 10 outliers, 1,580 weekly rows | 8 Nov |
| 3.11 | Data dictionary → `docs/data_dictionary.md` (column, type, meaning, unit, example) | Keshav | ✅ | 5 Nov |
| 3.12 | Metadata record → `docs/metadata.json` (title, source, licence, date, creator, keywords) | Keshav | ✅ | 5 Nov |
| 3.13 | Governance: roles (owner, steward, users), lineage, AI risks | Keshav | ✅ | 5 Nov |
| 3.14 | Cleaning log → `docs/cleaning_log_2025.md` (written by `cleaning.py`) | Vivek + Shashank | ✅ written by `cleaning.py` on every run (rows before → after per rule) | 8 Nov |
| 3.15 | Quality KPIs and FAIR score after cleaning (before vs after) | Jasmeet · review: Yash + Keshav  | Jasmeet ✅ (`docs/quality_before_after.md`): Yash review ✅, Keshav ✅ (FAIR after)| |

## Phase 4 — Presentation (Day 5–7)

| # | Task | Owner | Status | Date |
|---|---|---|---|---|
| 4.1 | Slides 1–2: dataset, problem statement, architecture | Jasmeet | ✅ | |
| 4.2 | Slide 3: FAIR | Keshav | ✅ | |
| 4.3 | Slides 4–5: profiling | Yash | ✅ | |
| 4.4 | Slides 6–11: Tableau Prep (full flow + main steps) | Vivek | ✅ | |
| 4.5 | Slides 12–13: reproducible pipeline | Shashank | ✅ | |
| 4.6 | Slide 14: governance | Keshav | ✅ | |
| 4.7 | Slide 15: conclusion (answer the problem statement + lessons learned) | Jasmeet | ✅ | |
| 4.8 | Merge all slides into one deck (SRH template only) | Jasmeet | ⬜ | |
| 4.9 | Rehearsal 1 with timer (target 14:30 min) | Everyone | Jasmeet ⬜, Yash ✅, Vivek ⬜, Shashank ⬜, Keshav ⬜ | |
| 4.10 | Rehearsal 2 + list of likely questions and answers | Everyone | Jasmeet ⬜, Yash ✅, Vivek ⬜, Shashank ⬜, Keshav ⬜ | |
| 4.11 | Export `tableau/flow.tflx` (packaged flow) | Vivek | ✅ packaged flow with data + Script, missing-days fix by Jasmeet | 8 Nov |

## Phase 5 — Report + Submission (after the presentation)

| # | Task | Owner | Status | Date |
|---|---|---|---|---|
| 5.1 | Write own report section (~1.5 pages) | Everyone | Jasmeet ⬜, Yash ⬜, Vivek ⬜, Shashank ⬜, Keshav ⬜ | |
| 5.2 | Reflection: what we could not fix + who did what | Jasmeet | ⬜ | |
| 5.3 | Appendix: metadata record, cleaning log, data dictionary, GitHub link | Keshav | ⬜ | |
| 5.4 | Merge and export report as PDF | Jasmeet | ⬜ | |
| 5.5 | Upload `DM_Project_Group07.zip` to Moodle (slides, report PDF, .tflx, code, GitHub link) | Jasmeet | ⬜ | |

---

## Notes / blockers

| Date | Who | Note |
|---|---|---|
| 2 Nov | Jasmeet | Raw data downloaded: 10,839 rows for Heidelberg + Mannheim (30 counter sites, 2025); DWD station 05906 Mannheim |
| 3 Nov | Jasmeet | Profiling report in `docs/profiling_report.md`. Yash: please review and add your findings |
| 3 Nov | Jasmeet | Draft FAIR score in `docs/fair_score.md` (18/30 original). Keshav: please review the scores |
| 3 Nov | Jasmeet | Draft `src/cleaning.py`, `tests/test_cleaning.py` and `docs/cleaning_rules.md` uploaded early. Shashank: please review and run `pytest` after 2.6 is agreed |
| 5 Nov | Keshav  | FAIR review done (18/30 confirmed). New: `docs/data_dictionary.md`, `docs/metadata.json`, `docs/governance.md` (PR #1). Yash: ready to do 3.15 together | 
| 5 Nov | Jasmeet | Merged PR #1 (Keshav: FAIR review, data dictionary, metadata, governance). His review found a bug: weekly total showed 0 instead of NULL; fixed in `cleaning.py`, 10 tests pass |
| 5 Nov | Jasmeet | Quality KPIs before vs after ready (`docs/quality_before_after.md`). Yash: please review |
| 6 Nov | Keshav  | FAIR after cleaning: 27/30 (90 %), up from 18/30; 29/30 only with a Zenodo DOI (F1, F4). Updated data dictionary, metadata (new weekly checksum) and governance for the J3 weekly NULL fix |
| 6 Nov | Jasmeet | Merged PR #3 + #4 (Keshav: FAIR after 27/30, J3 docs, slides) and PR #2 (Vivek: Tableau Prep flow, TabPy Script step) |
| 6 Nov | Jasmeet | Check 3.10, Tableau vs Python: match on 10,839 rows, 30 sites, 77 outages, 20 single zero days, 10 outliers. Still different: B9 missing days not added (10,839 vs 10,874), weekly 1,577 vs 1,580 rows without valid_days, no separate sites/weather outputs. Vivek: follow-up PR |
| 7 Nov | Jasmeet | Full re-run on a second machine (Linux, other pandas version): 10/10 tests pass, same row counts, 4 of 5 outputs byte-identical. sites.csv differed in the 15th decimal of 3 coordinates → coordinates rounded to 6 decimals (~10 cm), now identical everywhere |
| 7 Nov | Jasmeet | Tableau flow review sent to Vivek: rain threshold 0.1 → 1 mm (132 vs 94 rainy days), -999 cleaned columns not kept, stray ``` in 2 formulas, B9 missing days, sites output + valid_days missing |
| 7 Nov | Jasmeet | Effect analysis on model_table (median of 29 sites): holiday −52 %, weekend −40 %, cold −35 %, heavy rain −23 %, rain −14 %; R² 0.57 (temp, rain, weekend, holiday). Found level shift at B38. RI. AUS (×130 from Sept) → documented in metadata + governance risk 10 |
| 8 Nov | Jasmeet | 3.10 done: Tableau now adds the 35 missing site-days (New Rows calendar per site + left join), weekly totals use Monday weeks like Python (1,580), weekend check no longer depends on the computer's settings. Tableau = Python on all row counts |
| 8 Nov | Yash | Profiling re-run with 'na' counted as missing (PR #6): 12,225 'na' cells, 4 inconsistent site names. 5 new tests (PR #7): 'na' → NULL, Berlin date, outliers per site, join keeps row count, duplicate site key stops the join |
| 8 Nov | Shashank | Profiling and quality chart re-run (PR #8), numbers unchanged |
| 8 Nov | Jasmeet | Merged PR #6, #7, #8. Removed a module-level `pytest.skip` (pytest failed on a fresh clone without raw data). 15 tests pass. Fresh clone + re-run gives the same processed files and cleaning log |
| 8 Nov | Jasmeet | Tableau Script step on a new laptop: TabPy must be started from the repo with `PYTHONPATH=src`, otherwise "No module named cleaning"; TabPy needs pandas, numpy, holidays. Output paths set to `data/processed/`. Steps written in README |
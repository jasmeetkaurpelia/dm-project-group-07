# Task Tracker

**How to use:** when you finish a task, change ⬜ to ✅ and write **your name + date** in the "Done by" column. Commit with a message like `done: task 2.3`.

Status: ⬜ to do · 🔄 in progress · ✅ done · ⚠️ blocked (write the reason in Notes)

**Timeline:** Day 1 = Mon 2 Nov · Day 7 = Sun 8 Nov · Presentation: **\_\_\_\_** · Report due: 1 week after the presentation

---

## Phase 0 — Setup (Day 1) · must be done first

| #   | Task                                                                                                             | Owner    | Status                                                | Done by (name + date) |
| --- | ---------------------------------------------------------------------------------------------------------------- | -------- | ----------------------------------------------------- | --------------------- |
| 0.1 | Create GitHub repo, add README, TASKS, requirements                                                              | Jasmeet  | ✅                                                    |                       |
| 0.2 | Invite all 4 teammates as collaborators                                                                          | Jasmeet  | ✅                                                    |                       |
| 0.3 | Create folders: `data/raw`, `data/processed`, `notebooks`, `src`, `tests`, `tableau`, `docs`, `slides`, `report` | Jasmeet  | ✅                                                    |                       |
| 0.4 | Clone repo + `pip install -r requirements.txt`                                                                   | Everyone | Jasmeet ✅, Yash ⬜, Vivek ✅, Shashank ⬜, Keshav ⬜ |     
|
| 0.5 | Install Tableau Prep Builder (free student licence)                                                              | Everyone | Jasmeet ✅, Yash ⬜, Vivek ✅, Shashank ⬜, Keshav ⬜ |                      |
| 0.6 | Share SRH slide template in `slides/`                                                                            | Jasmeet  | ⬜                                                    |                       |

## Phase 1 — Get the data (Day 1)

| #   | Task                                                                                                               | Owner   | Status | Done by (name + date) |
| --- | ------------------------------------------------------------------------------------------------------------------ | ------- | ------ | --------------------- |
| 1.1 | Write `src/download.py`: download 12 monthly files for 2025 (`fahrradzaehler_tageswerten_2025MM.csv.gz`) and unzip | Jasmeet | ⬜     |                       |
| 1.2 | Find the Mannheim station ID in the DWD station list and download its daily `kl` file                              | Jasmeet | ⬜     |                       |
| 1.3 | Check rows for Heidelberg + Mannheim (must be ≥ 1,000) and write the number in the README                          | Jasmeet | ⬜     |                       |
| 1.4 | Write the download date + file names in the README                                                                 | Jasmeet | ⬜     |                       |

## Phase 2 — Understand the data (Day 2)

| #   | Task                                                                                                                 | Owner    | Status                                                | Done by (name + date) |
| --- | -------------------------------------------------------------------------------------------------------------------- | -------- | ----------------------------------------------------- | --------------------- |
| 2.1 | Profiling notebook: rows, columns, data types, % missing, duplicates, min/max                                        | Yash     | ⬜                                                    |                       |
| 2.2 | Find the main issues: zero days (outages), -999 values, text-typed numbers, duplicate dates, IN/OUT/ALL double count | Yash     | ⬜                                                    |                       |
| 2.3 | Calculate the quality KPIs on raw data (completeness, validity, uniqueness, consistency)                             | Yash     | ⬜                                                    |                       |
| 2.4 | FAIR score of the original dataset (F, A, I, R, each scored) → `docs/fair_score.md`                                  | Keshav   | ⬜                                                    |                       |
| 2.5 | Architecture sketch: source → raw → Tableau Prep / Python → processed → AI model (ETL)                               | Jasmeet  | ⬜                                                    |                       |
| 2.6 | **Team call (30 min):** agree on the cleaning rules → `docs/cleaning_rules.md`                                       | Everyone | Jasmeet ⬜, Yash ⬜, Vivek ⬜, Shashank ⬜, Keshav ⬜ |                       |

> ⚠️ Phase 3 starts only after 2.6 is done.

## Phase 3 — Build (Day 3–4)

| #    | Task                                                                                     | Owner            | Status | Done by (name + date) |
| ---- | ---------------------------------------------------------------------------------------- | ---------------- | ------ | --------------------- |
| 3.1  | Tableau Prep: input + union of 12 months                                                 | Vivek            | ⬜     |                       |
| 3.2  | Tableau Prep: clean steps (types, filter HD + MA, fix -999, duplicates, outage days)     | Vivek            | ⬜     |                       |
| 3.3  | Tableau Prep: split into sites table + daily counts table, join weather on date          | Vivek            | ⬜     |                       |
| 3.4  | Tableau Prep: calculated fields (weekday, weekend, holiday, rain yes/no)                 | Vivek            | ⬜     |                       |
| 3.5  | Tableau Prep: aggregate (per site per week) + output, note rows before → after per step  | Vivek            | ⬜     |                       |
| 3.6  | Python: one function per cleaning rule in `src/cleaning.py`                              | Shashank         | ⬜     |                       |
| 3.7  | Python: `run_pipeline()` that calls all functions in order                               | Shashank         | ⬜     |                       |
| 3.8  | Python: tests in `tests/test_cleaning.py` (no duplicates, no -999, valid dates)          | Shashank         | ⬜     |                       |
| 3.9  | Python: re-run on a new month (e.g. Jan 2026) and show the same result                   | Shashank         | ⬜     |                       |
| 3.10 | Compare row counts between Tableau and Python (must match)                               | Vivek + Shashank | ⬜     |                       |
| 3.11 | Data dictionary → `docs/data_dictionary.md` (column, type, meaning, unit, example)       | Keshav           | ⬜     |                       |
| 3.12 | Metadata record → `docs/metadata.json` (title, source, licence, date, creator, keywords) | Keshav           | ⬜     |                       |
| 3.13 | Governance: roles (owner, steward, users), lineage, AI risks                             | Keshav           | ⬜     |                       |
| 3.14 | Cleaning log → `docs/cleaning_log.md` (step, rule, rows before, rows after)              | Vivek + Shashank | ⬜     |                       |
| 3.15 | Quality KPIs and FAIR score after cleaning (before vs after)                             | Yash + Keshav    | ⬜     |                       |

## Phase 4 — Presentation (Day 5–7)

| #    | Task                                                                  | Owner    | Status | Done by (name + date) |
| ---- | --------------------------------------------------------------------- | -------- | ------ | --------------------- |
| 4.1  | Slides 1–2: dataset, problem statement, architecture                  | Jasmeet  | ⬜     |                       |
| 4.2  | Slide 3: FAIR                                                         | Keshav   | ⬜     |                       |
| 4.3  | Slides 4–5: profiling                                                 | Yash     | ⬜     |                       |
| 4.4  | Slides 6–11: Tableau Prep (full flow + main steps)                    | Vivek    | ⬜     |                       |
| 4.5  | Slides 12–13: reproducible pipeline                                   | Shashank | ⬜     |                       |
| 4.6  | Slide 14: governance                                                  | Keshav   | ⬜     |                       |
| 4.7  | Slide 15: conclusion (answer the problem statement + lessons learned) | Jasmeet  | ⬜     |                       |
| 4.8  | Merge all slides into one deck (SRH template only)                    | Jasmeet  | ⬜     |                       |
| 4.9  | Rehearsal 1 with timer (target 14:30 min)                             | Everyone | ⬜     |                       |
| 4.10 | Rehearsal 2 + list of likely questions and answers                    | Everyone | ⬜     |                       |
| 4.11 | Export `tableau/flow.tflx` (packaged flow)                            | Vivek    | ⬜     |                       |

## Phase 5 — Report + Submission (after the presentation)

| #   | Task                                                                                     | Owner    | Status                                                | Done by (name + date) |
| --- | ---------------------------------------------------------------------------------------- | -------- | ----------------------------------------------------- | --------------------- |
| 5.1 | Write own report section (~1.5 pages)                                                    | Everyone | Jasmeet ⬜, Yash ⬜, Vivek ⬜, Shashank ⬜, Keshav ⬜ |                       |
| 5.2 | Reflection: what we could not fix + who did what                                         | Jasmeet  | ⬜                                                    |                       |
| 5.3 | Appendix: metadata record, cleaning log, data dictionary, GitHub link                    | Keshav   | ⬜                                                    |                       |
| 5.4 | Merge and export report as PDF                                                           | Jasmeet  | ⬜                                                    |                       |
| 5.5 | Upload `DM_Project_Group07.zip` to Moodle (slides, report PDF, .tflx, code, GitHub link) | Jasmeet  | ⬜                                                    |                       |

---

## Notes / blockers

| Date | Who | Note |
| ---- | --- | ---- |
|      |     |      |

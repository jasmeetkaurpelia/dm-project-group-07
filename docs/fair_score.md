# FAIR score

Scored by: Jasmeet Kaur · 3 Nov 2026  · Reviewed by: Keshav Sain · 5 Nov 2026 · Method: the 15 FAIR sub-principles ([GO FAIR](https://www.go-fair.org/fair-principles/)), each scored **0 = not met, 1 = partly met, 2 = fully met**. Maximum 30 points.

Scored dataset: **MobiData BW — Gebündelte Daten Eco-Counter Fahrradzählstellen Baden-Württemberg** (bike counts, main table).
Evidence from the [dataset page](https://mobidata-bw.de/en/dataset/eco-counter-fahrradzahler), checked 2 Nov 2026.

## Summary

| | Original dataset | Our data product (target) |
|---|---|---|
| Findable | 6 / 8 | 8 / 8 |
| Accessible | 7 / 8 | 8 / 8 |
| Interoperable | 2 / 6 | 6 / 6 |
| Reusable | 3 / 8 | 7 / 8 |
| **Total** | **18 / 30 (60 %)** | **29 / 30 (97 %)** |

**Main finding:** the data is easy to find and download (F and A are strong). It is hard to reuse correctly (I and R are weak): every column is text, there are no descriptions or units, and nothing links the data to other datasets.

## Detailed score

| Principle | Question | Original | Evidence (original) | Ours | What we did |
|---|---|---|---|---|---|
| F1 | Unique, persistent identifier? | 1 | Portal ID (UUID) and URL, but no DOI | 2 | DOI via Zenodo release of the GitHub repo *(to do — else 1)* |
| F2 | Rich metadata? | 1 | Title, description, author, maintainer, tags, spatial area, licence; no column descriptions | 2 | `docs/metadata.json` + data dictionary |
| F3 | Metadata names the data's identifier? | 2 | Each resource has its own URL and ID in the metadata | 2 | File names + checksums in metadata and logs |
| F4 | Registered in a searchable resource? | 2 | Harvested into GovData; tagged for Mobilithek | 2 | GitHub + Zenodo *(to do)* |
| A1 | Retrievable by its identifier with a standard protocol? | 2 | HTTPS download, CKAN API | 2 | HTTPS (GitHub) |
| A1.1 | Protocol open and free? | 2 | HTTPS, no fee | 2 | HTTPS |
| A1.2 | Authentication where needed? | 2 | Not needed: no registration | 2 | Not needed |
| A2 | Metadata stays even if data goes? | 1 | Older resource marked "will be discontinued soon"; no promise to keep metadata | 2 | Metadata versioned in Git |
| I1 | Formal, shared language? | 1 | CSV + DCAT-AP.de metadata, but no schema for the data itself | 2 | Typed CSV + JSON metadata with column types |
| I2 | Shared vocabularies? | 1 | Licence as a DCAT-AP.de URI; column names are the vendor's own | 2 | English names with SI units (°C, mm, cm) |
| I3 | References to other data? | 0 | No link to weather, stations or other datasets | 2 | Keys `site_id` + `date` link counts, sites and DWD weather |
| R1 | Rich, accurate attributes? | 0 | Data dictionary lists only names, all typed "text"; no units or meaning | 2 | `docs/data_dictionary.md` (type, unit, meaning, example) |
| R1.1 | Clear licence? | 2 | Datenlizenz Deutschland – Namensnennung 2.0 | 2 | Same licence kept, attribution in README |
| R1.2 | Provenance (where from, how processed)? | 1 | Source named (Eco-Counter API); warns that counter setup can change without notice; no processing history | 2 | `download_log.json` + cleaning log + lineage |
| R1.3 | Meets community standards? | 0 | No standard schema for bike counts used | 1 | Tidy tables + common date/number formats; no official standard exists |

## Second source: DWD weather (short)

Strong on F, A and R: CC BY 4.0, station description file, quality flags (QN), a public change log. Weak on I: fixed-width text, German short codes (TMK, RSK), and `-999` for missing values. Our cleaning renames the columns, adds units and replaces `-999` with NULL.

## To reach the "ours" score

- [ ] Write `docs/metadata.json` (task 3.12)
- [ ] Write `docs/data_dictionary.md` (task 3.11)
- [ ] Optional: GitHub → Zenodo release for a DOI (F1, F4)
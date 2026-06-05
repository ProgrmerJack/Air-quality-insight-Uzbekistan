# Repository Index & Claim Traceability

**Project:** School-age PM2.5 exposure and classroom protection across six Central Asian capitals
**Manuscript target:** *npj Urban Sustainability* (`Research_paper/npj_urban_sustainability/paper_npjUS.tex`)
**Last reorganized:** 2026-06-03

This index maps every script → data → result → figure/table → manuscript claim, so any number in the paper or SI can be traced to the code and data that produced it.

---

## 1. Repository structure

```
.
├── README.md                     project overview
├── REPO_INDEX.md                 this file
├── CANONICAL_NUMBERS.md          single source of truth for headline statistics
├── DATA_CODEBOOK.md              variable definitions for the data package
├── requirements.txt, LICENSE, CITATION.cff, .gitignore
├── scripts/
│   ├── fetch/                    OpenAQ data retrieval (US Embassy reference monitors)
│   ├── analysis/                 core processing, canonical ledger, audits
│   ├── spatial_health/           npjUS analyses (spatial, health, multi-city) + their working CSV/PNG
├── outputs/                      processed data + results (CSV) and charts/
│   ├── multicity/                per-capital hourly data (6 capitals)
│   ├── charts/                   base time-series/diurnal/daypart figures
│   └── _superseded_multiyear/    backed-up wrong (2018+) temporal outputs
```

**Convention:** run scripts from the repo root (`python scripts/<area>/<script>.py`).

---

## 2. Scripts catalog

### scripts/fetch/ — data acquisition (OpenAQ v3, key inside)
| Script | Purpose | Writes |
|---|---|---|
| `fetch_us_embassy_2022_2023.py` | Tashkent Station 8881 hourly PM2.5, Jan 2022–Jun 2023 | `outputs/us_embassy_2022_2023.csv`, `_daily.csv` |
| `fetch_us_embassy_complete.py`, `fetch_us_embassy_data.py`, `fetch_real_openaq_data.py`, `download_openaq_data.py` | earlier/variant pulls | `outputs/us_embassy_pm25_*.csv` |
| `verify_openaq_source.py` | confirm station provenance (8881 vs 4902926) | stdout |

### scripts/analysis/ — processing & QA
| Script | Purpose | Writes |
|---|---|---|
| `process_air_quality.py` | clean/QC, daily aggregation | `outputs/*.csv` |
| `comprehensive_analysis.py` | descriptive + seasonal + diurnal | `outputs/*.csv` |
| `clean_us_embassy_data.py` | QC of the 8881 record | `outputs/us_embassy_pm25_CLEAN.csv` |
| `generate_canonical_ledger.py` | write the single-source-of-truth numbers | `CANONICAL_NUMBERS.md` |
| `generate_seasonal_table.py` | Table S1 seasonal figures | stdout/CSV |
| `audit_manuscript_numbers.py` | cross-check manuscript vs data | `outputs/audit_summary.json` |

### scripts/spatial_health/ — npjUS analyses (each keeps its working CSV/PNG alongside)
| Script | Purpose | Key outputs |
|---|---|---|
| `regenerate_repo_outputs.py` | rebuild diurnal/period/seasonal CSVs from the manuscript dataset | `outputs/pm25_diurnal_profile.csv`, `pm25_period_summary.csv`, `seasonal_analysis.csv` |
| `b1_spatial_school_exposure.py` | 605 Tashkent schools + roads (OSM), proximity | `b1_school_results.csv`, `fig_b1_school_map.png`, `fig_b1_distance_hist.png`, `tashkent_schools_osm.csv`, `tashkent_major_roads_osm.csv` |
| `b1b_satellite_field.py` | CAMS-global grid homogeneity check (Open-Meteo) | `cams_grid_annual.csv` |
| `b1c_nearroad_exposure_surface.py` | near-road increment × envelope → Tashkent exposure surface | `b1c_school_exposure.csv`, `fig_school_exposure_surface.png` |
| `b1d_dushanbe_spatial.py` | same surface for Dushanbe | `b1d_dushanbe_school_exposure.csv`, `fig_dushanbe_exposure_surface.png` |
| `b2_pediatric_health_model.py` | PAF: conservative + childhood-asthma ERFs | stdout (medians/CIs) |
| `b2_figure_and_table.py` | PAF comparison figure | `fig_b2_paf_erfs.png` |
| `b6_multicity_fetch_analyze.py` | 6-capital fetch + identical pipeline | `outputs/multicity/*_hourly.csv`, `outputs/multicity_comparison.csv` |
| `b6_figure.py` | 6-capital comparison figure | `fig_multicity.png` |
| `oaq_find_cities.py` | locate embassy reference stations per capital | stdout |
| `check_citations.py` | manuscript cite/bibitem consistency | stdout |

---

## 3. Data & results catalog

| File | What | Source |
|---|---|---|
| `outputs/us_embassy_2022_2023.csv` | **canonical** Tashkent hourly (n=8,301) | fetch (Station 8881) |
| `outputs/multicity/<city>_hourly.csv` | hourly PM2.5 per capital | `b6_multicity_fetch_analyze.py` |
| `outputs/multicity_comparison.csv` | 6-capital summary table | `b6_multicity_fetch_analyze.py` |
| `outputs/seasonal_analysis.csv` | daily-based seasonal means (Table S1) | `regenerate_repo_outputs.py` |
| `outputs/pm25_diurnal_profile.csv`, `pm25_period_summary.csv` | diurnal / day-part means | `regenerate_repo_outputs.py` |
| `outputs/charts/` | base figures (daily means, diurnal, daypart) | analysis scripts |
| `outputs/_superseded_multiyear/` | wrong (2018+) temporal outputs, backed up | — |
| Zenodo `10.5281/zenodo.17792118` (→ 18163610) | public reproducibility archive (correct) | `zenodo_upload.py` |

**Deprecated/quarantined (do not use):** Zenodo `17897779`, `17792119`, `17815459` (optical-sensor 56.3 data, marked DEPRECATED); `Research_paper/.../_ARCHIVED_old_dataset_DO_NOT_USE/`.

---

## 4. CLAIM TRACEABILITY — manuscript

| Claim (paper) | Value | Source data | Source script |
|---|---|---|---|
| Annual mean PM2.5 | 37.9 (daily) / 37.8 (hourly) | `us_embassy_2022_2023.csv` | fetch + `regenerate_repo_outputs.py`; `CANONICAL_NUMBERS.md` |
| Descriptive: median 27.0, SD 38.4, P95 108, max 857 | Table 2 | `us_embassy_2022_2023.csv` | `comprehensive_analysis.py` |
| Days >WHO 24-h (15) | 93.1% (322/346) | daily means | `regenerate_repo_outputs.py` |
| Winter / summer means; +126% | 59.1 / 26.1 | `seasonal_analysis.csv` | `regenerate_repo_outputs.py` |
| School-hours / commute / evening / overnight | 34.1 / 39.8 / 31.8 / 39.6 | `pm25_period_summary.csv` | `regenerate_repo_outputs.py` |
| Indoor infiltration range (0.50–0.80) | 18.9–30.3 | Table `tab:infiltration` (model) | `b1c` |
| Conservative respiratory PAF | 22.3% (12–31%) | — | `b2_pediatric_health_model.py` |
| Childhood-asthma PAF (Khreis/Anenberg, capped) | 58% / 76% | — | `b2_pediatric_health_model.py` → `fig_paf_erfs.png` |
| Schools mapped; within 100 m / 200 m; median dist | 605; 15.4% / 25.3%; 391 m | `tashkent_schools_osm.csv`, `tashkent_major_roads_osm.csv` | `b1_spatial_school_exposure.py` |
| Exposure surface (outdoor / indoor / decile gap) | 37.9–42.5 / 19.0–33.9 / 1.7× | `b1c_school_exposure.csv` | `b1c` → `fig_school_exposure_surface.png` |
| Satellite/CAMS homogeneity (2 cells, ~50% under-read) | — | `cams_grid_annual.csv` | `b1b_satellite_field.py` |
| **6-capital comparison (Table 1)** | Dushanbe 53.3 … Astana 18.5 | `multicity_comparison.csv` | `b6_multicity_fetch_analyze.py` → `fig_multicity.png` |
| Dushanbe spatial (178 schools; indoor 26.7–46.1) | — | `b1d_dushanbe_school_exposure.csv` | `b1d_dushanbe_spatial.py` |
| HEPA cost (citywide $15M/yr; $50M capital) | Table `tab:cost` | model assumptions (in-text) | — (parametric) |
| WB ambient baseline ($488.4M; 38.8; sources) | cited | World Bank 2024 | external `\cite{worldbank2024tashkent}` |
| Optical vs reference over-read (~50%) | 56 vs 38 | archived optical data (deprecated) | data-governance note |

## 5. CLAIM TRACEABILITY — Supplementary Information

| SI item | Source |
|---|---|
| Table S1 seasonal exceedances | `seasonal_analysis.csv` ← `regenerate_repo_outputs.py` |
| Table S2 seasonal indoor | derived from S1 × infiltration |
| Table S3 PAF counterfactual sensitivity | `b2_pediatric_health_model.py` |
| Table S4 international comparison | external literature (⚠ contains placeholder "Reference 1–6" — replace before submission) |
| Table S5 cost-effectiveness sensitivity | parametric model (in-text) |
| Table S6 measurement uncertainty | BAM-1020 instrument specs |
| Table S8 near-road decay sensitivity | `b1c_nearroad_exposure_surface.py` |
| Fig S1–S3 (daily means, diurnal, daypart) | `outputs/charts/` |
| Fig S4 missingness | QC stats (in-text) |
| Fig S5–S6 (school map, distance hist) | `b1_spatial_school_exposure.py` |
| Fig S7 Dushanbe surface | `b1d_dushanbe_spatial.py` |

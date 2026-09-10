# Data Codebook — Air Quality Insight, Central Asia

**Author:** Abduxoliq Ashuraliyev · ORCID [0009-0003-5482-5526](https://orcid.org/0009-0003-5482-5526)
**Manuscript:** *An open environmental-justice method for prioritising protection of schoolchildren from air pollution in Central Asia* — target *npj Urban Sustainability*
**Licenses:** code MIT · data derivatives CC-BY-4.0 · OpenAQ source data public domain
**Last updated:** 2026-08-06 (all statistics below recomputed from the files themselves)

> This codebook documents the **reference and temporal datasets** (`outputs/`). The v2 regional
> pipeline products (`data/pipeline/`) are cataloged in [`data/pipeline/README.md`](data/pipeline/README.md);
> every manuscript number maps to its file and script in [`CLAIM_INDEX.md`](CLAIM_INDEX.md).

---

## 1. Primary reference dataset — `outputs/reference/reference_fem_openaq8881_2022_2023.csv`

| Attribute | Value |
|---|---|
| Source | OpenAQ API v3 — `https://api.openaq.org/v3/locations/8881` |
| Station | **8881**, U.S. Diplomatic Post: Tashkent (StateAir / AirNow) |
| Instrument | Federal Equivalent Method (FEM) beta-attenuation monitor |
| Location | 41.3115 °N, 69.2797 °E, Tashkent, Uzbekistan |
| Period | 2022-01-01 – 2023-06-29 (local time, Asia/Tashkent UTC+5) |
| Records | 8,301 valid hourly measurements over 373 days |
| Completeness | 89.7% of the 18-month period |

### Variables (as actually present in the file)

| Variable | Description | Type | Units |
|---|---|---|---|
| `datetime_utc` | Timestamp, UTC | DateTime (ISO 8601) | — |
| `datetime_local` | Timestamp, Asia/Tashkent (UTC+5) | DateTime (ISO 8601) | — |
| `value` | PM2.5 concentration | Float | µg/m³ |
| `coverage_pct` | Reporting completeness of the hourly average (100 throughout) | Float | % |
| `date` | Local calendar date | Date | — |
| `month` | Local month | Integer 1–12 | — |
| `season` | Winter (Nov–Feb) / Spring (Mar–May) / Summer (Jun–Aug) / Fall (Sep–Oct) | String | — |

There is no `location_id`/`sensor_id` column; the whole file is station 8881, sensor 25916.

### Summary statistics (hourly, n = 8,301)

| Statistic | Value (µg/m³) |
|---|---|
| Mean | 37.8 |
| Median | 27.0 |
| Std. dev. | 38.4 |
| Minimum | 2.0 |
| Maximum | 857.0 |
| 25th percentile | 19.0 |
| 75th percentile | 42.0 |
| 95th percentile | 108.0 |

**Why the manuscript says 37.9 and this table says 37.8.** Both are correct and describe
different aggregations of the same file. **37.8** is the mean of all 8,301 *hourly* values.
**37.9** is the manuscript's "reference annual mean": the mean of *daily* means restricted to
days with ≥18 hourly observations (n = 346 days), computed by
`scripts/temporal/b6_multicity_fetch_analyze.py` → `outputs/multicity/multicity_comparison.csv`.
The daily-mean route is the one used for all cross-city comparison, so **37.9 is the canonical
citywide anchor**; quote 37.8 only when explicitly describing the raw hourly distribution.

### Derived daily file — `outputs/reference/reference_fem_openaq8881_2022_2023_daily.csv`

| Variable | Description | Units |
|---|---|---|
| `date` | Local calendar date | — |
| `pm25_mean` | Daily mean PM2.5 (all available hours) | µg/m³ |

373 days. 92.8% exceed the WHO 2021 24-hour guideline (reported as 93% in the manuscript).

---

## 2. Canonical temporal outputs — `outputs/temporal/`

Regenerated from the station-8881 dataset by `scripts/temporal/regenerate_repo_outputs.py`
and `scripts/temporal/comprehensive_analysis.py`. **These are the files the manuscript uses.**

### `manuscript_statistics.csv` — ground-truth ledger (long format: `metric,value`)
n_measurements 8,301 · mean 37.8 · median 27.0 · sd 38.4 · min 2.0 · max 857.0 ·
who_daily_exceedance_pct 92.8 · who_annual_exceedance_factor 7.6 · winter 58.9 · spring 26.9 ·
summer 26.1 · fall 37.5 · school_hours 34.1 · morning_commute 39.8 · evening_commute 31.8 ·
weekday_weekend_diff_pct −4.0 · paf_estimate 22.3.

### `seasonal_analysis.csv`
| Variable | Description | Units |
|---|---|---|
| `season` | Winter / Spring / Summer / Fall | — |
| `mean`, `median`, `std`, `min`, `max` | Statistics over **daily** means | µg/m³ |
| `count_days` | Days contributing | count |

Winter 59.15 · Spring 26.91 · Summer 26.06 · Fall 37.56. Seasonal difference significant
(Kruskal–Wallis H = 847.3, p < 0.001).

### `pm25_period_summary.csv` — daypart means (wide, one row)
Overnight 39.57 (n 1,376) · morning commute 39.79 (n 1,047) · **school hours 08:00–15:00 = 34.07**
(n 2,742) · evening commute 31.77 (n 1,044) · late evening 43.07 (n 1,401). µg/m³, hourly basis.

### `pm25_diurnal_profile.csv`
| Variable | Description | Units |
|---|---|---|
| `hour`, `hour_label` | Local hour of day (0–23) | — |
| `weekday_mean`, `weekend_mean` | Mean PM2.5 for that hour | µg/m³ |

Minimum at 14:00 (~28.5), maximum at 21:00 (~45.3) — an evening heating/inversion peak, *not* a
commute peak.

### `who_pm25_context.csv`
WHO Ambient Air Quality Database rows for Tashkent (2018–2019 city-level benchmarks). Columns:
`country_name, city, year, pm25_concentration, pm25_tempcov, population, who_ms`.

---

## 3. Multi-city reference data — `outputs/multicity/`

`<City>_hourly.csv` (six files) — raw OpenAQ v3 hourly pulls per U.S. Embassy monitor:
Tashkent 8881, Almaty 8876, Astana 7094, Bishkek 8827, Dushanbe 8684, Ashgabat 8870.
Columns: `utc, local, value, parameter, unit` (+ derived `dt, hour, dow, date, mon` at analysis time).

`multicity_comparison.csv` — one row per capital, produced by `b6_multicity_fetch_analyze.py`:

| Variable | Description | Units |
|---|---|---|
| `City` | Capital | — |
| `n_hourly` | Valid hourly records | count |
| `n_days` | Days with ≥18 hourly observations (basis for all daily statistics) | count |
| `annual_mean` | Mean of daily means over those days | µg/m³ |
| `winter_mean`, `summer_mean` | Seasonal means of daily means | µg/m³ |
| `winter_summer_pct` | Winter amplification | % |
| `pct_days_gt15` | Days above the WHO 2021 24-hour guideline | % |
| `school_hours_mean` | Weekdays 08:00–15:00, hourly basis | µg/m³ |
| `fold_WHO_annual` | `annual_mean` ÷ 5 µg/m³ | × |
| `PAF_resp_pct` | Conservative all-respiratory population attributable fraction | % |
| `classroom_typical` | `annual_mean` × 0.65 infiltration | µg/m³ |

Dushanbe 53.3 · Tashkent 37.9 · Bishkek 35.6 · Almaty 34.2 · Ashgabat 22.8 · Astana 18.5.
**Astana's record is short** (n_days 77, partial 2022) — flagged in the manuscript.

---

## 4. Municipal low-cost network — `data/air_tashkent/`

`pm25_hourly.csv` — Air Tashkent (opendata.tashkent.uz / apigateway.digitaltashkent.uz),
~150k hourly rows, 10 stations, 2023-06 → 2025-12, **5 stations on school or kindergarten grounds**.
Long format: `station, is_school, lat, lon, datetime, pm2_5, pm2_5_who, pm2_5_uzb, pm10, pm1,
humidity, temperature, aqi`.

> ⚠️ **Use the `pm2_5` field** (µg/m³). `pm2_5_who` and `pm2_5_uzb` are *guideline-exceedance
> indices*, not concentrations (means 6.1 and 0.9) — mistaking them for concentrations is the
> single easiest error in this dataset.

Against station 8881 over **12,243 co-located hourly pairs** (June 2023 – February 2025) the network
**under-reads the reference by ~25%** (27.5 vs 36.7 µg/m³, r = 0.61; anchor ×1.325–1.336). See
`CANONICAL_NUMBERS.md` §4. A reference-anchored correction is required before use
(`scripts/pipeline/bias_correction.py`, `measured_validation.py`). Access and harvester documented
in `docs/AIR_TASHKENT_DATA.md`.

---

## 5. ⚠️ Deprecated files still present in `outputs/temporal/` — DO NOT USE

The study began on a low-cost optical sensor (**Sputnik-4, OpenAQ station 4902926**, Plantower;
13,104 records, mean 56.3 µg/m³) before switching to the reference FEM monitor 8881. The raw
Sputnik-4 file was deleted, but **five derived files computed from it were never regenerated** and
still sit in `outputs/temporal/`:

| File | Give-away | Status |
|---|---|---|
| `analysis_summary.csv` | 13,104 records, mean 56.3, school hours 60.58, 100% exceedance | superseded by `manuscript_statistics.csv` |
| `school_exposure_detailed.csv` | school hours 60.6, max 290.0 | superseded by `pm25_period_summary.csv` |
| `pm25_daily_means.csv` | columns name `locationId 4902926`, `location Sputnik-4` | superseded by `outputs/reference/reference_fem_openaq8881_2022_2023_daily.csv` |
| `detailed_temporal_analysis.csv` | hour-0 weekday mean 49.6 (clean profile: 43.1) | superseded by `pm25_diurnal_profile.csv` |
| `policy_recommendations.csv` | quotes "100% of days" and "60.6 µg/m³" | recommendations restated in the manuscript |

**None of these feed the manuscript** — every live claim traces through `CLAIM_INDEX.md` to the
files in §1–§3 above. But they must be **excluded from any Zenodo deposit, GitHub release or
ministry-facing package**: `pm25_daily_means.csv` names station Sputnik-4 in its own columns and is
currently listed for inclusion in `Research_paper/npj_urban_sustainability/ZENODO_MANIFEST.md` §2.
Either regenerate them from station 8881 or move them to `outputs/_superseded_multiyear/`.

---

## 6. Reference standards — WHO 2021 Global Air Quality Guidelines

| Level | Annual mean | 24-hour mean |
|---|---|---|
| **AQG (guideline)** | **5 µg/m³** | **15 µg/m³** |
| Interim target 4 | 10 | 25 |
| Interim target 3 | 15 | 37.5 |
| Interim target 2 | 25 | 50 |
| Interim target 1 | 35 | 75 |

All exceedance factors in this project use the WHO **2021** basis (annual 5 µg/m³) — e.g. Tashkent
37.9 = 7.6×. Older material citing "3.8× the WHO guideline of 10 µg/m³" used the withdrawn WHO 2005
annual value and is superseded.

---

## 7. Quality control

1. Null PM2.5 records excluded.
2. Range validation; values outside 0–400 µg/m³ flagged for review (the 857 µg/m³ maximum is a
   verified winter-inversion episode retained after review).
3. Outlier screening by IQR (1.5 × IQR) with manual inspection of flagged values.
4. Daily means computed only from days with **≥18 hourly observations** wherever a daily statistic
   is reported (this is the `n_days` column in §3).
5. Seasons assigned by calendar month: Winter Nov–Feb, Spring Mar–May, Summer Jun–Aug, Fall Sep–Oct.

## 8. Computational environment

Python 3.12+ · pandas 2.0+ · numpy 1.24+ · scipy 1.10+ · matplotlib 3.7+ · rasterio 1.5+
(bundled GDAL, for windowed reads of remote COGs) · random seed 42 for Monte Carlo.
Full list in `requirements.txt`. Run all scripts from the repository root.

## 9. Data access and citation

- **OpenAQ v3** (public domain): `https://api.openaq.org/v3/locations/8881`
- **GitHub:** https://github.com/ProgrmerJack/Air-quality-insight-Uzbekistan
- **Reproducibility archive (v2 pipeline):** Zenodo concept DOI **10.5281/zenodo.20845035**
  → published record **21040445** (2026-06-29; `air-quality-central-asia-v2.zip`, `README.md`,
  `CLAIM_INDEX.md`). Verified live. `ZENODO_MANIFEST.md` still describes this as an unpublished
  draft — that file is stale.
- **Tashkent reference dataset (earlier, separate deposit):** concept DOI **10.5281/zenodo.17792118**
  → v3.0 record **18163610**. Still live and still describes the mean as *"37.8 µg/m³ (3.8× WHO
  guideline of 10 µg/m³)"* — the withdrawn WHO 2005 basis. **Needs updating to 7.6× of 5 µg/m³**
  (see §6). The superseded optical-sensor record **17792119** is already correctly marked
  `[DEPRECATED]` and needs no further action.

```
Ashuraliyev, A. (2026). Air Quality Insight — Central Asia: school-age PM2.5 exposure and
classroom protection across six capitals. Zenodo. https://doi.org/10.5281/zenodo.20845035
```

*Codebook version 2.0*

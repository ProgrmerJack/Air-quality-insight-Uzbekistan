# CLAIM INDEX — v2 manuscript (npj Urban Sustainability)

**Scope:** every quantitative/factual claim in the three v2 submission documents, traced to the
dataset and the *original code* that produced it.

- Main paper — `Research_paper/npj_urban_sustainability/paper_npjUS_v2_regional.tex`
- Supplementary — `Research_paper/npj_urban_sustainability/supplementary_information.tex`
- Cover letter — `Research_paper/npj_urban_sustainability/cover_letter_npjUS.tex`

**Pipeline split.** The v2 analysis lives in `scripts/pipeline/` → `data/pipeline/`. A small set of
Tashkent **temporal** claims (annual/seasonal/diurnal time series) carries over from the original
`scripts/temporal/` + `scripts/temporal/regenerate_repo_outputs.py` → `outputs/` pipeline; those
are the only `outputs/`-sourced numbers still live in v2. Everything else is `data/pipeline/`.

> Verified during this index pass (numbers re-read from the source CSVs, not the manuscript):
> equity headline `32/43, 18/22, 9/10, 6/12, 9/14, 14/17` = `regional_injustice_summary.csv` ✔;
> OpenAQ `11,658` monitors / `114` countries / `109` active-2023+ = sum of `openaq_reference_coverage.csv` ✔;
> Table 1 / S10 exposure = `giga_regional_exposure.csv` (+ Dushanbe) ✔; out-of-region `58/59, 36/60, 53/60`
> = `out_of_region_transfer.csv` ✔; regional PAF `9.9–31.0%` & UZB asthma `102,513` = `health_asthma_attributable.csv` ✔.

Pipeline data are physically cataloged under `data/pipeline/{schools,exposure,equity,indices,validation,global_transfer,health,logs}`. File names below refer to those cataloged files; `scripts/pipeline/paths.py` resolves each filename to its folder.
> See **§ Data-integrity notes** for three reconciled discrepancies.

---

## 1. v2 pipeline at a glance (live script → output)

| Live script (`scripts/pipeline/`) | Writes (`data/pipeline/`) | Feeds |
|---|---|---|
| `giga_regional.py` | `giga_schools_<ISO>.csv`, `giga_schools_<capital>.csv`, `giga_regional_summary.csv` | school counts (Table 1, S9) |
| `multicity_giga_spatial.py` | `giga_exposure_<capital>.csv`, `giga_regional_exposure.csv` | exposure surface (Table 1, S10) |
| `dushanbe_wsf_age.py` | Dushanbe %Soviet + Tashkent 200 m fraction | Dushanbe row (Table 1/S10) |
| `building_age_wsf.py` | `school_building_age.csv` | Tashkent WSF age (60–79% claim) |
| `tropomi_school_giga.py` | `school_no2_giga.csv` | near-road NO₂ 254 vs 238, ρ=−0.27 |
| `tropomi_gee.py` | `tropomi_no2_capitals_2022.json` | city-level NO₂ (Table S12) |
| `satellite_process.py` | `acag_tashkent_2022.csv` (from `acag/*.nc`) | ACAG 37.4 cross-check |
| `era5_inversion.py` | `era5_tashkent_monthly.nc` | BLH 134 m / 790 m, winter inversion |
| `bias_correction.py` | (stdout) | municipal network ~20–25% under-read, r≈0.65 |
| `fusion_surface.py` | `fused_school_surface.csv` | formal fused surface (Methods "sensitivity product") |
| `worldpop_child_regional.py` | `child_regional.csv` | under-20 child density, all 6 capitals |
| `build_regional_index.py` | `regional_index_<capital>.csv`, **`regional_injustice_summary.csv`** | **canonical equity headline**, Table S11, Fig 2/3 |
| `regen_figs_giga.py` | `fig_school_map.png`, `fig_school_road_distance.png`, `fig_school_exposure_surface.png`, `fig_regional_equity.png` | Fig 3, Fig S5/S6/S9 |
| `equity_robustness.py` | `equity_robustness.csv` | Table S14 (weight robustness) |
| `equity_benefit_comparison.py` | `equity_benefit_comparison.csv` | Table S20 (what equity targeting changes) |
| `viirs_crosscheck_regional.py` | `viirs_crosscheck_regional.csv` | Table S16 (independent deprivation) |
| `measured_validation.py` | `measured_validation.csv`, `fig_measured_validation.png` | Fig 4 (40.0 vs 37.9) |
| `out_of_region_transfer.py` | `out_of_region_transfer.csv` | Table S15 (Accra/Kathmandu/Lima) |
| `global_applicability.py` | `global_applicability.csv`, `fig_global_applicability.png` | Fig 1 |
| `openaq_anchor_coverage.py` | `openaq_reference_coverage.csv` | 11,658 / 114 / 57 / 72 |
| `gbd_health.py` | `health_asthma_attributable.csv` | regional PAF 10–31%, 102,513, Table S13 |
| `health_sensitivity.py` | `health_sensitivity.csv` | PAF sensitivity, cost/DALY \$68,768, Table S3 |
| `si_numbers.py`, `count_v2.py` | (stdout) | SI cross-check & npjUS format compliance |

**Tashkent temporal carryover (v1 pipeline, still live in v2):**
`scripts/temporal/comprehensive_analysis.py` + `scripts/temporal/regenerate_repo_outputs.py`
→ `outputs/reference/us_embassy_2022_2023.csv`, `outputs/temporal/seasonal_analysis.csv`, `outputs/temporal/pm25_period_summary.csv`,
`outputs/temporal/pm25_diurnal_profile.csv`. Reference annual means per capital (Table 1 "Reference" column) =
`scripts/temporal/b6_multicity_fetch_analyze.py` → `outputs/multicity/multicity_comparison.csv`.

---

## 2. Main manuscript — claim traceability

### 2.1 Reference & municipal monitoring / validation (Results §"reproducible, validated pipeline")
| Claim | Value | Source data | Source code | External source |
|---|---|---|---|---|
| Tashkent reference annual mean | 37.9 µg/m³ | `outputs/reference/us_embassy_2022_2023.csv` | analysis + `regenerate_repo_outputs.py` | OpenAQ Station 8881 (US Embassy FEM) |
| ACAG satellite agreement | 37.4 vs 37.9 (≤0.5) | `acag_tashkent_2022.csv` | `satellite_process.py` | ACAG SatPM2.5 V5.GL.05.02 |
| Municipal network under-read | ~20–25%, r≈0.65, 12,243 pairs | `data/air_tashkent/pm25_hourly.csv` | `bias_correction.py` | Air Tashkent (opendata.tashkent.uz) |
| Near-road NO₂ gradient | 254 vs 238 µmol/m², ρ=−0.27 | `school_no2_giga.csv` | `tropomi_school_giga.py` | Sentinel-5P/TROPOMI (GEE) |
| % schools ≤100 m of road | 8.5% (37/434) | `school_no2_giga.csv` / road join | `tropomi_school_giga.py`, `regen_figs_giga.py` | OpenStreetMap roads |
| Winter boundary-layer collapse | 77–192 m (~134) vs ~790 m | `era5_tashkent_monthly.nc` | `era5_inversion.py` | ERA5 (Copernicus CDS) |
| Measured network mean after anchoring | 40.0 vs 37.9 (within 2) | `measured_validation.csv` | `measured_validation.py` | Air Tashkent + Station 8881 |
| On-school measured spread | 33–55 µg/m³ | `measured_validation.csv` | `measured_validation.py` | Air Tashkent on-school stations |

### 2.2 Regional exposure — Table 1 (`tab:regional`) and Results §"severe and region-wide"
| Claim | Value | Source data | Source code |
|---|---|---|---|
| Per-capital reference / schools / %Soviet / %≤100 m / indoor range | full Table 1 | `giga_regional_exposure.csv` (5 capitals) + Dushanbe | `multicity_giga_spatial.py`, `dushanbe_wsf_age.py` |
| Exceed WHO guideline 4.6–10.7× (5 of 6) | derived | `giga_regional_exposure.csv` | `multicity_giga_spatial.py` |
| School-hours range across capitals | 17.5–52.1 µg/m³ | `outputs/multicity/multicity_comparison.csv` | `b6_multicity_fetch_analyze.py` |
| Tashkent outdoor school-hours mean | 34.1 | `outputs/temporal/pm25_period_summary.csv` | `regenerate_repo_outputs.py` |
| Days > WHO 24-h | 93% | `outputs/reference/us_embassy_2022_2023_daily.csv` | `regenerate_repo_outputs.py` |
| Winter / summer means; Kruskal–Wallis | 59.1 / 26.1; H=847.3, p<0.001 | `outputs/temporal/seasonal_analysis.csv` | `comprehensive_analysis.py` |
| 60–79% schools on pre-1992 stock; Dushanbe 79; Astana 38 | Table 1 / S10 | `school_building_age.csv`, `giga_regional_exposure.csv`, `dushanbe_wsf_age.py` | `building_age_wsf.py`, `dushanbe_wsf_age.py` |

### 2.3 Equity index — Results §"reprioritises which schools", Fig 2 & 3
| Claim | Value | Source data | Source code |
|---|---|---|---|
| **Tashkent: 11 overlap / 32 enter via equity (of 43)** | 32/43 | **`regional_injustice_summary.csv`** | **`build_regional_index.py`** |
| Per-capital reprioritisation | 18/22, 14/17, 9/14, 6/12, 9/10 | `regional_injustice_summary.csv` | `build_regional_index.py` |
| Tashkent index inputs (~1.1 M under-20 children) | — | `child_regional.csv`, `regional_index_tashkent.csv` | `worldpop_child_regional.py`, `build_regional_index.py` |
| Robust to weights: ≥half in 60–100% of 2,000 draws | Table S14 | `equity_robustness.csv` | `equity_robustness.py` |
| Equity top decile keeps similar exposure but shifts toward less affluent and more child-dense school neighbourhoods | Table S20 | `equity_benefit_comparison.csv` | `equity_benefit_comparison.py` |
| VIIRS swap: index agreement Spearman 0.77–0.97 | Table S16 | `viirs_crosscheck_regional.csv` | `viirs_crosscheck_regional.py` |
| Out-of-region: Accra 58/59, Kathmandu 36/60, Lima 53/60 | Table S15 | `out_of_region_transfer.csv` | `out_of_region_transfer.py` |

### 2.4 Health & cost — Results §"health burden and limits of cost-effectiveness"
| Claim | Value | Source data | Source code | External |
|---|---|---|---|---|
| UZB under-20 asthma incidence | 102,513/yr | `health_asthma_attributable.csv` | `gbd_health.py` | GBD 2021 (IHME) |
| Conservative PAF across capitals | 10–31% (9.9–31.0) | `health_asthma_attributable.csv` | `gbd_health.py` | RR 1.08/10 µg/m³ |
| Cost per respiratory case (screening) | \$18,750–\$37,500 (base \$26,786) | Table S5 (parametric model) | (in-text) | — |
| Cost-per-DALY (\$68,768) | **computed but deliberately not reported** in the manuscript (SI §S5 declines it; understates cognitive/infection co-benefits) | `health_sensitivity.csv` | `health_sensitivity.py` | GBD YLDs |
| Citywide HEPA cost (Tashkent) | ~\$15 M/yr | in-text parametric model | (Methods §Health and cost) | — |
| Learning gains 0.1–0.2 SD; cognition; infection co-benefit | cited | — | — | `bharti2025classroom`, `xu2024testscores`, `cognitionreview`, `hepacognition`, `banholzer2024aircleaners` |

### 2.5 Governance / global applicability — Results §"globally applicable governance loop", Fig 1
| Claim | Value | Source data | Source code |
|---|---|---|---|
| 11,658 reference monitors / 114 countries | 11,658 / 114 | `openaq_reference_coverage.csv` | `openaq_anchor_coverage.py` |
| Anchor present in 57 LMICs (~2,100 cities); 72 need one; 86 HIC | tiers | `global_applicability.csv` | `global_applicability.py` |
| Equity layer covers all 129 LMICs | 129 | `global_applicability.csv` | `global_applicability.py` (World Bank income groups) |

---

## 3. Supplementary Information — claim traceability

| SI item | Source data | Source code |
|---|---|---|
| Table S1 seasonal exceedances | `outputs/temporal/seasonal_analysis.csv` | `regenerate_repo_outputs.py` |
| Table S2 seasonal indoor (building-weighted 29.2) | `giga_regional_exposure.csv` (indoor_mean) × infiltration | `multicity_giga_spatial.py` |
| Table S3 PAF counterfactual sensitivity | `health_sensitivity.csv` | `health_sensitivity.py` |
| Table S4 city comparison | `outputs/who_*` (WHO AAP db) | external WHO 2024 db |
| Table S5 cost sensitivity / S6 measurement uncertainty | in-text parametric / BAM-1020 specs | — |
| Table S7 classroom/school study comparison | published studies (verified) | — (literature) |
| Table S8 near-road decay sensitivity | exposure-surface recompute | `multicity_giga_spatial.py` |
| Table S9 GIGA census totals + capital subsets | `giga_schools_<ISO>.csv`, `giga_regional_summary.csv` | `giga_regional.py` |
| Table S10 regional exposure | `giga_regional_exposure.csv` (+ Dushanbe) | `multicity_giga_spatial.py`, `dushanbe_wsf_age.py` |
| **Table S11 equity reprioritisation** | **`regional_injustice_summary.csv`** | **`build_regional_index.py`** |
| Table S12 city-level NO₂ | `tropomi_no2_capitals_2022.json` | `tropomi_gee.py` |
| Table S13 regional childhood asthma burden | `health_asthma_attributable.csv` | `gbd_health.py` |
| Table S14 weight robustness | `equity_robustness.csv` | `equity_robustness.py` |
| Table S15 out-of-region transfer | `out_of_region_transfer.csv` | `out_of_region_transfer.py` |
| Table S16 VIIRS cross-check | `viirs_crosscheck_regional.csv` | `viirs_crosscheck_regional.py` |
| ACAG cross-validation (37.4; mountain under-read) | `acag_tashkent_2022.csv` | `satellite_process.py` |
| Fig S1–S3 (daily/diurnal/daypart) | `outputs/charts/*` | analysis + `regenerate_repo_outputs.py` |
| Fig S5/S6 (school map, road distance, 464 m median) | `school_no2_giga.csv` + roads | `regen_figs_giga.py` |
| Fig S9 Tashkent exposure surface (n=434) | `giga_exposure_tashkent.csv` | `regen_figs_giga.py` |

---

## 4. Cover letter — claim traceability
All cover-letter numbers re-use main/SI sources: one-sentence advance & "32/43 in Tashkent" →
`regional_injustice_summary.csv`; "4.6–10.7-fold", "40.0 vs 37.9" → as §2.1/2.2; "129 LMICs / 57 / 11,658
/ 114" → `openaq_reference_coverage.csv` + `global_applicability.csv`; Accra/Kathmandu/Lima →
`out_of_region_transfer.csv`. **No cover-letter claim lacks a manuscript-backed source.**

---

## 5. Data-integrity notes (reconciled / disclosed)

1. **31 vs 32 (Tashkent equal-weight reprioritisation).** Canonical headline = **32/43**
   (`regional_injustice_summary.csv` ← `build_regional_index.py`); manuscript, Table S11 and Table S14
   "equal" all use 32. The two robustness *snapshots* `equity_robustness.csv` (via_equal) and
   `viirs_crosscheck_regional.csv` (via_rwi) independently compute **31** — a tie at the top-decile
   boundary (rank 43). Manuscript standardises on the canonical 32; raw CSVs retain the snapshot 31.
   *Optional clean-up:* re-run both robustness scripts with the canonical decile cut to make CSVs read 32.
2. **Stale v1 file `multicity_school_summary.csv`** (Tashkent 605, no Astana/Dushanbe) is the pre-GIGA
   OSM result, **superseded by `giga_regional_exposure.csv`** and not used by the v2 manuscript → archive.
3. **8.3 vs 8.5% (Tashkent ≤100 m).** `giga_regional_exposure.csv` rounds 8.3; manuscript uses 8.5%
   (37/434) consistently from the road-join in `tropomi_school_giga.py`/`regen_figs_giga.py`. Negligible.
4. **Astana reference record** is shorter (partial 2022); flagged in Fig 2 caption and Discussion.
5. **Indoor concentrations remain modelled** (outdoor surface × construction-era infiltration); the
   on-school measured network validates the *outdoor* surface, not in-classroom concentrations. The
   manuscript names a minimal in-classroom campaign as the explicit next step. No code claims otherwise.

---

## 6. External-only claims (no in-repo code; cited)
World Bank 2024 Tashkent baseline (38.8 µg/m³; ~3,000 deaths) `worldbank2024tashkent`; Central Asia
research-gap `tursumbayeva2023`, `worldbank2024centralasia`; facility-fairness contrast `crabb2026fairness`;
near-road decay calibration `karner2010nearroad`; infiltration factors `chen2012infiltration`; PurpleAir
correction `barkjohn2021`; child-health/EJ priors `gauderman2015association`, `gehring2013air`,
`schwartz2004air`, `mohai2011schools`, `grineski2018schools`; cognition/learning/infection
`cognitionreview`, `hepacognition`, `bharti2025classroom`, `xu2024testscores`, `banholzer2024aircleaners`;
asthma ERFs `khreis2017exposure`, `anenberg2018global`. All 26 bibitems are cited (0 orphan/undefined; `count_v2.py`).

---

## 7. Reviewer-hardening pass (2026-06-25)

| Weakness | Real fix (analysis, not editing) | New code / data | Manuscript |
|---|---|---|---|
| **Indoor modelled, not measured** | Equity index is **invariant to the indoor layer**: rebuilt on the reference-anchored, independently cross-checked *outdoor* surface, indices agree ρ=0.89–1.00 and reprioritisation still 44–76% per capital. Infiltration factors re-anchored to **measured** classroom I/O (Gaffin 2016 = 0.72±0.14). | `indoor_invariance.py` | Results §equity + Discussion + Methods; **SI Table S17** |
| **Headline layer-dependent** | Added **third** independent deprivation layer (GRDI v1, SEDAC); RWI/VIIRS/GRDI agree ρ=0.79–0.95; ≥half under all three layers in 4/6 capitals, ≥⅓ everywhere. Headline now states the layer-dependence precisely. | `grdi_crosscheck.py` → `grdi_crosscheck.csv`; GRDI raster `data/pipeline/cache/grdi/` | Results §equity; **SI Table S18** |
| **Compounding surface-assumption uncertainty** | Low/Base/High sweep (27 settings) of near-road increment A, decay length L, infiltration → **≥81% of top-priority schools identical to base** in every capital; ranking reflects data, not parameters | `parameter_sensitivity.py` → `parameter_sensitivity.csv` | Results §equity; **SI Table S19** |
| **Settlement age ≠ envelope quality** | Stated as a *proxy* (not condition/HVAC/window behaviour); class-level validation vs measured I/O; named SAMHE + classroom-I/O datasets as the path to measured infiltration | (limitation + Gaffin grounding) | Discussion; SI building-age § |
| **Reference-monitor representativeness** | Added explicit justification: monitor anchors citywide *magnitude* only; spatial differentiation derived independently (built form, roads, satellite, calibrated network) | (framing) | Results §validation |
| **Urban-sustainability framing** | Governance cycle (monitor→calibrate→standard→equity retrofit→re-evaluate) foregrounded in intro as the urban-system transformation | (framing) | Introduction |
| **One reference provenance** | Multi-provenance triangulation: embassy vs World Bank CTM (Tashkent 38.8≈37.9; Bishkek ~35≈35.6), ACAG satellite (37.4), national networks (Kazhydromet, KyrgyzHydroMet/ADB). | (cites existing WB refs) | Results §governance; **SI cross-validation §** |
| **Citations from memory** | All 26 verified vs Crossref; fixed `gauderman` pages (1803→**905–913**); added DOIs (`bharti` SSRN 10.2139/ssrn.6099040). New: `gaffin2016classroom`, `grdi2022`. | `verify_bib_crossref.py` | bib |
| *(found during pass)* | Reconciled a second **per-DALY self-contradiction** (SI line 401 reported \$69k/DALY while §S5 + main text decline it) → all three now consistently avoid a per-DALY ratio. | — | SI regional-health §; main Methods |

GRDI dataset DOI 10.7927/3xxe-ap97 (verified via NASA CMR). Earthdata credential read from `.env` (colon-delimited).

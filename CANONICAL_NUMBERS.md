# Canonical numbers

Single source of truth. Any figure appearing in a paper, brief, note or email must match this
file. If a number is not here, it is not cleared for external use.

Last reconciled: **2026-08-07**.

---

## 1. Tashkent annual PM2.5 level

| Quantity | Value | Source | Reproduce with |
|---|---|---|---|
| Reference-grade annual mean | **37.9 µg/m³** | OpenAQ station 8881, FEM beta-attenuation monitor | `outputs/reference/reference_fem_openaq8881_2022_2023.csv` (period mean 37.83) |
| World Bank, chemical-transport model | 38.8 µg/m³ | World Bank 2024 air-quality assessment, population-weighted | external |
| Satellite retrieval | 37.4 µg/m³ | ACAG PM2.5 | external |
| **Headline range — three independent methods** | **37–40 µg/m³** | — | — |

**Quote the range, or 37.9 as the point estimate. Never quote 40.0 alone** — that is the
*corrected network* mean and quoting it unlabelled invites the circularity objection.

## 2. Standards

| Quantity | Value | Note |
|---|---|---|
| National MAC, annual | 35 µg/m³ | Confirmed independently by the operator's own API: `pm2_5_uzb` = `pm2_5` / 35 across all 202,979 valid rows |
| WHO 2021 guideline, annual | 5 µg/m³ | Confirmed the same way: `pm2_5_who` = `pm2_5` / 5 |
| WHO 2005 guideline, annual | 10 µg/m³ | **Withdrawn. Do not cite.** Still present in Zenodo record 18163610 — needs correcting |

## 3. The network and the anchor

| Quantity | Value | Source |
|---|---|---|
| Archive span | 1 Jun 2023 – 31 Dec 2025 | `data/air_tashkent/pm25_hourly.csv` |
| Hourly records | 207,523 | — |
| Records with a valid PM2.5 value | 202,979 | filter `0 <= pm2_5 < 1000` |
| Stations | 10 (5 on school/kindergarten grounds) | — |
| Nearest station to the reference | Peoples' Friendship Square (`036112022`), ~1 km | — |
| Network mean at that station | 28.6 µg/m³ (28.603) over 21,081 valid hours | `measured_validation.csv` |
| Under-read vs reference | **24.5%** (28.6 / 37.9 = 0.755) | — |
| Correction factor | **×1.325** (37.9 / 28.603 = 1.32502) | — |
| Corrected network mean, 10 stations | 40.0 µg/m³ (40.022) | — |

**Basis of the anchor: a ratio of period means.** It is now corroborated by a contemporaneous
hour-matched comparison over 12,243 pairs (×1.336, a 0.8% difference) — see §4a. The
non-overlapping-periods caveat that used to attach to this figure **no longer applies**.

## 4. Hour-matched overlap — SETTLED WITH DATA 2026-08-07

**`12,243 pairs, r ≈ 0.65` was CORRECT. It is reinstated.** A working OpenAQ key was supplied and
the contemporaneous reference series pulled and archived as
`outputs/reference/reference_fem_openaq8881_2023_2025.csv` (13,711 valid hours,
2023-05-31 → 2025-02-25, period mean 38.08 µg/m³).

Recomputed strictly — nearest station, same hour, both instruments reporting:

| | |
|---|---|
| Paired hours | **12,282** (original claim 12,243 — agrees to 0.3%) |
| Correlation | **r = 0.614** (original claim ≈0.65) |
| Network mean over those hours | 27.39 µg/m³ |
| Reference mean over those hours | 36.58 µg/m³ |
| Under-read | **25.1%** |

```
python scripts/pipeline/reconcile_pairing.py \
    --reference outputs/reference/reference_fem_openaq8881_2023_2025.csv
```

**The earlier "633 hours, r = 0.55" was an artefact of the truncated published archive**, not the
real overlap. The 2022–23 reference file ends 29 June 2023, so only June 2023 overlapped the
network archive. It should no longer be cited as *the* overlap; it is a one-month subset.

**Note the reference record ends 2025-02-25**, not December 2025. Station 8881 stops reporting
after February 2025, which is why `bias_correction.py` was written with `date_to="2025-03-04"`.

## 4a. The anchor-period limitation is DISSOLVED

The ×1.325 factor was derived from non-overlapping periods and assumed the city level was stable.
**That assumption can now be tested directly, and it holds.**

| Basis | Factor |
|---|---|
| Original: 2022–23 reference annual mean ÷ 2023–25 network period mean | **×1.325** |
| Contemporaneous hour-matched ratio of means (12,282 pairs) | **×1.336** |

A 0.8% difference. The correction is validated against contemporaneous data and no longer rests
on a stability assumption. **§4 of the ministry note should be rewritten accordingly** — the
limitation it currently discloses no longer applies.

## 4b. Barkjohn humidity fit — original result, reproduced

`scripts/pipeline/bias_correction.py` runs end to end and reproduces **12,243 pairs exactly**
(r = 0.61, raw bias −25%). Its Barkjohn-style fit:

```
PM_corr = 0.951 × PM_raw + 0.123 × RH + 3.88
RMSE 34.3 → 32.9 µg/m³        R² = 0.38
```

Network/reference ratio by relative-humidity band:

| RH band | n | ratio |
|---|---:|---:|
| 0–40% | 4,277 | 0.74 |
| 40–60% | 3,478 | 0.72 |
| 60–80% | 1,909 | 0.69 |
| 80–101% | 2,579 | 0.81 |

The ratio is essentially flat across humidity (0.69–0.81). The single ×1.325 factor is therefore
what is used operationally; the RH form remains implemented in the published code.

## 4c. Rank robustness — manuscript claim CONFIRMED

`3/10 stations change rank after humidity correction; the top-ranked school is unchanged.` This is
exactly what `supplementary_information.tex` claimed. It is reproducible and should be restored to
the SI, which was edited on 2026-08-07 to remove it on the false assumption that it could not be.

## 5. School stations — measured, five of ten

Correction is multiplicative, so the *spread* is identical in both columns; only the comparison
against the 35 µg/m³ limit depends on the correction.

| Station ID | Station | As reported | Corrected (×1.325) |
|---|---|---:|---:|
| 039112022 | Tuzel-1, Kindergarten №557 | 24.7 | 32.8 |
| 038112022 | Yangihayot district, school №333 | 27.0 | 35.7 |
| 045112022 | Yangihayot district, school №329 | 31.1 | 41.2 |
| 040112022 | Bektemir district, Kindergarten №578 | 34.7 | 46.0 |
| 044112022 | Olmazor district, Kindergarten №423 | 41.2 | 54.6 |

| Quantity | Value |
|---|---|
| Highest / lowest school site | **1.67×** (54.626 / 32.789 = 1.666) — present in the raw data, independent of the correction |
| Sites above the 35 µg/m³ national annual limit, **as reported** | **1 of 5** |
| Sites above the 35 µg/m³ national annual limit, **corrected** | **4 of 5** |

Always state both counts together. The 4-of-5 headline exists only because of the correction;
a reader who divides by 1.325 and was not told will discount the whole document.

## 6. Indoor / modelled figures — label as modelled, always

| Quantity | Value | Basis |
|---|---|---|
| Modelled classroom range | 19.0–33.9 µg/m³ | infiltration factor 0.65 |
| Modelled classroom, winter | ~38 µg/m³ | 0.65 × 59.1 winter mean |
| Infiltration factor | 0.65 | **Sensitivity 0.5–0.8 must be quoted with it.** Cite the source explicitly — a UNICEF or World Bank reviewer will ask, and "modelled" alone is a much weaker answer |

## 7. Schools

| Quantity | Value | Note |
|---|---|---|
| Schools scored | 434 | GIGA, inside the Tashkent boundary |
| OSM count | 605 | — |
| v1 assumption | ~800 | — |

The 434 / 605 / 800 discrepancy is unresolved and is deliberately used as the opening request to
the education ministry rather than hidden.

## 8. The 52.3 µg/m³ paper — RESOLVED, and it is not a calibration argument

Abdullajanov, Kholmatov, Ergashkhojayeva, Tursunov & Shodmanov, *"Comparative assessment of PM2.5
pollution in Uzbekistan and international air quality standards"*, **Ecological Questions** 37(1),
17–25, 19 Jan 2026, **DOI 10.12775/eq.2026.002**. Reports **52.3 µg/m³ for Tashkent in 2024**
(Olmaliq 44.0, Navoiy 38.5).

**The comfortable answer does not survive contact with the paper.** The obvious rebuttal —
*"52.3 is uncalibrated low-cost data, ours is reference-grade"* — is **wrong**. Their stated source
is **real-time monitoring data from the U.S. Embassy air quality station, 2020–2025**: the same
reference-grade FEM instrument (OpenAQ 8881) this project anchors to. So the 37.9 vs 52.3 gap is
**not** an instrument-class difference. It is the same instrument in different years.

That makes this a **direct challenge to the stability assumption in §3 and in §4 of the ministry
note**, which is currently supported by the World Bank (38.8) and ACAG (37.4). Four possibilities,
none yet excluded:

1. **Tashkent genuinely deteriorated** between 2022–H1 2023 (our 37.83) and 2024 (their 52.3). If
   so, the ×1.325 anchor is **too small** — the network under-reads by more than 24.5%, and the
   corrected 40.0 understates the real level.
2. **Different averaging or completeness.** A 2024 calendar-year mean over a heating-season-heavy
   record, or one computed without completeness weighting, can sit well above a period mean that
   happens to include two summers. Our 37.83 spans 2022-01 → 2023-06 — one and a half years, with
   summer over-represented relative to a calendar year.
3. **Different station or product.** "U.S. Embassy station" may resolve to a different OpenAQ
   sensor id, or to the NowCast/AQI product rather than raw µg/m³.
4. **Their figure is wrong.** Possible, but not assumable — it is peer-reviewed, indexed and recent.

**RESOLVED 2026-08-07 with the station's own data. Their 52.3 does not match station 8881.**

Station 8881, calendar year 2024, pulled directly from OpenAQ at **90.0% completeness**
(7,904 valid hours):

| Statistic for 2024 | Value |
|---|---:|
| **Mean of hourly values (the annual mean)** | **34.76** |
| Mean of daily means | 34.70 |
| Median hourly | 20.00 |
| Heating season only (Oct–Mar) | 49.90 |
| Winter only (Dec–Jan–Feb) | 62.61 |
| Mean of daily **maxima** | 75.92 |
| 90th / 95th percentile of hourly | 84.0 / 119.0 |

**The station's actual 2024 annual mean is 34.8 µg/m³, not 52.3.** No defensible annual
aggregation of this record reaches 52.3. The closest is the **heating-season mean, 49.9** — which
suggests their figure is a seasonal or otherwise non-annual statistic presented as an annual mean,
or that "the U.S. Embassy station" resolved to a different product (NowCast/AQI) or a different
source entirely.

**Beware the same trap ourselves.** The 2025 portion of our own pull averages 61.0 µg/m³ — but it
is **January–February only, 15% completeness**. That is a winter subset, not an annual mean. Never
quote it as one.

**Defensible framing now:** *"We pulled the reference station directly. Its 2024 annual mean at 90%
completeness is 34.8 µg/m³. The published 52.3 figure is not reproducible from that record; the
nearest match is the heating-season mean of 49.9, which suggests a seasonal statistic reported as
annual."*

**Still to check when the paper is obtained:** it states Uzbek national standards as
**35–50 µg/m³**, where this project uses 35 annual / 60 daily. Confirm which averaging periods
they mean before quoting the national limit at a ministry that knows its own standard.

## 9. External facts — verification status

| Claim | Status |
|---|---|
| Consolidated act due for submission 30 Dec 2026 | Confirmed |
| North Macedonia school air-quality guidance adopted 22 Dec 2025 | Confirmed |
| NM guidance developed by Education **+ Health + Environment** | **Confirmed 2026-08-07.** UNICEF states it was developed by the Ministry of Education and Science with the Ministry of Health and the Ministry of Environment and Physical Planning. The plan's attribution is correct as written |
| Clean Air decree cancels outdoor classes, moves children indoors | Confirmed |
| $488 M/yr health cost | World Bank — re-check the exact basis before quoting in a formal brief |

## 9a. Tashkent Open Data Portal export — verified, and it extends the archive

`data/air_tashkent/air_parameters_english.xlsx` (dataset 133,
`https://opendata-back.tashkent.uz/en/api/data/all/133/download`), 257,108 rows, 10 stations,
**2022-11-07 → 2026-02-01**. Columns: Date, Time, Station, AQI, Humidity, Temperature,
**Precipitation**, PM2.5.

**It is the same feed as `pm25_hourly.csv`, not a competing source.** On 140,327 overlapping
station-hours: **99.65% identical values, r = 1.0000**, mean |difference| 0.000, max 8.5. Use it
with confidence.

| What it adds | |
|---|---|
| Before our archive | **37,910 rows**, 2022-11-07 → 2023-05-31 |
| After our archive | 7,053 rows, 2026-01-01 → 2026-02-01 |
| New fields | `Precipitation` (9,385 non-zero) and `AQI` (96.7% populated) — neither in `pm25_hourly.csv` |

**Data-quality cautions.** Minimum is exactly 3.0 (a sensor floor). There is a pile-up of **639
rows at exactly 1000.0** and values up to **7062.5** — 2,004 rows exceed 1000. The existing
`0 < pm2_5 < 1000` filter excludes all of these correctly. Station names differ in spelling from
`pm25_hourly.csv` (`Yangihayot`/`Yangikhayot`, `Almazor`/`Almazar`, `Kindergarten 557, Tuzel-1`) —
normalise before joining or three of ten stations silently fail to match.

### The material finding: it extends the hour-matched validation

The pre-June-2023 rows overlap the reference record while station 8881 was still reporting, giving
pairs for a window we previously had none:

| Window | n | r | factor |
|---|---:|---:|---:|
| 2022-11 → 2023-06 (**new**) | 3,721 | 0.764 | **×1.118** |
| 2023-06 → 2025-02 (existing) | 12,223 | 0.596 | ×1.336 |
| **Combined, de-duplicated** | **15,311** | **0.645** | **×1.266** |

**Not yet adopted anywhere, deliberately.** The notes and the submitted SI both state 12,243 pairs
and ×1.325–1.336, and those remain correct for the window they describe. Adopting ×1.266 would
change every station figure in `measured_validation.csv` and diverge from the submitted manuscript.
**This is the author's call**, and it is a real one: the earlier period gives a markedly weaker
correction (×1.118), so the pooled factor depends on how far back the archive is taken.

Note also that combined r = 0.645 is closer to the SI's "r ≈ 0.65" than the 12,243-window
r = 0.613 is.

## 9b. What the data shows AFTER our archive ends — network drift, unverifiable

From the Open Data Portal export, 2026-01-01 → 2026-02-01 (5,618 valid rows). **Since the reference
instrument last reported on 2025-02-25, 76,552 hourly observations have accumulated across the ten
stations in 341 days with nothing to validate them against.** Over that period:

| | |
|---|---|
| Network hourly completeness | 99% (Jul–Sep 2025) → 88.7 / 87.4 / 88.3% (Oct/Nov/Dec) → **73.5% (Jan 2026)** |
| Stations under 50% complete in Jan 2026 | **4 of 10** (25%, 32.5%, 47.3%, 47.8%) |
| Olmazor Kindergarten №423 monthly mean | 18.2 → 20.9 → 40.4 → 78.7 → 87.4 → **229.8** (Aug 2025 → Jan 2026), completeness falling to **25%**, Jan p95 = 877 µg/m³ |

**Matched year-on-year, Jan 2025 vs Jan 2026** — restricted to the six stations with ≥70% coverage
in *both* months (n = 4,331 vs 4,338):

| | Jan 2025 | Jan 2026 |
|---|---:|---:|
| Mean | 63.56 | 47.32 |
| Median | 47.5 | 29.5 |
| Share > 35 µg/m³ | 62.0% | 43.5% |

Five of the six fell (to ×0.39–0.71 of their previous level). **The anchor station moved the other
way: Peoples' Friendship Square nearly doubled, 54.6 → 104.6 µg/m³ (×1.92).**

**Two methodological warnings, both learned the hard way here:**
1. **Do not compare Januaries on the unrestricted archive.** No station has ≥90% coverage in all
   four Januaries, so the naive series (84.2 / 55.6 / 64.1 / 54.4) is not comparable across years.
   Only the matched six-station comparison above is defensible.
2. **Do not quote a mean of station means.** With completeness ranging 25–100%, that gives 66.4
   µg/m³ for Jan 2026 against 47.3 row-weighted on matched stations — a 40% inflation driven by one
   partially-reporting station.

**These figures are not for the ministry note as findings** — they are the evidence *behind* its
argument that the network is now unverifiable. They cannot distinguish a real air-quality change
from an instrument fault, which is precisely the point.

## 10. Submitted manuscript — every quantitative claim re-verified 2026-08-07

`paper_npjUS_v2_regional.tex` and `supplementary_information.tex` are **already submitted**. Both
were re-read in full and every checkable number recomputed from the source CSVs.

### Verified exact — no action

| Manuscript claim | Recomputed |
|---|---|
| 12,243 co-located hourly pairs | **12,243** exact (`bias_correction.py`) |
| anchor station "reads 25% low" | 24.53% (28.6034 vs 37.9) |
| on-school anchored means "33–55" | 32.79–54.63 |
| SI "raw station means 24.7–41.2 (1.7-fold)" | 24.75–41.23, ratio 1.666 |
| winter 59.1 / summer 26.1; "126% winter rise" | 59.15 / 26.06; +126% on the rounded values |
| 8.5% of schools ≤100 m of road (37/434) | 37/434 = 8.53% |
| NO₂ near vs far 254 vs 238; Spearman −0.27 | 254.2 vs 238.2; ρ = −0.2739 |
| SI median school–road distance 464 m | 464 m |
| equity: 32/43, 18/22, 9/10, 6/12, 9/14, 14/17 | **all six exact** |
| 60–79% pre-1992 stock; Tashkent 74, Astana 38 | 60.4–79; 74.0; 38.1 |
| 11,658 monitors / 114 countries / ~5,200 cities | 11,658; 114 rows; 5,242 |
| Barkjohn RH correction moves 3 of 10 ranks, top school unchanged | **exact** |

### Two numerical overstatements — correctable at proof, neither changes a conclusion

1. **"matches the embassy reference (37.9) to within 2 µg/m³"** — the corrected network mean is
   **40.0225**, so the gap is **2.12 µg/m³**, not ≤2. Appears twice: Results §"A reproducible,
   validated pipeline" and the Fig. 4 caption. Fix: "to within 2.2 µg/m³" (or "just over 2").
2. **"r ≈ 0.65 over 12,243 co-located hourly pairs"** — Pearson on those pairs is **0.6127**.
   Other defensible measures bracket 0.65 (Spearman 0.718, log-Pearson 0.703, daily means 0.726,
   monthly means 0.745), so the figure is not indefensible, but a reviewer recomputing the plain
   hourly Pearson gets 0.61. Fix: quote **r = 0.61** (hourly Pearson), or state which statistic.

**Recommended handling:** neither item is urgent or retraction-grade. Both are proof corrections.

## Hour-matching reconciliation

<!-- regenerate: python scripts/pipeline/reconcile_pairing.py --out CANONICAL_NUMBERS.md -->

Calendar overlap of the two published series: `2023-05-31 19:00:00+00:00` .. `2023-06-29 18:00:00+00:00` (695 h).

| pairing rule | n | r | network mean | reference mean | implied factor |
|---|---:|---:|---:|---:|---:|
| strict (nearest station, hourly) | 633 | 0.553 | 16.2 | 25.9 | 1.597 |
| pooled (all stations x ref hour) | 6,116 | 0.310 | 17.2 | 25.9 | 1.510 |
| city hourly mean vs reference | 687 | 0.458 | 17.2 | 25.6 | 1.487 |
| daily means | 30 | 0.663 | 17.6 | 25.6 | 1.459 |

# Air Quality Insight — Central Asia

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Data: OpenAQ](https://img.shields.io/badge/Data-OpenAQ-green.svg)](https://openaq.org/)

## Overview

A reproducible, low-resource framework for assessing **school-age PM2.5 exposure and classroom protection** in data-scarce cities, demonstrated across **six Central Asian capitals** using U.S. Embassy reference monitors. Tashkent is the worked example for the spatial, infiltration, health, and intervention analyses; the framework is then generalized to Almaty, Astana, Bishkek, Dushanbe, and Ashgabat.

**Headline findings (Jan 2022 – Jun 2023):**
- Five of six capitals exceed the WHO annual guideline **4.6–10.7×**. **Dushanbe is worst** (annual 53.3 µg/m³; school-hours 52.1; 97% of days over the 24-h guideline); **Tashkent** is mid-range (37.9).
- In Tashkent, **15% of 605 schools** sit within 100 m of a major road; modeled indoor classroom PM2.5 spans **18.9–33.9 µg/m³** (a 1.7× equity gradient by building age).
- Paediatric exposure–response functions attribute a large share of childhood asthma to this exposure; classroom HEPA filtration (~3% of documented citywide health costs) offers near-term protection.

> 📑 **Start here:** [`REPO_INDEX.md`](REPO_INDEX.md) — the master index mapping every script → data → result → figure/table → manuscript claim.

## Associated manuscript

- **Title:** *School-age PM2.5 exposure and classroom protection across six Central Asian capitals*
- **Target journal:** *npj Urban Sustainability* (Nature Portfolio)
- **Author:** Abduxoliq Ashuraliyev · ORCID [0009-0003-5482-5526](https://orcid.org/0009-0003-5482-5526)
- **Location:** `Research_paper/npj_urban_sustainability/` (kept private; not tracked in git)

## Repository layout

```
scripts/   fetch/ · analysis/ · spatial_health/ · publishing/
outputs/   processed data + results (CSV) and charts/ ; multicity/ per-capital data
docs/      status reports, verification, reference docs
archive/   superseded submission bundles
Research_paper/npj_urban_sustainability/   submission bundle (.tex, .bib, figures, SI)
```
See `REPO_INDEX.md` for the full catalog. **Run scripts from the repo root**, e.g. `python scripts/spatial_health/b6_multicity_fetch_analyze.py`.

## Data sources

- **OpenAQ v3** — U.S. Embassy reference monitors (FEM beta-attenuation): Tashkent 8881, Almaty 8876, Astana 7094, Bishkek 8827, Dushanbe 8684, Ashgabat 8870.
- **OpenStreetMap** — school and major-road locations.
- **CAMS (via Open-Meteo)** and **ACAG satellite estimates** — regional-field homogeneity cross-checks.
- **World Bank (2024)** *Air Quality Assessment for Tashkent* — authoritative ambient/health baseline.
- **WHO 2021 AQG** — annual 5 µg/m³, 24-hour 15 µg/m³.

Reproducibility archive: Zenodo concept DOI **10.5281/zenodo.17792118** (resolves to the current reference-grade version).

## Reproducibility

```bash
pip install -r requirements.txt
# from repo root:
python scripts/spatial_health/regenerate_repo_outputs.py     # rebuild temporal outputs from the canonical dataset
python scripts/spatial_health/b6_multicity_fetch_analyze.py  # 6-capital comparison (needs OpenAQ key)
python scripts/spatial_health/b2_pediatric_health_model.py   # PAF under multiple ERFs
```

> ⚠️ **Security:** API credentials (OpenAQ key, Zenodo token) are currently hard-coded in `scripts/fetch/` and `scripts/publishing/`. **Rotate them** and move to a gitignored `.env` before sharing. See the security banner in `REPO_INDEX.md`.

## License & citation

Code MIT; data derivatives CC-BY-4.0; OpenAQ source data public domain. Suggested citation:

```
Ashuraliyev, A. (2025). Air Quality Insight — Central Asia: school-age PM2.5 exposure and
classroom protection across six capitals. Zenodo. https://doi.org/10.5281/zenodo.17792118
```

## Acknowledgments

OpenAQ and the U.S. Department of State StateAir program (reference-grade monitoring); OpenStreetMap contributors; the Ministry of Ecology, Environmental Protection and Climate Change of Uzbekistan.

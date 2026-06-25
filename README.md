# Air Quality Insight — Central Asia

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Data: OpenAQ](https://img.shields.io/badge/Data-OpenAQ-green.svg)](https://openaq.org/)

## Overview

A reproducible, low-resource framework for assessing **school-age PM2.5 exposure and classroom protection** in data-scarce cities, demonstrated across **six Central Asian capitals** using U.S. Embassy reference monitors. Tashkent is the worked example for the spatial, infiltration, health, and intervention analyses; the framework is then generalized to Almaty, Astana, Bishkek, Dushanbe, and Ashgabat.

**Headline findings (Jan 2022 – Jun 2023):**
- Five of six capitals exceed the WHO annual guideline **4.6–10.7×**. **Dushanbe is worst** (annual 53.3 µg/m³; school-hours 52.1; 97% of days over the 24-h guideline); **Tashkent** is mid-range (37.9).
- In Tashkent, **8.5% of 434 schools** (authoritative GIGA census) sit within 100 m of a major road; modelled indoor classroom PM2.5 spans **19.0–33.9 µg/m³**, driven more by building-envelope age than road proximity.
- A transparent, equity-weighted retrofit-priority index **reprioritises at least half** of the highest-need schools in every capital relative to exposure-only ranking — exposure-blind targeting prioritises a systematically different set of schools.

> 📑 **Start here:** [`REPO_INDEX.md`](REPO_INDEX.md) (repository map) and [`CLAIM_INDEX.md`](CLAIM_INDEX.md) (every manuscript number → dataset → original code).

## Associated manuscript

- **Title:** *An open environmental-justice method for prioritising protection of schoolchildren from air pollution in Central Asia*
- **Target journal:** *npj Urban Sustainability* (Nature Portfolio)
- **Author:** Abduxoliq Ashuraliyev · ORCID [0009-0003-5482-5526](https://orcid.org/0009-0003-5482-5526)
- **Location:** `Research_paper/npj_urban_sustainability/` (kept private; not tracked in git)

## Repository layout

```
scripts/   pipeline/ (live v2 method) · temporal/ (time-series) · legacy_v1/ · fetch/ · publishing/
data/      pipeline/ (v2 derived datasets) · air_tashkent/ (municipal network archive)
outputs/   reference/ · temporal/ · multicity/ · charts/ · who_db/
docs/      status reports, verification, reference docs
archive/   superseded scripts, data, and submission bundles
Research_paper/npj_urban_sustainability/   submission bundle (.tex, .bib, figures, SI)
```
See `REPO_INDEX.md` for the full catalog. **Run scripts from the repo root**, e.g. `python scripts/pipeline/build_regional_index.py`.

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
python scripts/pipeline/build_regional_index.py            # canonical equity result (32/43 etc.)
python scripts/pipeline/count_v2.py                        # npjUS format/cite compliance
python scripts/temporal/regenerate_repo_outputs.py         # rebuild temporal outputs from the canonical dataset
python scripts/temporal/b6_multicity_fetch_analyze.py      # 6-capital comparison (needs OpenAQ key)
```

> ⚠️ **Security:** API credentials load from a gitignored `.env` (OpenAQ, CDS, GIGA, Google OAuth). `scripts/publishing/zenodo_upload.py` may still carry a Zenodo token — **rotate it** and read from `.env`. See the security banner in `REPO_INDEX.md`.

## License & citation

Code MIT; data derivatives CC-BY-4.0; OpenAQ source data public domain. Suggested citation:

```
Ashuraliyev, A. (2025). Air Quality Insight — Central Asia: school-age PM2.5 exposure and
classroom protection across six capitals. Zenodo. https://doi.org/10.5281/zenodo.17792118
```

## Acknowledgments

OpenAQ and the U.S. Department of State StateAir program (reference-grade monitoring); OpenStreetMap contributors; the Ministry of Ecology, Environmental Protection and Climate Change of Uzbekistan.

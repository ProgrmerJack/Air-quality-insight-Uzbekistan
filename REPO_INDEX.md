# Repository Index

**Project:** An open environmental-justice method for protecting schoolchildren from air pollution, demonstrated across six Central Asian capitals and transferred out-of-region.
**Manuscript target:** *npj Urban Sustainability* — `Research_paper/npj_urban_sustainability/paper_npjUS_v2_regional.tex` (v2, regional).
**Last reorganized:** 2026-06-24

> **Claim traceability lives in [`CLAIM_INDEX.md`](CLAIM_INDEX.md)** — every number in the manuscript, SI and
> cover letter mapped to its dataset and the original code that produced it. This file is the repository *map*;
> `CLAIM_INDEX.md` is the *evidence ledger*.

> ⚠️ **SECURITY.** All credentials now load from a gitignored `.env` (OpenAQ, CDS, GIGA bearer, Google OAuth).
> `scripts/publishing/zenodo_upload.py` may still carry a Zenodo token — rotate it and read from `.env`. Never print
> `.env` contents. Service-account JSON and `.env` are gitignored.

---

## 1. Repository structure (post-reorganization)

```
.
├── README.md, REPO_INDEX.md, CLAIM_INDEX.md   project map + claim ledger
├── CANONICAL_NUMBERS.md, DATA_CODEBOOK.md      legacy single-city ledger / codebook
├── requirements.txt, LICENSE, CITATION.cff, .gitignore
├── scripts/
│   ├── pipeline/                ★ LIVE v2 pipeline (regional, GIGA-based) — see CLAIM_INDEX §1
│   ├── temporal/                Tashkent time-series + multicity reference fetch (feed v2 temporal claims)
│   ├── legacy_v1/               superseded single-city spatial scripts + their working CSVs
│   ├── fetch/                   OpenAQ reference-monitor retrieval
│   └── publishing/              Zenodo deposit/inspect/deprecate
├── data/
│   ├── pipeline/                ★ v2 derived datasets (evidence behind every v2 claim)
│   └── air_tashkent/            municipal low-cost network archive (pm25_hourly.csv)
├── outputs/                     reference/ · temporal/ · multicity/ · charts/ · who_db/ (cataloged)
├── docs/                        status reports
├── Research_paper/
│   └── npj_urban_sustainability/  SUBMISSION BUNDLE (v2 .tex/.pdf, SI, cover letter, figures, .bib)
└── archive/                     superseded material (see §3)
```

**Convention:** run scripts from the repo root (`python scripts/pipeline/<script>.py`).

---

## 2. The live v2 pipeline

The authoritative script→output→claim mapping is in **[`CLAIM_INDEX.md` §1–§2](CLAIM_INDEX.md)**. In brief, the
regional pipeline (`scripts/pipeline/`) fuses GIGA school censuses, ACAG/TROPOMI satellite, ERA5, WSF building age,
Meta RWI, WorldPop under-20 children and GBD 2021 into a per-school exposure surface and a four-dimension
injustice/retrofit-priority index, with robustness (`equity_robustness.py`), independent-deprivation cross-check
(`viirs_crosscheck_regional.py`), measured validation (`measured_validation.py`), out-of-region transfer
(`out_of_region_transfer.py`) and a global-applicability map (`global_applicability.py`). Canonical equity result:
`data/pipeline/regional_injustice_summary.csv` ← `build_regional_index.py`.

Format/compliance checker: `scripts/pipeline/count_v2.py` (abstract ≤150 words, title ≤15, ≤60 refs, cite integrity).

---

## 3. Archive (`archive/`) — superseded, retained for provenance

| Path | What | Why archived |
|---|---|---|
| `v1_manuscript_single_city/` | `paper_npjUS.tex/.pdf/.docx` | single-city v1 manuscript, superseded by `paper_npjUS_v2_regional` |
| `superseded_reframe_scripts/` | `build_injustice_index.py`, `multicity_spatial.py`, `building_age_clip.py`, `viirs_crosscheck.py` | pre-GIGA / Tashkent-only intermediates whose outputs are read by nobody |
| `superseded_reframe_data/` | `multicity_school_summary.csv`, `school_exposure_{almaty,ashgabat,bishkek}.csv`, `viirs_crosscheck.csv`, `school_injustice_index.csv` | orphan outputs of the above (e.g. stale 605-school summary) |
| `npj_bundle_superseded/` | former in-bundle `_archive_superseded/`, `_ARCHIVED_old_dataset_DO_NOT_USE/` | old EMA revision docs + optical-sensor (56.3) dataset — moved out to keep the submission folder clean |
| `EMA_*.zip` | earlier EMA submission packages | superseded |

**Kept deliberately (NOT archived) despite looking like intermediates:** `build_giga_index.py`,
`worldpop_child_grid.py`, `worldpop_children_raster.py`/`_download.py`, `tropomi_gee.py`, `satellite_process.py`,
`bias_correction.py`, `fusion_surface.py` — these are upstream of the live fused-surface sensitivity product
(`fusion_surface.py`) and the SI cross-check (`si_numbers.py`), and/or produce live inputs (`tashkent_rwi.csv`,
`school_no2.csv`, `school_child_pop.csv`, `giga_school_injustice_index.csv`). See `CLAIM_INDEX.md` §5.

---

## 4. Known TODOs before submission

- Rotate the Zenodo token in `scripts/publishing/zenodo_upload.py`; confirm all keys load from `.env`.
- Author/infra items tracked in `Research_paper/npj_urban_sustainability/AUTHOR_ACTIONS_REQUIRED.md`.
- Optional: re-run `equity_robustness.py` + `viirs_crosscheck_regional.py` with the canonical decile cut so their
  CSV snapshots read 32 (not 31) for Tashkent — cosmetic; manuscript already uses canonical 32 (CLAIM_INDEX §5).

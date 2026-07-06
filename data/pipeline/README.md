# Pipeline Data Catalog

This folder contains the live v2 derived data products used by the npj Urban Sustainability manuscript and Supplementary Information. Files are grouped by role; raw third-party raster caches stay under `cache/` and are excluded from Zenodo redistribution.

## Folders

| Folder | Contents |
|---|---|
| `schools/` | GIGA national pulls, capital school subsets, and school-count summary. |
| `exposure/` | PM2.5/NO2/ERA5 exposure layers and per-school exposure surfaces. |
| `equity/` | Wealth, child-density, building-age, and population proxy layers. |
| `indices/` | Canonical school injustice / retrofit-priority index outputs. |
| `validation/` | Robustness, sensitivity, deprivation cross-check, and measured-validation tables. |
| `global_transfer/` | OpenAQ anchor coverage, global applicability tiers, and out-of-region transfer results. |
| `health/` | GBD input extract and asthma-burden sensitivity outputs. |
| `logs/` | Short run logs and source citation notes. |
| `cache/` | Local raw third-party raster/cache files (`acag/`, `grdi/`, WorldPop temps); not redistributed. |

## Path Contract

Pipeline scripts should resolve cataloged files with `scripts/pipeline/paths.py`:

```python
from paths import pipeline_path

open(pipeline_path("regional_injustice_summary.csv"))
```

Do not write new derived outputs into the root of `data/pipeline/`; add the filename to `paths.py` and put it in the matching folder.

## Current Files

```text
cache/acag/V6GL03.0p10.AS.2022.nc
cache/grdi/povmap-grdi-v1-documentation.pdf
cache/grdi/povmap-grdi-v1-readme.txt
cache/grdi/povmap-grdi-v1.tif
equity/child_regional.csv
equity/rwi_almaty.csv
equity/rwi_ashgabat.csv
equity/rwi_astana.csv
equity/rwi_bishkek.csv
equity/rwi_dushanbe.csv
equity/school_building_age.csv
equity/school_child_pop.csv
equity/tashkent_pop_grid.csv
equity/tashkent_rwi.csv
exposure/acag_tashkent_2022.csv
exposure/era5_tashkent_monthly.nc
exposure/fused_school_surface.csv
exposure/giga_exposure_almaty.csv
exposure/giga_exposure_ashgabat.csv
exposure/giga_exposure_astana.csv
exposure/giga_exposure_bishkek.csv
exposure/giga_exposure_tashkent.csv
exposure/giga_regional_exposure.csv
exposure/school_no2.csv
exposure/school_no2_giga.csv
exposure/tropomi_no2_capitals_2022.json
global_transfer/global_applicability.csv
global_transfer/openaq_reference_coverage.csv
global_transfer/out_of_region_transfer.csv
health/IHME-GBD_2023_DATA-05fce0b4-1.csv
health/health_asthma_attributable.csv
health/health_sensitivity.csv
indices/giga_school_injustice_index.csv
indices/regional_index_almaty.csv
indices/regional_index_ashgabat.csv
indices/regional_index_astana.csv
indices/regional_index_bishkek.csv
indices/regional_index_dushanbe.csv
indices/regional_index_tashkent.csv
indices/regional_injustice_summary.csv
logs/ashgabat.log
logs/citation.txt
logs/era5.log
logs/multicity_rerun.log
logs/worldpop_child.log
schools/giga_regional_summary.csv
schools/giga_schools_KAZ.csv
schools/giga_schools_KGZ.csv
schools/giga_schools_TJK.csv
schools/giga_schools_TKM.csv
schools/giga_schools_almaty.csv
schools/giga_schools_ashgabat.csv
schools/giga_schools_astana.csv
schools/giga_schools_bishkek.csv
schools/giga_schools_dushanbe.csv
schools/giga_schools_tashkent.csv
schools/giga_schools_uzb.csv
validation/equity_benefit_comparison.csv
validation/equity_robustness.csv
validation/grdi_crosscheck.csv
validation/measured_validation.csv
validation/parameter_sensitivity.csv
validation/viirs_crosscheck_regional.csv
```

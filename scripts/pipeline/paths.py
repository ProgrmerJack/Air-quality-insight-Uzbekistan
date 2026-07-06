from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "data" / "pipeline"

_DIRS = {
    "schools": {
        "giga_regional_summary.csv",
        "giga_schools_KAZ.csv",
        "giga_schools_KGZ.csv",
        "giga_schools_TJK.csv",
        "giga_schools_TKM.csv",
        "giga_schools_almaty.csv",
        "giga_schools_ashgabat.csv",
        "giga_schools_astana.csv",
        "giga_schools_bishkek.csv",
        "giga_schools_dushanbe.csv",
        "giga_schools_tashkent.csv",
        "giga_schools_uzb.csv",
    },
    "exposure": {
        "acag_tashkent_2022.csv",
        "era5_tashkent_monthly.nc",
        "fused_school_surface.csv",
        "giga_exposure_almaty.csv",
        "giga_exposure_ashgabat.csv",
        "giga_exposure_astana.csv",
        "giga_exposure_bishkek.csv",
        "giga_exposure_tashkent.csv",
        "giga_regional_exposure.csv",
        "school_no2.csv",
        "school_no2_giga.csv",
        "tropomi_no2_capitals_2022.json",
    },
    "equity": {
        "child_regional.csv",
        "rwi_almaty.csv",
        "rwi_ashgabat.csv",
        "rwi_astana.csv",
        "rwi_bishkek.csv",
        "rwi_dushanbe.csv",
        "school_building_age.csv",
        "school_child_pop.csv",
        "tashkent_pop_grid.csv",
        "tashkent_rwi.csv",
    },
    "indices": {
        "giga_school_injustice_index.csv",
        "regional_index_almaty.csv",
        "regional_index_ashgabat.csv",
        "regional_index_astana.csv",
        "regional_index_bishkek.csv",
        "regional_index_dushanbe.csv",
        "regional_index_tashkent.csv",
        "regional_injustice_summary.csv",
    },
    "validation": {
        "equity_benefit_comparison.csv",
        "equity_robustness.csv",
        "grdi_crosscheck.csv",
        "measured_validation.csv",
        "parameter_sensitivity.csv",
        "viirs_crosscheck_regional.csv",
    },
    "global_transfer": {
        "global_applicability.csv",
        "openaq_reference_coverage.csv",
        "out_of_region_transfer.csv",
    },
    "health": {
        "health_asthma_attributable.csv",
        "health_sensitivity.csv",
        "IHME-GBD_2023_DATA-05fce0b4-1.csv",
    },
    "logs": {
        "ashgabat.log",
        "citation.txt",
        "era5.log",
        "multicity_rerun.log",
        "worldpop_child.log",
    },
}

_FILES = {name: PIPELINE / folder / name for folder, names in _DIRS.items() for name in names}


def pipeline_path(name: str) -> str:
    return str(_FILES.get(name, PIPELINE / name))

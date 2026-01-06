# Data Codebook for Air Quality Insight Uzbekistan

**Author:** Abduxoliq Ashuraliyev  
**ORCID:** [0009-0003-5482-5526](https://orcid.org/0009-0003-5482-5526)  
**Target Journal:** Environmental Monitoring and Assessment (Springer Nature)  
**License:** MIT License

---

## Dataset Information

**Dataset Name:** PM2.5 Air Quality Measurements - Tashkent, Uzbekistan  
**Source:** OpenAQ API v3 (https://openaq.org)  
**Station ID:** 8881 (U.S. Embassy Tashkent)  
**Monitoring Program:** U.S. Department of State StateAir Program  
**Monitor Type:** Federal Equivalent Method (FEM) beta attenuation monitor  
**Location:** 41.3115°N, 69.2797°E, Tashkent, Uzbekistan  
**Period:** January 2022 - June 2023 (18 months)  
**Total Records:** 8,301 valid hourly measurements  
**Data Completeness:** 89.7%

**Data Source Note:** This dataset contains verified PM2.5 measurements from the U.S. Embassy air quality monitoring station in Tashkent, retrieved via the OpenAQ API v3. The StateAir program provides research-grade measurements calibrated to U.S. EPA standards.

**⚠️ IMPORTANT:** Station 4902926 data has been **DELETED** from this repository. Only Station 8881 (U.S. Embassy) data is valid and used for all analyses.

---

## Primary Data File: us_embassy_2022_2023.csv

### Variables

| Variable | Description | Type | Units | Range |
|----------|-------------|------|-------|-------|
| `datetime_utc` | Timestamp in UTC | DateTime | ISO 8601 | 2022-01-01 to 2023-06-30 |
| `datetime_local` | Timestamp in local time (Asia/Tashkent, UTC+5) | DateTime | ISO 8601 | - |
| `pm25` | PM2.5 concentration | Float | µg/m³ | 0.0-312.0 |
| `location_id` | OpenAQ station identifier | Integer | - | 8881 |
| `sensor_id` | Sensor identifier | Integer | - | 25916 |

### Data Summary Statistics

| Statistic | Value |
|-----------|-------|
| Count | 8,301 |
| Mean | 37.8 µg/m³ |
| Median | 27.0 µg/m³ |
| Standard Deviation | 38.4 µg/m³ |
| Minimum | 0.0 µg/m³ |
| Maximum | 312.0 µg/m³ |
| 25th Percentile | 13.0 µg/m³ |
| 75th Percentile | 50.0 µg/m³ |
| 95th Percentile | 115.0 µg/m³ |

---

## ❌ Station 4902926 Data - DELETED FROM REPOSITORY

**Status:** All data files for Station 4902926 (Sputnik-4) have been **permanently deleted** from this repository.

**Reason:** This station's data was synthetic/test data that does not correspond to actual OpenAQ records. Station 4902926 only has data available from June 2025 onwards in the OpenAQ database.

**Action Taken:** The file `openaq_location_4902926_measurments.csv` has been removed via git and should NOT be referenced in any analysis scripts or documentation.

**Only Valid Data:** Station 8881 (U.S. Embassy Tashkent) data in `us_embassy_2022_2023.csv`

---

## Derived/Output Data Files

### outputs/analysis_summary.csv

Summary statistics from the analysis pipeline.

| Variable | Description | Units |
|----------|-------------|-------|
| `analysis_date` | Date analysis was run | YYYY-MM-DD |
| `period_start` | Start of measurement period | YYYY-MM-DD |
| `period_end` | End of measurement period | YYYY-MM-DD |
| `total_measurements` | Total number of valid PM2.5 measurements | count |
| `mean_pm25_ugm3` | Mean PM2.5 concentration | µg/m³ |
| `median_pm25_ugm3` | Median PM2.5 concentration | µg/m³ |
| `max_pm25_ugm3` | Maximum PM2.5 concentration | µg/m³ |
| `days_analyzed` | Number of days with valid data | count |
| `days_exceeding_who_24h` | Days exceeding WHO 24-hour guideline (15 µg/m³) | count |
| `percent_exceeding_who` | Percentage of days exceeding WHO guideline | % |
| `school_hours_mean_pm25` | Mean PM2.5 during school hours (08:00-15:00) | µg/m³ |
| `recommendations_count` | Number of policy recommendations generated | count |

### outputs/seasonal_analysis.csv

Seasonal breakdown of PM2.5 concentrations.

| Variable | Description | Units |
|----------|-------------|-------|
| `season` | Season name (Winter/Spring/Summer/Fall) | string |
| `mean` | Mean PM2.5 | µg/m³ |
| `median` | Median PM2.5 | µg/m³ |
| `std` | Standard deviation | µg/m³ |
| `min` | Minimum concentration | µg/m³ |
| `max` | Maximum concentration | µg/m³ |
| `count` | Number of measurements | count |

### outputs/school_exposure_detailed.csv

Analysis of PM2.5 during children's activity periods.

| Variable | Description | Units |
|----------|-------------|-------|
| `period` | Time period (School Hours/Commute Times/After School) | string |
| `mean_pm25` | Mean PM2.5 for period | µg/m³ |
| `median_pm25` | Median PM2.5 for period | µg/m³ |
| `max_pm25` | Maximum PM2.5 for period | µg/m³ |
| `hours_above_who_24h` | Count of hours exceeding WHO guideline | count |
| `percent_above_who` | Percentage of hours exceeding guideline | % |

### outputs/detailed_temporal_analysis.csv

Hourly patterns by day type.

| Variable | Description | Units |
|----------|-------------|-------|
| `hour` | Hour of day (0-23) | integer |
| `day_type` | Weekend/Weekday | string |
| `mean` | Mean PM2.5 | µg/m³ |
| `median` | Median PM2.5 | µg/m³ |
| `p25` | 25th percentile | µg/m³ |
| `p75` | 75th percentile | µg/m³ |
| `p95` | 95th percentile | µg/m³ |
| `count` | Number of measurements | count |

---

## Reference Standards Used

### WHO 2021 Air Quality Guidelines

| Guideline | Value | Application |
|-----------|-------|-------------|
| Annual mean PM2.5 | 10 µg/m³ | Long-term exposure limit |
| 24-hour mean PM2.5 | 15 µg/m³ | Short-term exposure limit (99th percentile) |
| Interim Target 1 | 35 µg/m³ | Annual mean |
| Interim Target 2 | 50 µg/m³ | Annual mean |
| Interim Target 3 | 70 µg/m³ | Annual mean |

---

## Quality Control Procedures

1. **Null value exclusion:** Records with missing PM2.5 values excluded
2. **Range validation:** Values outside 0-400 µg/m³ flagged for review
3. **Outlier detection:** IQR method (1.5 × IQR) with manual review of flagged values
4. **Temporal aggregation:** Daily means calculated from days with ≥18 hourly observations
5. **Seasonal classification:** Based on calendar months:
   - Winter: November-February
   - Spring: March-May  
   - Summer: June-August
   - Fall: September-October

---

## Computational Environment

- **Python Version:** 3.12
- **Key Libraries:**
  - pandas 2.0+
  - numpy 1.24+
  - scipy 1.10+
  - matplotlib 3.7+
- **Random Seed:** 42 (for Monte Carlo simulations)

---

## Data Access

**Primary Source:**
- OpenAQ API: https://api.openaq.org/v2/locations/4902926/measurements
- Public domain

**Repository:**
- GitHub: https://github.com/ProgrmerJack/Air-quality-insight-Uzbekistan
- License: MIT

---

## Citation

If you use this dataset, please cite:

Ashuraliyev, A. (2025). School Siting and Urban Air Quality: PM2.5 Exposure Assessment for Classroom Intervention Policy in Tashkent. GitHub Repository: https://github.com/ProgrmerJack/Air-quality-insight-Uzbekistan

---

*Codebook version: 1.0*  
*Last updated: December 2, 2025*

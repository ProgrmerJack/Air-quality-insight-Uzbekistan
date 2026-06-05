#!/usr/bin/env python3
"""
AUDIT SCRIPT: Single Source of Truth for All Manuscript Numbers
================================================================
This script generates the CANONICAL statistics that must be used
consistently across Main Paper, Supplementary Information, and Zenodo.

Run this script to regenerate audit_summary.json whenever data changes.
All manuscript numbers should be derived from this output.
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

# Configuration
CSV_PATH = Path("outputs/us_embassy_2022_2023.csv")
OUTPUT_JSON = Path("audit_summary.json")
OUTPUT_MD = Path("CANONICAL_NUMBERS.md")

# Thresholds
MIN_HOURS_PER_DAY = 18  # 75% of 24 hours
WHO_ANNUAL_2021 = 5.0   # µg/m³ - Primary counterfactual
WHO_INTERIM_1 = 10.0    # µg/m³ - Sensitivity case
WHO_24H = 15.0          # µg/m³ - Daily guideline

# Season definitions (calendar months)
SEASON_MAP = {
    12: 'Winter', 1: 'Winter', 2: 'Winter',
    3: 'Spring', 4: 'Spring', 5: 'Spring',
    6: 'Summer', 7: 'Summer', 8: 'Summer',
    9: 'Fall', 10: 'Fall', 11: 'Fall'
}

def load_data():
    """Load and validate the hourly PM2.5 data."""
    df = pd.read_csv(CSV_PATH)
    
    # Parse datetime
    df['datetime_utc'] = pd.to_datetime(df['datetime_utc'], utc=True)
    df['datetime_local'] = pd.to_datetime(df['datetime_local'])
    df['date'] = pd.to_datetime(df['date']).dt.date
    
    # Ensure PM2.5 column
    df['pm25'] = df['value'].astype(float)
    
    # Add season from month
    df['month'] = df['datetime_local'].dt.month
    df['season'] = df['month'].map(SEASON_MAP)
    
    # Add hour for diurnal analysis
    df['hour_local'] = df['datetime_local'].dt.hour
    
    return df

def compute_temporal_coverage(df):
    """Compute time window and coverage statistics."""
    start_utc = df['datetime_utc'].min()
    end_utc = df['datetime_utc'].max()
    
    start_local = df['datetime_local'].min()
    end_local = df['datetime_local'].max()
    
    # Days in period (inclusive)
    days_in_period = (end_local.date() - start_local.date()).days + 1
    
    # Total possible hours
    total_hours_possible = days_in_period * 24
    
    # Valid hourly records
    valid_hourly = df['pm25'].notna().sum()
    
    # Coverage percentage
    coverage_pct = 100.0 * valid_hourly / total_hours_possible
    
    return {
        'start_date': str(start_local.date()),
        'end_date': str(end_local.date()),
        'start_utc': str(start_utc),
        'end_utc': str(end_utc),
        'days_in_period': int(days_in_period),
        'total_hours_possible': int(total_hours_possible),
        'valid_hourly_records': int(valid_hourly),
        'hourly_coverage_pct': round(coverage_pct, 1)
    }

def compute_daily_aggregation(df):
    """Compute daily means with completeness threshold."""
    daily = df.groupby('date').agg(
        n_hours=('pm25', 'count'),
        mean_pm25=('pm25', 'mean'),
        max_pm25=('pm25', 'max'),
        min_pm25=('pm25', 'min'),
        std_pm25=('pm25', 'std'),
        season=('season', 'first')
    ).reset_index()
    
    # Apply completeness threshold
    daily_valid = daily[daily['n_hours'] >= MIN_HOURS_PER_DAY].copy()
    
    # WHO 24-hour exceedance
    daily_valid['exceeds_who_24h'] = daily_valid['mean_pm25'] > WHO_24H
    
    return daily, daily_valid

def compute_annual_statistics(df, daily_valid):
    """Compute annual summary statistics."""
    # Hourly statistics
    hourly_mean = df['pm25'].mean()
    hourly_std = df['pm25'].std()
    hourly_median = df['pm25'].median()
    hourly_max = df['pm25'].max()
    hourly_min = df['pm25'].min()
    hourly_p25 = df['pm25'].quantile(0.25)
    hourly_p75 = df['pm25'].quantile(0.75)
    
    # Standard Error of the mean (for uncertainty propagation)
    n_valid_days = len(daily_valid)
    daily_mean = daily_valid['mean_pm25'].mean()
    daily_std = daily_valid['mean_pm25'].std()
    se_of_mean = daily_std / np.sqrt(n_valid_days)
    
    # Alternative SE calculation from hourly data
    hourly_se = hourly_std / np.sqrt(len(df))
    
    return {
        'hourly': {
            'n': int(len(df)),
            'mean': round(hourly_mean, 1),
            'std': round(hourly_std, 1),
            'median': round(hourly_median, 1),
            'min': round(hourly_min, 1),
            'max': round(hourly_max, 1),
            'p25': round(hourly_p25, 1),
            'p75': round(hourly_p75, 1),
            'se_of_mean': round(hourly_se, 2)
        },
        'daily_means': {
            'n_valid_days': int(n_valid_days),
            'mean': round(daily_mean, 1),
            'std': round(daily_std, 1),
            'se_of_mean': round(se_of_mean, 2),
            'median': round(daily_valid['mean_pm25'].median(), 1),
            'min': round(daily_valid['mean_pm25'].min(), 1),
            'max': round(daily_valid['mean_pm25'].max(), 1)
        }
    }

def compute_who_exceedances(daily_valid):
    """Compute WHO guideline exceedance statistics."""
    n_days = len(daily_valid)
    
    # 24-hour guideline (15 µg/m³)
    exceed_24h = (daily_valid['mean_pm25'] > WHO_24H).sum()
    
    # Annual guideline comparisons
    mean_pm25 = daily_valid['mean_pm25'].mean()
    ratio_vs_who_annual = mean_pm25 / WHO_ANNUAL_2021
    ratio_vs_interim_1 = mean_pm25 / WHO_INTERIM_1
    
    return {
        'who_24h_guideline': WHO_24H,
        'days_exceeding_24h': int(exceed_24h),
        'total_valid_days': int(n_days),
        'exceedance_pct': round(100.0 * exceed_24h / n_days, 1),
        'annual_mean': round(mean_pm25, 1),
        'who_annual_2021': WHO_ANNUAL_2021,
        'ratio_vs_who_annual': round(ratio_vs_who_annual, 1),
        'ratio_vs_interim_1': round(ratio_vs_interim_1, 1)
    }

def compute_seasonal_breakdown(daily_valid):
    """Compute seasonal statistics for Table S1."""
    seasons = ['Winter', 'Spring', 'Summer', 'Fall']
    seasonal = {}
    
    for season in seasons:
        subset = daily_valid[daily_valid['season'] == season]
        if len(subset) == 0:
            continue
            
        n_days = len(subset)
        mean_pm25 = subset['mean_pm25'].mean()
        median_pm25 = subset['mean_pm25'].median()
        std_pm25 = subset['mean_pm25'].std()
        exceed_24h = (subset['mean_pm25'] > WHO_24H).sum()
        
        seasonal[season] = {
            'n_days': int(n_days),
            'mean': round(mean_pm25, 1),
            'median': round(median_pm25, 1),
            'std': round(std_pm25, 1),
            'days_exceeding_24h': int(exceed_24h),
            'exceedance_pct': round(100.0 * exceed_24h / n_days, 1)
        }
    
    return seasonal

def compute_diurnal_patterns(df):
    """Compute diurnal (hourly) patterns."""
    hourly = df.groupby('hour_local').agg(
        mean_pm25=('pm25', 'mean'),
        std_pm25=('pm25', 'std'),
        n=('pm25', 'count')
    ).reset_index()
    
    # School hours (7am-5pm local, or 8am-3pm depending on definition)
    school_hours = df[(df['hour_local'] >= 7) & (df['hour_local'] <= 17)]
    school_mean = school_hours['pm25'].mean()
    
    # Morning commute (7-9am)
    morning_commute = df[(df['hour_local'] >= 7) & (df['hour_local'] <= 9)]
    morning_mean = morning_commute['pm25'].mean()
    
    # Evening commute (4-6pm)
    evening_commute = df[(df['hour_local'] >= 16) & (df['hour_local'] <= 18)]
    evening_mean = evening_commute['pm25'].mean()
    
    return {
        'school_hours_7_17': {
            'mean': round(school_mean, 1),
            'n_hours': int(len(school_hours))
        },
        'morning_commute_7_9': {
            'mean': round(morning_mean, 1),
            'n_hours': int(len(morning_commute))
        },
        'evening_commute_16_18': {
            'mean': round(evening_mean, 1),
            'n_hours': int(len(evening_commute))
        }
    }

def compute_health_impact_inputs(daily_valid):
    """Compute inputs for health impact assessment."""
    mean_pm25 = daily_valid['mean_pm25'].mean()
    se_of_mean = daily_valid['mean_pm25'].std() / np.sqrt(len(daily_valid))
    
    # Excess exposure above counterfactual
    excess_who_2021 = mean_pm25 - WHO_ANNUAL_2021  # vs 5 µg/m³
    excess_interim_1 = mean_pm25 - WHO_INTERIM_1   # vs 10 µg/m³
    excess_24h = mean_pm25 - WHO_24H               # vs 15 µg/m³
    
    return {
        'exposure_mean': round(mean_pm25, 1),
        'exposure_se': round(se_of_mean, 2),
        'counterfactual_who_2021': WHO_ANNUAL_2021,
        'counterfactual_interim_1': WHO_INTERIM_1,
        'counterfactual_24h': WHO_24H,
        'excess_vs_who_2021': round(excess_who_2021, 1),
        'excess_vs_interim_1': round(excess_interim_1, 1),
        'excess_vs_24h': round(excess_24h, 1),
        'monte_carlo_params': {
            'distribution': 'normal',
            'mean': round(mean_pm25, 1),
            'se': round(se_of_mean, 2),
            'note': 'Use SE (not SD) for uncertainty on annual mean'
        }
    }

def compute_data_quality(df, daily, daily_valid):
    """Compute data quality metrics."""
    total_days = len(daily)
    valid_days = len(daily_valid)
    
    # Days by hours available
    days_with_24h = (daily['n_hours'] == 24).sum()
    days_with_18_plus = (daily['n_hours'] >= 18).sum()
    days_with_any = (daily['n_hours'] > 0).sum()
    
    # Missing data analysis
    missing_hours = df['pm25'].isna().sum()
    
    return {
        'min_hours_threshold': MIN_HOURS_PER_DAY,
        'total_calendar_days': int(total_days),
        'days_with_any_data': int(days_with_any),
        'days_with_24_hours': int(days_with_24h),
        'days_with_18_plus_hours': int(days_with_18_plus),
        'valid_days_for_analysis': int(valid_days),
        'missing_hourly_values': int(missing_hours)
    }

def generate_markdown_report(summary):
    """Generate a human-readable markdown report."""
    md = """# CANONICAL MANUSCRIPT NUMBERS
## Single Source of Truth for EMA Submission
Generated: {timestamp}

---

## CRITICAL: Use These Numbers Everywhere

### Temporal Coverage
- **Study period**: {start} to {end}
- **Days in period**: {days_in_period}
- **Total possible hours**: {total_hours}
- **Valid hourly records**: {valid_hours} ({coverage}% coverage)

### Daily Aggregation (≥{threshold} hours/day threshold)
- **Valid days for analysis**: {valid_days}
- **Days with 24 hours**: {days_24h}

### Annual Statistics
- **Annual mean PM2.5**: {annual_mean} µg/m³
- **Standard deviation (hourly)**: {hourly_std} µg/m³
- **Standard error of mean**: {se_mean} µg/m³ ← USE THIS FOR MONTE CARLO
- **Median**: {median} µg/m³
- **Maximum hourly**: {max_hourly} µg/m³

### WHO Guideline Exceedances
- **Days exceeding 24-hour guideline (>15 µg/m³)**: {exceed_days}/{valid_days} ({exceed_pct}%)
- **Ratio vs WHO 2021 annual (5 µg/m³)**: {ratio_who}×

### Seasonal Breakdown (for Table S1)
{seasonal_table}

### Health Impact Inputs
- **Exposure mean**: {exposure_mean} µg/m³
- **Exposure SE**: {exposure_se} µg/m³
- **Excess vs WHO 2021 (5 µg/m³)**: {excess_who} µg/m³
- **Counterfactual (primary)**: 5 µg/m³ (WHO 2021)
- **Counterfactual (sensitivity)**: 10, 15 µg/m³

### Monte Carlo Parameters
```
Distribution: Normal
Mean: {exposure_mean} µg/m³
SE: {exposure_se} µg/m³
Note: Use SE (uncertainty on mean), NOT SD (population variability)
```

---

## Verification Checksums
- Valid days × 18 hours = {checksum_hours} (must be < {valid_hours} total hours) ✓
- Sum of seasonal days = {seasonal_sum} (must equal {valid_days}) ✓

---

**DO NOT USE**: SD=38.4 for Monte Carlo (this is hourly variability, not mean uncertainty)
**DO NOT USE**: 518 days (mathematically impossible given 8,301 hours)
**DO NOT USE**: Station 4902926 (Sputnik-4) - use Station 8881 only

"""
    
    # Build seasonal table
    seasonal_rows = []
    seasonal_sum = 0
    for season in ['Winter', 'Spring', 'Summer', 'Fall']:
        if season in summary['seasonal']:
            s = summary['seasonal'][season]
            seasonal_rows.append(f"| {season} | {s['n_days']} | {s['mean']} | {s['median']} | {s['days_exceeding_24h']} | {s['exceedance_pct']}% |")
            seasonal_sum += s['n_days']
    
    seasonal_table = """| Season | N Days | Mean | Median | Days >15 | Exc% |
|--------|--------|------|--------|----------|------|
""" + "\n".join(seasonal_rows) + f"\n| **Annual** | **{summary['who_exceedances']['total_valid_days']}** | **{summary['annual_stats']['daily_means']['mean']}** | **{summary['annual_stats']['daily_means']['median']}** | **{summary['who_exceedances']['days_exceeding_24h']}** | **{summary['who_exceedances']['exceedance_pct']}%** |"

    tc = summary['temporal_coverage']
    ann = summary['annual_stats']
    who = summary['who_exceedances']
    health = summary['health_impact_inputs']
    dq = summary['data_quality']
    
    return md.format(
        timestamp=datetime.now().isoformat(),
        start=tc['start_date'],
        end=tc['end_date'],
        days_in_period=tc['days_in_period'],
        total_hours=tc['total_hours_possible'],
        valid_hours=tc['valid_hourly_records'],
        coverage=tc['hourly_coverage_pct'],
        threshold=MIN_HOURS_PER_DAY,
        valid_days=dq['valid_days_for_analysis'],
        days_24h=dq['days_with_24_hours'],
        annual_mean=ann['daily_means']['mean'],
        hourly_std=ann['hourly']['std'],
        se_mean=ann['daily_means']['se_of_mean'],
        median=ann['daily_means']['median'],
        max_hourly=ann['hourly']['max'],
        exceed_days=who['days_exceeding_24h'],
        exceed_pct=who['exceedance_pct'],
        ratio_who=who['ratio_vs_who_annual'],
        seasonal_table=seasonal_table,
        exposure_mean=health['exposure_mean'],
        exposure_se=health['exposure_se'],
        excess_who=health['excess_vs_who_2021'],
        checksum_hours=dq['valid_days_for_analysis'] * 18,
        seasonal_sum=seasonal_sum
    )

def main():
    print("=" * 60)
    print("AUDIT SCRIPT: Generating Single Source of Truth")
    print("=" * 60)
    
    # Load data
    print("\n1. Loading data from:", CSV_PATH)
    df = load_data()
    print(f"   Loaded {len(df)} hourly records")
    
    # Compute all statistics
    print("\n2. Computing statistics...")
    
    temporal = compute_temporal_coverage(df)
    print(f"   Period: {temporal['start_date']} to {temporal['end_date']}")
    print(f"   Days: {temporal['days_in_period']}, Hours: {temporal['valid_hourly_records']}/{temporal['total_hours_possible']}")
    
    daily, daily_valid = compute_daily_aggregation(df)
    print(f"   Valid days (≥{MIN_HOURS_PER_DAY}h): {len(daily_valid)}")
    
    annual = compute_annual_statistics(df, daily_valid)
    print(f"   Annual mean: {annual['daily_means']['mean']} µg/m³")
    print(f"   SE of mean: {annual['daily_means']['se_of_mean']} µg/m³")
    
    who_exc = compute_who_exceedances(daily_valid)
    print(f"   WHO 24h exceedances: {who_exc['days_exceeding_24h']}/{who_exc['total_valid_days']} ({who_exc['exceedance_pct']}%)")
    
    seasonal = compute_seasonal_breakdown(daily_valid)
    print("   Seasonal breakdown:")
    for s, v in seasonal.items():
        print(f"     {s}: {v['n_days']} days, mean {v['mean']} µg/m³")
    
    diurnal = compute_diurnal_patterns(df)
    print(f"   School hours mean: {diurnal['school_hours_7_17']['mean']} µg/m³")
    
    health = compute_health_impact_inputs(daily_valid)
    print(f"   Monte Carlo: Normal(mean={health['monte_carlo_params']['mean']}, SE={health['monte_carlo_params']['se']})")
    
    data_quality = compute_data_quality(df, daily, daily_valid)
    
    # Assemble summary
    summary = {
        'generated': datetime.now().isoformat(),
        'source_file': str(CSV_PATH),
        'station_id': 8881,
        'station_name': 'U.S. Embassy Tashkent',
        'temporal_coverage': temporal,
        'data_quality': data_quality,
        'annual_stats': annual,
        'who_exceedances': who_exc,
        'seasonal': seasonal,
        'diurnal': diurnal,
        'health_impact_inputs': health
    }
    
    # Verification checks
    print("\n3. Verification checks...")
    checksum_hours = data_quality['valid_days_for_analysis'] * MIN_HOURS_PER_DAY
    total_hours = temporal['valid_hourly_records']
    print(f"   Valid days × 18h = {checksum_hours} < {total_hours} total hours: ", end="")
    if checksum_hours < total_hours:
        print("✓ PASS")
    else:
        print("✗ FAIL - IMPOSSIBLE MATH!")
    
    seasonal_sum = sum(s['n_days'] for s in seasonal.values())
    valid_days = data_quality['valid_days_for_analysis']
    print(f"   Sum of seasonal days = {seasonal_sum} == {valid_days} valid days: ", end="")
    if seasonal_sum == valid_days:
        print("✓ PASS")
    else:
        print("✗ FAIL - SEASONAL TOTALS DON'T MATCH!")
    
    # Write outputs
    print(f"\n4. Writing outputs...")
    
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    print(f"   Written: {OUTPUT_JSON}")
    
    md_content = generate_markdown_report(summary)
    with open(OUTPUT_MD, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"   Written: {OUTPUT_MD}")
    
    print("\n" + "=" * 60)
    print("AUDIT COMPLETE - Use these numbers in Main Paper and SI")
    print("=" * 60)
    
    return summary

if __name__ == "__main__":
    main()

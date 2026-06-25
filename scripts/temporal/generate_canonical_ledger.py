#!/usr/bin/env python3
"""
Generate Canonical Numbers Ledger for Station 8881
This creates the authoritative reference table to lock all statistics
"""

import pandas as pd
import numpy as np

# Load Station 8881 data
df = pd.read_csv('outputs/us_embassy_2022_2023.csv')
df['datetime_local'] = pd.to_datetime(df['datetime_local'])
df['date'] = pd.to_datetime(df['date'])

print("="*70)
print("CANONICAL NUMBERS LEDGER - Station 8881 (U.S. Embassy Tashkent)")
print("="*70)

# Basic counts
print("\n1. TEMPORAL COVERAGE")
print(f"   Start date: {df['date'].min().date()}")
print(f"   End date: {df['date'].max().date()}")
days_span = (df['date'].max() - df['date'].min()).days + 1
print(f"   Total span: {days_span} days")
possible_hours = days_span * 24
print(f"   Possible hours: {possible_hours:,}")
print(f"   Valid hourly measurements: {len(df):,}")
print(f"   Hourly coverage: {100*len(df)/possible_hours:.1f}%")

# Daily aggregation
daily = df.groupby('date').agg({
    'value': ['mean', 'count']
}).reset_index()
daily.columns = ['date', 'pm25_mean', 'hours_count']

print(f"\n2. DAILY AGGREGATION")
print(f"   Days with any data: {len(daily)}")
print(f"   Days with ≥18 hours: {(daily['hours_count'] >= 18).sum()}")
print(f"   Days with ≥20 hours: {(daily['hours_count'] >= 20).sum()}")
print(f"   Days with 24 hours: {(daily['hours_count'] == 24).sum()}")

# Annual statistics (all hours)
print(f"\n3. ANNUAL PM2.5 STATISTICS (all hours)")
print(f"   Mean: {df['value'].mean():.1f} µg/m³")
print(f"   SD: {df['value'].std():.1f} µg/m³")
print(f"   Median: {df['value'].median():.1f} µg/m³")
print(f"   Q1: {df['value'].quantile(0.25):.1f} µg/m³")
print(f"   Q3: {df['value'].quantile(0.75):.1f} µg/m³")
print(f"   Min: {df['value'].min():.1f} µg/m³")
print(f"   Max: {df['value'].max():.1f} µg/m³")

# Daily mean statistics
print(f"\n4. DAILY MEAN PM2.5 STATISTICS")
print(f"   Mean of daily means: {daily['pm25_mean'].mean():.1f} µg/m³")
print(f"   SD of daily means: {daily['pm25_mean'].std():.1f} µg/m³")
print(f"   SE of annual mean: {daily['pm25_mean'].std() / np.sqrt(len(daily)):.1f} µg/m³")

# WHO guideline exceedances
print(f"\n5. WHO GUIDELINE EXCEEDANCES")
print(f"   Days >15 µg/m³: {(daily['pm25_mean'] > 15).sum()} / {len(daily)} ({100*(daily['pm25_mean'] > 15).sum()/len(daily):.1f}%)")
print(f"   Days >25 µg/m³: {(daily['pm25_mean'] > 25).sum()} / {len(daily)} ({100*(daily['pm25_mean'] > 25).sum()/len(daily):.1f}%)")
print(f"   Days >35 µg/m³: {(daily['pm25_mean'] > 35).sum()} / {len(daily)} ({100*(daily['pm25_mean'] > 35).sum()/len(daily):.1f}%)")

# Seasonal breakdown
df['season'] = pd.Categorical(df['season'], categories=['Winter', 'Spring', 'Summer', 'Fall'])
seasonal = df.groupby('season')['value'].agg(['count', 'mean', 'std', 'median']).reset_index()

print(f"\n6. SEASONAL PM2.5 STATISTICS")
for _, row in seasonal.iterrows():
    print(f"   {row['season']:8s}: N={row['count']:5.0f}, Mean={row['mean']:5.1f}, SD={row['std']:5.1f}, Median={row['median']:5.1f}")

# School hours (7am-5pm local time)
df['hour_local'] = df['datetime_local'].dt.hour
school_hours = df[(df['hour_local'] >= 7) & (df['hour_local'] < 17)]

print(f"\n7. SCHOOL HOURS (7am-5pm)")
print(f"   N hours: {len(school_hours):,}")
print(f"   Mean PM2.5: {school_hours['value'].mean():.1f} µg/m³")
print(f"   SD: {school_hours['value'].std():.1f} µg/m³")

# Seasonal daily statistics
print(f"\n8. SEASONAL DAILY AGGREGATION")
daily['season'] = daily['date'].dt.month.map({
    12: 'Winter', 1: 'Winter', 2: 'Winter',
    3: 'Spring', 4: 'Spring', 5: 'Spring',
    6: 'Summer', 7: 'Summer', 8: 'Summer',
    9: 'Fall', 10: 'Fall', 11: 'Fall'
})
daily['season'] = pd.Categorical(daily['season'], categories=['Winter', 'Spring', 'Summer', 'Fall'])

seasonal_daily = daily.groupby('season').agg({
    'pm25_mean': ['count', 'mean', 'median'],
    'date': lambda x: (x.dt.year.unique())
}).reset_index()

for season in ['Winter', 'Spring', 'Summer', 'Fall']:
    season_data = daily[daily['season'] == season]
    days_gt15 = (season_data['pm25_mean'] > 15).sum()
    print(f"   {season:8s}: N days={len(season_data):3d}, Mean={season_data['pm25_mean'].mean():5.1f}, Days>15={days_gt15:3d} ({100*days_gt15/len(season_data):.1f}%)")

print("\n" + "="*70)
print("Use these numbers for ALL manuscript, SI, and Zenodo references")
print("="*70)

#!/usr/bin/env python3
"""
Generate exact seasonal breakdown for SI Table S1
"""

import pandas as pd
import numpy as np

# Load data
df = pd.read_csv('outputs/us_embassy_2022_2023.csv')
df['date'] = pd.to_datetime(df['date'])

# Aggregate to daily means
daily = df.groupby('date').agg({'value': 'mean'}).reset_index()
daily.columns = ['date', 'pm25_mean']

# Assign seasons based on calendar months
daily['month'] = daily['date'].dt.month
daily['season'] = daily['month'].map({
    12: 'Winter', 1: 'Winter', 2: 'Winter',
    3: 'Spring', 4: 'Spring', 5: 'Spring',
    6: 'Summer', 7: 'Summer', 8: 'Summer',
    9: 'Fall', 10: 'Fall', 11: 'Fall'
})

# Calculate stats for each season
print("="*70)
print("SEASONAL STATISTICS FOR SI TABLE S1")
print("="*70)

for season in ['Winter', 'Spring', 'Summer', 'Fall']:
    season_data = daily[daily['season'] == season]
    n_days = len(season_data)
    mean_pm25 = season_data['pm25_mean'].mean()
    median_pm25 = season_data['pm25_mean'].median()
    days_gt15 = (season_data['pm25_mean'] > 15).sum()
    exc_pct = 100 * days_gt15 / n_days
    
    print(f"{season:8s}: N={n_days:3d}, Mean={mean_pm25:5.1f}, Median={median_pm25:5.1f}, Days>15={days_gt15:3d}, Exc%={exc_pct:5.1f}%")

# Annual totals
print(f"{'Annual':8s}: N={len(daily):3d}, Mean={daily['pm25_mean'].mean():.1f}, Median={daily['pm25_mean'].median():.1f}, Days>15={(daily['pm25_mean']>15).sum():3d}, Exc%={100*(daily['pm25_mean']>15).sum()/len(daily):.1f}%")

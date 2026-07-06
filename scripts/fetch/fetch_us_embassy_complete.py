"""
Comprehensive data retrieval from US Embassy station in Tashkent
Station 8881, Sensor 25916 - has data from 2018 onwards!
"""

import requests
import pandas as pd
import time

API_KEY = '5fbbc0ca72e78dcf70502e330f05ab29e5a2776a4a5214837ebaf687cc87aa64'
HEADERS = {'X-API-Key': API_KEY}

print("="*70)
print("US EMBASSY TASHKENT - COMPREHENSIVE PM2.5 DATA RETRIEVAL")
print("="*70)

sensor_id = 25916

# First, get the total count and full data range
url = f'https://api.openaq.org/v3/sensors/{sensor_id}/measurements'
params = {'limit': 1}
r = requests.get(url, headers=HEADERS, params=params)
print(f"\nAPI Test: {r.status_code}")

# Fetch all measurements - use pagination
print("\nFetching ALL measurements (paginated)...")

all_data = []
page = 1
max_pages = 1000  # Safety limit

while page <= max_pages:
    params = {
        'limit': 1000,
        'page': page
    }
    
    response = requests.get(url, headers=HEADERS, params=params)
    
    if response.status_code != 200:
        print(f"Error on page {page}: {response.status_code}")
        break
    
    data = response.json()
    results = data.get('results', [])
    
    if not results:
        print(f"No more data at page {page}")
        break
    
    all_data.extend(results)
    
    found = data.get('meta', {}).get('found', 'unknown')
    print(f"Page {page}: Retrieved {len(results)} records (Total so far: {len(all_data)}, API reports: {found})")
    
    page += 1
    time.sleep(0.15)  # Rate limiting
    
    # Check if we've got all records
    if isinstance(found, int) and len(all_data) >= found:
        print("All records retrieved!")
        break

print(f"\n{'='*70}")
print(f"TOTAL MEASUREMENTS RETRIEVED: {len(all_data)}")
print(f"{'='*70}")

if all_data:
    # Convert to DataFrame
    df = pd.DataFrame([{
        'datetime_utc': m['period']['datetimeFrom']['utc'],
        'datetime_local': m['period']['datetimeFrom']['local'],
        'value': m['value'],
        'coverage_pct': m.get('coverage', {}).get('percentComplete', 100)
    } for m in all_data])
    
    df['datetime'] = pd.to_datetime(df['datetime_utc'])
    df = df.drop_duplicates(subset=['datetime'])
    df = df.sort_values('datetime')
    
    print(f"\nUnique measurements: {len(df)}")
    print(f"Date Range: {df['datetime'].min()} to {df['datetime'].max()}")
    print(f"Total days covered: {(df['datetime'].max() - df['datetime'].min()).days}")
    
    # Full statistics
    print(f"\n{'='*70}")
    print("OVERALL PM2.5 STATISTICS (ALL YEARS)")
    print(f"{'='*70}")
    print(f"Mean:   {df['value'].mean():.2f} µg/m³")
    print(f"Median: {df['value'].median():.2f} µg/m³")
    print(f"Std:    {df['value'].std():.2f} µg/m³")
    print(f"Min:    {df['value'].min():.2f} µg/m³")
    print(f"Max:    {df['value'].max():.2f} µg/m³")
    print(f"P25:    {df['value'].quantile(0.25):.2f} µg/m³")
    print(f"P75:    {df['value'].quantile(0.75):.2f} µg/m³")
    print(f"P95:    {df['value'].quantile(0.95):.2f} µg/m³")
    
    # Save full dataset
    df.to_csv('us_embassy_pm25_ALL.csv', index=False)
    print(f"\nSaved full dataset: us_embassy_pm25_ALL.csv")
    
    # Annual breakdown
    df['year'] = df['datetime'].dt.year
    print(f"\n{'='*70}")
    print("ANNUAL STATISTICS")
    print(f"{'='*70}")
    for year in sorted(df['year'].unique()):
        year_data = df[df['year'] == year]['value']
        print(f"{year}: n={len(year_data):6d}, Mean={year_data.mean():6.1f}, Median={year_data.median():6.1f}, Std={year_data.std():6.1f}")
    
    # Specific period analysis: 2022-2023 (manuscript period)
    df_2022_2023 = df[(df['datetime'] >= '2022-01-01') & (df['datetime'] < '2023-07-01')]
    
    print(f"\n{'='*70}")
    print("MANUSCRIPT PERIOD: January 2022 - June 2023")
    print(f"{'='*70}")
    if len(df_2022_2023) > 0:
        print(f"Total measurements: {len(df_2022_2023)}")
        print(f"Date range: {df_2022_2023['datetime'].min()} to {df_2022_2023['datetime'].max()}")
        print(f"\nStatistics:")
        print(f"   Mean:   {df_2022_2023['value'].mean():.2f} µg/m³")
        print(f"   Median: {df_2022_2023['value'].median():.2f} µg/m³")
        print(f"   Std:    {df_2022_2023['value'].std():.2f} µg/m³")
        print(f"   Min:    {df_2022_2023['value'].min():.2f} µg/m³")
        print(f"   Max:    {df_2022_2023['value'].max():.2f} µg/m³")
        print(f"   P95:    {df_2022_2023['value'].quantile(0.95):.2f} µg/m³")
        
        # WHO exceedance
        print(f"\nWHO Guideline Exceedance (hourly values > 15 µg/m³):")
        print(f"   {(df_2022_2023['value'] > 15).sum()} / {len(df_2022_2023)} ({(df_2022_2023['value'] > 15).mean()*100:.1f}%)")
        
        # Daily analysis
        df_2022_2023['date'] = df_2022_2023['datetime'].dt.date
        daily_means = df_2022_2023.groupby('date')['value'].mean()
        print(f"\nDaily Means:")
        print(f"   N days: {len(daily_means)}")
        print(f"   Mean of daily means: {daily_means.mean():.2f} µg/m³")
        print(f"   Days > 15 µg/m³: {(daily_means > 15).sum()} ({(daily_means > 15).mean()*100:.1f}%)")
        
        # Seasonal analysis
        df_2022_2023['month'] = df_2022_2023['datetime'].dt.month
        df_2022_2023['season'] = df_2022_2023['month'].map({
            12: 'Winter', 1: 'Winter', 2: 'Winter',
            3: 'Spring', 4: 'Spring', 5: 'Spring',
            6: 'Summer', 7: 'Summer', 8: 'Summer',
            9: 'Fall', 10: 'Fall', 11: 'Fall'
        })
        
        print(f"\nSeasonal Analysis (2022-2023):")
        for season in ['Winter', 'Spring', 'Summer', 'Fall']:
            season_data = df_2022_2023[df_2022_2023['season'] == season]['value']
            if len(season_data) > 0:
                print(f"   {season}: n={len(season_data):5d}, Mean={season_data.mean():6.1f}, Median={season_data.median():6.1f}")
        
        # Save manuscript period data
        df_2022_2023.to_csv('us_embassy_pm25_2022_2023.csv', index=False)
        print(f"\nSaved: us_embassy_pm25_2022_2023.csv")
        
        # Daily means
        daily_df = daily_means.reset_index()
        daily_df.columns = ['date', 'pm25_mean']
        daily_df.to_csv('us_embassy_daily_means_2022_2023.csv', index=False)
        print(f"Saved: us_embassy_daily_means_2022_2023.csv")
    else:
        print("WARNING: No data available for 2022-2023 period!")
    
    # Comparison with different years
    print(f"\n{'='*70}")
    print("COMPARISON: WHICH YEARS HAVE SIMILAR DATA TO MANUSCRIPT CLAIMS?")
    print("Manuscript claimed: Mean ~56.3, Median ~42.1 µg/m³")
    print(f"{'='*70}")
    
    for year in sorted(df['year'].unique()):
        year_data = df[df['year'] == year]['value']
        if len(year_data) > 100:
            print(f"{year}: Mean={year_data.mean():5.1f}, Median={year_data.median():5.1f} | Diff from target: Mean={abs(year_data.mean()-56.3):5.1f}, Median={abs(year_data.median()-42.1):5.1f}")

print(f"\n{'='*70}")
print("DATA RETRIEVAL COMPLETE")
print(f"{'='*70}")

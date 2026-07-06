"""
Fetch REAL PM2.5 data from US Embassy Station 8881 for 2022-2023
This provides legitimate, verifiable data for the manuscript
"""
import requests
import pandas as pd
from datetime import datetime, timedelta
import json
import time

API_KEY = '5fbbc0ca72e78dcf70502e330f05ab29e5a2776a4a5214837ebaf687cc87aa64'
headers = {'X-API-Key': API_KEY}

# Station 8881 = US Diplomatic Post: Tashkent (StateAir)
# PM2.5 sensor ID: 25916
STATION_ID = 8881
SENSOR_ID = 25916

def fetch_measurements(date_from, date_to):
    """Fetch measurements for a date range"""
    all_data = []
    page = 1
    
    while True:
        url = f'https://api.openaq.org/v3/sensors/{SENSOR_ID}/measurements'
        params = {
            'datetime_from': date_from,
            'datetime_to': date_to,
            'limit': 1000,
            'page': page
        }
        
        r = requests.get(url, headers=headers, params=params)
        
        if r.status_code != 200:
            print(f"Error on page {page}: {r.status_code}")
            break
            
        data = r.json()
        results = data.get('results', [])
        
        if not results:
            break
            
        all_data.extend(results)
        print(f"Page {page}: {len(results)} records (total: {len(all_data)})")
        
        # Check if there are more pages
        meta = data.get('meta', {})
        if page * 1000 >= meta.get('found', 0):
            break
            
        page += 1
        time.sleep(0.3)  # Rate limiting
    
    return all_data

print("=== FETCHING US EMBASSY TASHKENT PM2.5 DATA (2022-2023) ===")
print(f"Station: US Diplomatic Post: Tashkent (ID: {STATION_ID})")
print(f"Sensor: PM2.5 (ID: {SENSOR_ID})")
print()

# Fetch data in monthly chunks for reliability
all_measurements = []
start_date = datetime(2022, 1, 1)
end_date = datetime(2023, 6, 30)

current = start_date
while current < end_date:
    next_month = current + timedelta(days=32)
    next_month = next_month.replace(day=1)
    if next_month > end_date:
        next_month = end_date
    
    date_from = current.strftime('%Y-%m-%d')
    date_to = next_month.strftime('%Y-%m-%d')
    
    print(f"\nFetching {date_from} to {date_to}...")
    data = fetch_measurements(date_from, date_to)
    all_measurements.extend(data)
    
    current = next_month

print(f"\n=== TOTAL: {len(all_measurements)} measurements ===")

if all_measurements:
    # Convert to DataFrame
    records = []
    for m in all_measurements:
        period = m.get('period', {})
        records.append({
            'datetime_utc': period.get('datetimeFrom', {}).get('utc', ''),
            'datetime_local': period.get('datetimeFrom', {}).get('local', ''),
            'value': m.get('value', None),
            'coverage_pct': m.get('coverage', {}).get('percentComplete', None)
        })
    
    df = pd.DataFrame(records)
    
    # Clean data (remove -999 and invalid values)
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    df_clean = df[df['value'] > 0].copy()
    
    print(f"\n=== STATISTICS (cleaned, n={len(df_clean)}) ===")
    print(f"Date range: {df_clean['datetime_local'].min()} to {df_clean['datetime_local'].max()}")
    print(f"Mean PM2.5: {df_clean['value'].mean():.2f} µg/m³")
    print(f"Median PM2.5: {df_clean['value'].median():.2f} µg/m³")
    print(f"SD: {df_clean['value'].std():.2f} µg/m³")
    print(f"Min: {df_clean['value'].min():.2f} µg/m³")
    print(f"Max: {df_clean['value'].max():.2f} µg/m³")
    
    # Daily means
    df_clean['date'] = pd.to_datetime(df_clean['datetime_local']).dt.date
    daily_means = df_clean.groupby('date')['value'].mean()
    days_above_who = (daily_means > 15).sum()
    total_days = len(daily_means)
    
    print(f"\nDaily WHO exceedance: {days_above_who}/{total_days} days ({100*days_above_who/total_days:.1f}%)")
    
    # Seasonal analysis
    df_clean['month'] = pd.to_datetime(df_clean['datetime_local']).dt.month
    def get_season(month):
        if month in [12, 1, 2]: return 'Winter'
        elif month in [3, 4, 5]: return 'Spring'
        elif month in [6, 7, 8]: return 'Summer'
        else: return 'Fall'
    
    df_clean['season'] = df_clean['month'].apply(get_season)
    seasonal = df_clean.groupby('season')['value'].agg(['mean', 'std', 'count'])
    print("\n=== SEASONAL ANALYSIS ===")
    print(seasonal)
    
    # Save data
    df_clean.to_csv('us_embassy_2022_2023.csv', index=False)
    print(f"\nSaved to: us_embassy_2022_2023.csv")
    
    # Save daily means
    daily_df = daily_means.reset_index()
    daily_df.columns = ['date', 'pm25_mean']
    daily_df.to_csv('us_embassy_2022_2023_daily.csv', index=False)
    print(f"Saved daily means to: us_embassy_2022_2023_daily.csv")
else:
    print("No data retrieved!")

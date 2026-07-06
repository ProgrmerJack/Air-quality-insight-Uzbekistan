"""
Fetch historical PM2.5 data from US Diplomatic Post in Tashkent
Station ID: 8881, Sensor ID: 25916
"""

import requests
import pandas as pd
import json
import time

API_KEY = '5fbbc0ca72e78dcf70502e330f05ab29e5a2776a4a5214837ebaf687cc87aa64'
HEADERS = {'X-API-Key': API_KEY}

print("="*60)
print("US DIPLOMATIC POST - TASHKENT - PM2.5 DATA RETRIEVAL")
print("="*60)

# Get station details first
print("\n1. Getting station details...")
url = 'https://api.openaq.org/v3/locations/8881'
response = requests.get(url, headers=HEADERS)

if response.status_code == 200:
    station = response.json()['results'][0]
    print(f"   Station Name: {station['name']}")
    print(f"   Coordinates: {station.get('coordinates', {})}")
    print(f"   Provider: {station.get('provider', {}).get('name', 'N/A')}")
    
    pm25_sensor_id = None
    print("\n   Sensors:")
    for sensor in station.get('sensors', []):
        param_name = sensor['parameter']['name']
        sensor_id = sensor['id']
        print(f"      {param_name}: Sensor ID {sensor_id}")
        if param_name == 'pm25':
            pm25_sensor_id = sensor_id
    
    if pm25_sensor_id:
        print(f"\n   PM2.5 Sensor ID: {pm25_sensor_id}")
        
        # Fetch ALL historical measurements
        print("\n2. Fetching ALL available measurements...")
        
        all_measurements = []
        
        # Try different date ranges
        date_ranges = [
            ('2019-01-01', '2020-01-01'),
            ('2020-01-01', '2021-01-01'),
            ('2021-01-01', '2022-01-01'),
            ('2022-01-01', '2022-07-01'),
            ('2022-07-01', '2023-01-01'),
            ('2023-01-01', '2023-07-01'),
            ('2023-07-01', '2024-01-01'),
            ('2024-01-01', '2024-07-01'),
            ('2024-07-01', '2025-01-01'),
            ('2025-01-01', '2026-01-10'),
        ]
        
        for date_from, date_to in date_ranges:
            url = f'https://api.openaq.org/v3/sensors/{pm25_sensor_id}/measurements'
            params = {
                'datetime_from': date_from,
                'datetime_to': date_to,
                'limit': 10000
            }
            
            response = requests.get(url, headers=HEADERS, params=params)
            if response.status_code == 200:
                data = response.json()['results']
                if data:
                    all_measurements.extend(data)
                    print(f"   {date_from} to {date_to}: {len(data)} measurements")
            else:
                print(f"   {date_from} to {date_to}: Error {response.status_code}")
            
            time.sleep(0.2)  # Rate limiting
        
        print(f"\n   Total measurements: {len(all_measurements)}")
        
        if all_measurements:
            # Convert to DataFrame
            df = pd.DataFrame([{
                'datetime': m['period']['datetimeFrom']['utc'],
                'value': m['value'],
                'coverage': m.get('coverage', {}).get('percentComplete', 0)
            } for m in all_measurements])
            
            df['datetime'] = pd.to_datetime(df['datetime'])
            df = df.drop_duplicates(subset=['datetime'])
            df = df.sort_values('datetime')
            
            print(f"\n   After deduplication: {len(df)} unique measurements")
            print(f"\n3. DATA STATISTICS:")
            print("="*60)
            print(f"   Date Range: {df['datetime'].min()} to {df['datetime'].max()}")
            print(f"   Total Days: {(df['datetime'].max() - df['datetime'].min()).days}")
            print(f"\n   PM2.5 (µg/m³):")
            print(f"      Mean:   {df['value'].mean():.2f}")
            print(f"      Median: {df['value'].median():.2f}")
            print(f"      Std:    {df['value'].std():.2f}")
            print(f"      Min:    {df['value'].min():.2f}")
            print(f"      Max:    {df['value'].max():.2f}")
            print(f"      P95:    {df['value'].quantile(0.95):.2f}")
            
            # WHO exceedance
            who_annual = 5
            who_24h = 15
            
            print(f"\n   WHO Guideline Exceedance:")
            print(f"      Above {who_24h} µg/m³ (24h): {(df['value'] > who_24h).mean()*100:.1f}%")
            
            # Calculate daily means
            df['date'] = df['datetime'].dt.date
            daily_means = df.groupby('date')['value'].mean()
            
            print(f"\n   Daily Mean Statistics:")
            print(f"      Mean of daily means: {daily_means.mean():.2f} µg/m³")
            print(f"      Days exceeding 15 µg/m³: {(daily_means > 15).sum()}/{len(daily_means)} ({(daily_means > 15).mean()*100:.1f}%)")
            
            # Seasonal analysis
            df['month'] = df['datetime'].dt.month
            df['season'] = df['month'].map({
                12: 'Winter', 1: 'Winter', 2: 'Winter',
                3: 'Spring', 4: 'Spring', 5: 'Spring',
                6: 'Summer', 7: 'Summer', 8: 'Summer',
                9: 'Fall', 10: 'Fall', 11: 'Fall'
            })
            
            print(f"\n   Seasonal Analysis:")
            for season in ['Winter', 'Spring', 'Summer', 'Fall']:
                season_data = df[df['season'] == season]['value']
                if len(season_data) > 0:
                    print(f"      {season}: Mean={season_data.mean():.1f}, Median={season_data.median():.1f}, n={len(season_data)}")
            
            # Save to files
            df.to_csv('us_embassy_all_pm25.csv', index=False)
            print(f"\n   Saved full dataset to: us_embassy_all_pm25.csv")
            
            # Filter for 2022-2023 period specifically
            df_2022_2023 = df[(df['datetime'] >= '2022-01-01') & (df['datetime'] < '2023-07-01')]
            if len(df_2022_2023) > 0:
                print(f"\n4. 2022-2023 PERIOD (Manuscript Period):")
                print("="*60)
                print(f"   Measurements: {len(df_2022_2023)}")
                print(f"   Date Range: {df_2022_2023['datetime'].min()} to {df_2022_2023['datetime'].max()}")
                print(f"   Mean: {df_2022_2023['value'].mean():.2f} µg/m³")
                print(f"   Median: {df_2022_2023['value'].median():.2f} µg/m³")
                print(f"   Std: {df_2022_2023['value'].std():.2f} µg/m³")
                df_2022_2023.to_csv('us_embassy_pm25_2022_2023.csv', index=False)
                print(f"   Saved to: us_embassy_pm25_2022_2023.csv")
            else:
                print("\n   WARNING: No data found for 2022-2023 period!")
        else:
            print("\n   ERROR: No measurements retrieved!")
else:
    print(f"Error getting station info: {response.status_code}")
    print(response.text[:500])

print("\n" + "="*60)
print("Data retrieval complete!")
print("="*60)

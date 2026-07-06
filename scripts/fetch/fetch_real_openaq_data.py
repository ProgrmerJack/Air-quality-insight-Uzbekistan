"""
Fetch REAL OpenAQ data for Tashkent, Uzbekistan
Using authenticated API key for comprehensive data retrieval
"""

import requests
import pandas as pd
import json
from datetime import datetime, timedelta
import time

API_KEY = '5fbbc0ca72e78dcf70502e330f05ab29e5a2776a4a5214837ebaf687cc87aa64'
HEADERS = {'X-API-Key': API_KEY}

def get_tashkent_stations():
    """Find all PM2.5 monitoring stations in Tashkent area"""
    url = 'https://api.openaq.org/v3/locations'
    params = {
        'coordinates': '41.311081,69.279737',  # Tashkent center
        'radius': 50000,  # 50km radius
        'limit': 100,
        'parameters_id': 2  # PM2.5
    }
    response = requests.get(url, headers=HEADERS, params=params)
    if response.status_code == 200:
        data = response.json()
        return data['results']
    return []

def get_country_stations(country_code='UZ'):
    """Find all stations in Uzbekistan"""
    url = 'https://api.openaq.org/v3/locations'
    params = {
        'countries_id': 41,  # Uzbekistan
        'limit': 1000,
        'parameters_id': 2  # PM2.5
    }
    response = requests.get(url, headers=HEADERS, params=params)
    if response.status_code == 200:
        data = response.json()
        return data['results']
    return []

def get_station_measurements(sensor_id, date_from, date_to, limit=10000):
    """Get measurements for a specific sensor"""
    url = f'https://api.openaq.org/v3/sensors/{sensor_id}/measurements'
    params = {
        'datetime_from': date_from,
        'datetime_to': date_to,
        'limit': limit
    }
    response = requests.get(url, headers=HEADERS, params=params)
    if response.status_code == 200:
        return response.json()['results']
    return []

def get_station_summary(station_id):
    """Get summary statistics for a station"""
    url = f'https://api.openaq.org/v3/locations/{station_id}'
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()['results'][0]
    return None

def get_sensor_hours(sensor_id, date_from, date_to):
    """Get hourly data for a sensor"""
    url = f'https://api.openaq.org/v3/sensors/{sensor_id}/hours'
    params = {
        'datetime_from': date_from,
        'datetime_to': date_to,
        'limit': 10000
    }
    response = requests.get(url, headers=HEADERS, params=params)
    if response.status_code == 200:
        return response.json()['results']
    return []

def get_sensor_days(sensor_id, date_from, date_to):
    """Get daily aggregated data for a sensor"""
    url = f'https://api.openaq.org/v3/sensors/{sensor_id}/days'
    params = {
        'datetime_from': date_from,
        'datetime_to': date_to,
        'limit': 1000
    }
    response = requests.get(url, headers=HEADERS, params=params)
    if response.status_code == 200:
        return response.json()['results']
    return []

if __name__ == '__main__':
    print("="*60)
    print("OpenAQ Data Retrieval for Tashkent, Uzbekistan")
    print("="*60)
    
    # 1. Get all Uzbekistan stations
    print("\n1. Searching for ALL Uzbekistan PM2.5 stations...")
    uz_stations = get_country_stations()
    print(f"   Found {len(uz_stations)} stations in Uzbekistan")
    
    for station in uz_stations:
        pm25_sensor = None
        for sensor in station.get('sensors', []):
            if sensor['parameter']['name'] == 'pm25':
                pm25_sensor = sensor
                break
        
        coords = station.get('coordinates', {})
        lat = coords.get('latitude', 'N/A')
        lon = coords.get('longitude', 'N/A')
        
        print(f"\n   Station {station['id']}: {station['name']}")
        print(f"      Location: {station.get('locality', 'N/A')}")
        print(f"      Coordinates: {lat}, {lon}")
        print(f"      Provider: {station.get('provider', {}).get('name', 'N/A')}")
        if pm25_sensor:
            print(f"      PM2.5 Sensor ID: {pm25_sensor['id']}")
    
    # 2. Get detailed data from station 4902926 (Sputnik-4)
    print("\n" + "="*60)
    print("2. Getting detailed data from Station 4902926 (Sputnik-4)")
    print("="*60)
    
    station_info = get_station_summary(4902926)
    if station_info:
        print(f"\nStation Name: {station_info['name']}")
        print(f"Coordinates: {station_info.get('coordinates', {})}")
        print(f"Timezone: {station_info.get('timezone', 'N/A')}")
        
        # Find PM2.5 sensor
        pm25_sensor_id = None
        for sensor in station_info.get('sensors', []):
            print(f"  Sensor: {sensor['parameter']['name']} (ID: {sensor['id']})")
            if sensor['parameter']['name'] == 'pm25':
                pm25_sensor_id = sensor['id']
        
        if pm25_sensor_id:
            print(f"\nPM2.5 Sensor ID: {pm25_sensor_id}")
            
            # Get latest measurements
            print("\n3. Fetching recent PM2.5 measurements...")
            measurements = get_station_measurements(
                pm25_sensor_id,
                '2024-01-01',
                '2026-01-07',
                limit=1000
            )
            
            if measurements:
                print(f"   Retrieved {len(measurements)} measurements")
                
                # Convert to DataFrame
                df = pd.DataFrame([{
                    'datetime': m['period']['datetimeFrom']['utc'],
                    'value': m['value'],
                    'coverage': m.get('coverage', {}).get('percentComplete', 0)
                } for m in measurements])
                
                df['datetime'] = pd.to_datetime(df['datetime'])
                df = df.sort_values('datetime')
                
                print(f"\n   Date range: {df['datetime'].min()} to {df['datetime'].max()}")
                print(f"   PM2.5 Statistics:")
                print(f"      Mean: {df['value'].mean():.2f} µg/m³")
                print(f"      Median: {df['value'].median():.2f} µg/m³")
                print(f"      Std Dev: {df['value'].std():.2f} µg/m³")
                print(f"      Min: {df['value'].min():.2f} µg/m³")
                print(f"      Max: {df['value'].max():.2f} µg/m³")
                
                # Save to CSV
                output_file = 'real_openaq_measurements.csv'
                df.to_csv(output_file, index=False)
                print(f"\n   Saved to {output_file}")
            
            # Get daily data
            print("\n4. Fetching daily aggregated data...")
            daily_data = get_sensor_days(pm25_sensor_id, '2024-01-01', '2026-01-07')
            if daily_data:
                print(f"   Retrieved {len(daily_data)} daily records")
                
                daily_df = pd.DataFrame([{
                    'date': d['period']['datetimeFrom']['utc'][:10],
                    'mean': d['value'],
                    'min': d.get('summary', {}).get('min', None),
                    'max': d.get('summary', {}).get('max', None),
                    'sd': d.get('summary', {}).get('sd', None)
                } for d in daily_data])
                
                daily_df.to_csv('real_openaq_daily.csv', index=False)
                print(f"   Saved to real_openaq_daily.csv")
                print(f"\n   Daily Stats:")
                print(f"      Mean of daily means: {daily_df['mean'].mean():.2f} µg/m³")
                print(f"      Days > 15 µg/m³ (WHO): {(daily_df['mean'] > 15).sum()} ({(daily_df['mean'] > 15).mean()*100:.1f}%)")
    
    # 3. Search for other data sources
    print("\n" + "="*60)
    print("5. Searching for historical Tashkent data...")
    print("="*60)
    
    # Try getting measurements from a broader time range
    measurements_all = []
    
    for year in [2022, 2023, 2024, 2025]:
        for month in range(1, 13):
            if year == 2025 and month > 12:
                break
            date_from = f"{year}-{month:02d}-01"
            if month == 12:
                date_to = f"{year+1}-01-01"
            else:
                date_to = f"{year}-{month+1:02d}-01"
            
            if pm25_sensor_id:
                data = get_station_measurements(pm25_sensor_id, date_from, date_to, limit=1000)
                if data:
                    measurements_all.extend(data)
                    print(f"   {year}-{month:02d}: {len(data)} measurements")
            
            time.sleep(0.1)  # Rate limiting
    
    print(f"\n   Total measurements retrieved: {len(measurements_all)}")
    
    if measurements_all:
        full_df = pd.DataFrame([{
            'datetime': m['period']['datetimeFrom']['utc'],
            'value': m['value']
        } for m in measurements_all])
        
        full_df['datetime'] = pd.to_datetime(full_df['datetime'])
        full_df = full_df.drop_duplicates()
        full_df = full_df.sort_values('datetime')
        
        print(f"   After deduplication: {len(full_df)} unique measurements")
        print(f"   Full date range: {full_df['datetime'].min()} to {full_df['datetime'].max()}")
        
        full_df.to_csv('real_openaq_all_measurements.csv', index=False)
        print(f"   Saved to real_openaq_all_measurements.csv")

    print("\n" + "="*60)
    print("Data retrieval complete!")
    print("="*60)

"""
Verify OpenAQ data source for Station 4902926
"""
import requests
import json

API_KEY = '5fbbc0ca72e78dcf70502e330f05ab29e5a2776a4a5214837ebaf687cc87aa64'
headers = {'X-API-Key': API_KEY}

# Check station details
print("=== STATION 4902926 INFO ===")
url = 'https://api.openaq.org/v3/locations/4902926'
r = requests.get(url, headers=headers)
if r.status_code == 200:
    data = r.json()
    if 'results' in data and len(data['results']) > 0:
        loc = data['results'][0]
        print(f"Name: {loc.get('name', 'N/A')}")
        print(f"Provider: {loc.get('provider', {}).get('name', 'N/A')}")
        dt_first = loc.get('datetimeFirst', {})
        dt_last = loc.get('datetimeLast', {})
        print(f"First data: {dt_first.get('utc', 'N/A') if isinstance(dt_first, dict) else dt_first}")
        print(f"Last data: {dt_last.get('utc', 'N/A') if isinstance(dt_last, dict) else dt_last}")
    else:
        print(f"No results. Response: {json.dumps(data, indent=2)[:500]}")
else:
    print(f"Error {r.status_code}: {r.text[:500]}")

# Try to get measurements from 2022
print("\n=== CHECKING 2022 DATA AVAILABILITY ===")
url = 'https://api.openaq.org/v3/locations/4902926/measurements'
params = {
    'date_from': '2022-01-01',
    'date_to': '2022-01-31',
    'limit': 10
}
r = requests.get(url, headers=headers, params=params)
if r.status_code == 200:
    data = r.json()
    results = data.get('results', [])
    print(f"Found {len(results)} measurements for Jan 2022")
    if results:
        print(f"Sample: {results[0]}")
    else:
        print("No data available for Jan 2022 from OpenAQ API")
else:
    print(f"Error {r.status_code}: {r.text[:500]}")

# Check US Embassy Station 8881 specifically
print("\n=== US EMBASSY STATION 8881 ===")
url = 'https://api.openaq.org/v3/locations/8881'
r = requests.get(url, headers=headers)
if r.status_code == 200:
    data = r.json()
    if 'results' in data and len(data['results']) > 0:
        loc = data['results'][0]
        print(f"Name: {loc.get('name', 'N/A')}")
        print(f"Provider: {loc.get('provider', {}).get('name', 'N/A')}")
        dt_first = loc.get('datetimeFirst', {})
        dt_last = loc.get('datetimeLast', {})
        print(f"First data: {dt_first.get('utc', 'N/A') if isinstance(dt_first, dict) else dt_first}")
        print(f"Last data: {dt_last.get('utc', 'N/A') if isinstance(dt_last, dict) else dt_last}")
        print(f"Country: {loc.get('country', {}).get('name', 'N/A')}")
else:
    print(f"Error: {r.text[:500]}")

# Search specifically for Uzbekistan/Tashkent stations
print("\n=== SEARCHING FOR TASHKENT STATIONS ===")
url = 'https://api.openaq.org/v3/locations'
params = {'city': 'Tashkent', 'limit': 50}
r = requests.get(url, headers=headers, params=params)
if r.status_code == 200:
    data = r.json()
    print(f"Found {len(data.get('results', []))} stations:")
    for loc in data.get('results', []):
        dt_first = loc.get('datetimeFirst', {})
        dt_last = loc.get('datetimeLast', {})
        first = dt_first.get('utc', 'N/A')[:10] if dt_first and isinstance(dt_first, dict) else 'N/A'
        last = dt_last.get('utc', 'N/A')[:10] if dt_last and isinstance(dt_last, dict) else 'N/A'
        print(f"  ID {loc.get('id')}: {loc.get('name')} - Provider: {loc.get('provider', {}).get('name', 'N/A')}")
        print(f"    Country: {loc.get('country', {}).get('name', 'N/A')}, Data: {first} to {last}")
else:
    print(f"Error: {r.text[:500]}")

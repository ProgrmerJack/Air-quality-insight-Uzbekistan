"""
Real reference-anchor layer for the global applicability map: harvest every reference-grade
(isMonitor=True) PM2.5 monitoring location from OpenAQ v3, grouped by country and city. This grounds
the "one reference anchor" requirement in actual data (anchor-agnostic: any reference-grade monitor).
Output: data/pipeline/openaq_reference_coverage.csv (country_code, n_monitors, n_cities, n_active_2023plus)
"""
import os, csv, sys, time, requests
from collections import defaultdict
from paths import pipeline_path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "data", "pipeline")
KEY = [l.split("=", 1)[1].strip().strip("'\"") for l in open(os.path.join(ROOT, ".env"), encoding="utf-8")
       if l.lower().startswith("openaq")][0]
H = {"X-API-Key": KEY}

mon = defaultdict(int); cities = defaultdict(set); active = defaultdict(int)
page = 1; total = 0
while True:
    r = requests.get("https://api.openaq.org/v3/locations",
                     params={"parameters_id": 2, "limit": 1000, "page": page}, headers=H, timeout=120)
    if r.status_code != 200:
        print("stop at page", page, r.status_code, r.text[:120]); break
    res = r.json()["results"]
    if not res: break
    for loc in res:
        if not loc.get("isMonitor"):      # reference-grade only
            continue
        cc = (loc.get("country") or {}).get("code")
        if not cc: continue
        mon[cc] += 1; total += 1
        loc_name = loc.get("locality") or f"{loc['coordinates']['latitude']:.1f},{loc['coordinates']['longitude']:.1f}"
        cities[cc].add(loc_name)
        dl = loc.get("datetimeLast") or {}
        d = dl.get("utc") or dl.get("local") or ""
        if d[:4].isdigit() and int(d[:4]) >= 2023:
            active[cc] += 1
    print(f"page {page}: +{len(res)} (running reference monitors {total}, countries {len(mon)})")
    if len(res) < 1000: break
    page += 1; time.sleep(0.3)

with open(pipeline_path("openaq_reference_coverage.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["country_code", "n_monitors", "n_cities", "n_active_2023plus"])
    for cc in sorted(mon, key=lambda c: -mon[c]):
        w.writerow([cc, mon[cc], len(cities[cc]), active[cc]])
ncountries = len(mon)
ncities = sum(len(s) for s in cities.values())
ncountries_active = sum(1 for cc in mon if active[cc] > 0)
print(f"\nReference-grade PM2.5 anchors: {total} monitors | {ncountries} countries "
      f"({ncountries_active} with a 2023+ active monitor) | ~{ncities} distinct cities/localities")
print("saved openaq_reference_coverage.csv")

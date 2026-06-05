"""Discover OpenAQ v3 PM2.5 reference locations for Central Asian capitals (key reused from repo)."""
import re, os, requests, time

root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
src = open(os.path.join(root, "scripts", "fetch", "fetch_us_embassy_2022_2023.py"), encoding="utf-8").read()
KEY = re.search(r"API_KEY\s*=\s*'([^']+)'", src).group(1)
H = {"X-API-Key": KEY}

CAPS = {
    "Almaty": (43.238, 76.889), "Astana": (51.169, 71.449),
    "Bishkek": (42.874, 74.612), "Dushanbe": (38.559, 68.787),
    "Ashgabat": (37.960, 58.326), "Tashkent": (41.311, 69.249),
}
for city, (la, lo) in CAPS.items():
    params = {"coordinates": f"{la},{lo}", "radius": 25000,
              "parameters_id": 2, "limit": 50}
    r = requests.get("https://api.openaq.org/v3/locations", headers=H, params=params, timeout=60)
    if r.status_code != 200:
        print(f"{city}: HTTP {r.status_code} {r.text[:120]}"); continue
    res = r.json().get("results", [])
    # focus on US reference monitors (AirNow / StateAir) covering the study window
    ref = [l for l in res if "airnow" in l.get("provider", {}).get("name", "").lower()]
    print(f"\n=== {city}: {len(ref)} AirNow reference station(s) of {len(res)} pm2.5 locations ===")
    for loc in (ref or res[:3]):
        dl = (loc.get("datetimeLast") or {}).get("utc", "")[:10]
        df = (loc.get("datetimeFirst") or {}).get("utc", "")[:10]
        prov = loc.get("provider", {}).get("name", "")
        name = loc.get("name", "").encode("ascii", "replace").decode()
        print(f"  id={loc['id']:>8}  {name[:30]:30} prov={prov[:16]:16} first={df} last={dl}")
    time.sleep(0.5)

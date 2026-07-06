"""
Regional GIGA authoritative school census for all Central Asian countries (beyond Tashkent).
Pulls KAZ, KGZ, TJK, TKM (UZB already pulled) and extracts each capital's school subset.
Output: data/pipeline/giga_schools_<ISO>.csv + per-capital subsets + summary.
"""
import os, csv, sys, requests
from paths import pipeline_path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "data", "pipeline")
key = [l.split("Giga schools:", 1)[1].strip() for l in open(os.path.join(ROOT, ".env"), encoding="utf-8") if l.startswith("Giga schools:")][0]
H = {"User-Agent": "npjUS-research/1.0", "Authorization": "Bearer " + key}
BASE = "https://uni-ooi-giga-maps-service.azurewebsites.net/api/v1/schools_location/country/"

COUNTRIES = ["KAZ", "KGZ", "TJK", "TKM"]
CAPITALS = {  # name: (ISO, S, W, N, E)
    "Almaty":   ("KAZ", 43.15, 76.75, 43.35, 77.05),
    "Astana":   ("KAZ", 51.00, 71.20, 51.30, 71.70),
    "Bishkek":  ("KGZ", 42.78, 74.45, 42.95, 74.75),
    "Dushanbe": ("TJK", 38.48, 68.68, 38.62, 68.88),
    "Ashgabat": ("TKM", 37.85, 58.20, 38.05, 58.55),
}

def num(x):
    try: return float(x)
    except: return None

bycountry = {}
for iso in COUNTRIES:
    r = requests.get(BASE + iso, headers=H, timeout=180)
    data = r.json().get("data", [])
    pts = [(num(s.get("latitude")), num(s.get("longitude")), s.get("school_name", "")) for s in data]
    pts = [p for p in pts if p[0] and p[1]]
    bycountry[iso] = pts
    with open(pipeline_path(f"giga_schools_{iso}.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["lat", "lon", "name"]); w.writerows(pts)
    print(f"{iso}: {len(pts):,} schools")

print("\n=== capital subsets ===")
summ = []
for cap, (iso, s, w, n, e) in CAPITALS.items():
    pts = [p for p in bycountry.get(iso, []) if s <= p[0] <= n and w <= p[1] <= e]
    with open(pipeline_path(f"giga_schools_{cap.lower()}.csv"), "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f); wr.writerow(["lat", "lon", "name"]); wr.writerows(pts)
    summ.append({"capital": cap, "iso": iso, "giga_schools": len(pts)})
    print(f"  {cap:9} ({iso}): {len(pts)} schools")
with open(pipeline_path("giga_regional_summary.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["capital", "iso", "giga_schools"]); w.writeheader(); w.writerows(summ)
print("saved giga_schools_<ISO>.csv + per-capital subsets + giga_regional_summary.csv")

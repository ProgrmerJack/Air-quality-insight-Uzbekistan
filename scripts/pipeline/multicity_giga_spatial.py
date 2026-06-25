"""
Regional school-exposure on AUTHORITATIVE GIGA schools (Dushanbe uses OSM; GIGA lacks TJK).
Per capital: GIGA schools + OSM major roads (Overpass) + objective WSF building age (windowed COG)
+ embassy-FEM background + near-road increment -> indoor classroom surface.
Output: data/pipeline/giga_regional_exposure.csv (+ per-capital CSVs).
"""
import os, csv, math, sys, time
import numpy as np, requests, rasterio
from rasterio.windows import from_bounds
from shapely.geometry import LineString, Point
from shapely.strtree import STRtree
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "data", "pipeline")
H = {"User-Agent": "npjUS-research/1.0 (academic)"}
A, L = 5.0, 150.0
WSF = "https://download.geoservice.dlr.de/WSF_EVO/files/WSFevolution_cog.tif"

# capital: (schools_csv, S,W,N,E, embassy-FEM bg)
CITIES = {
    "Tashkent": ("giga_schools_tashkent.csv", 41.15, 69.10, 41.42, 69.45, 37.9),
    "Almaty":   ("giga_schools_almaty.csv",   43.15, 76.75, 43.35, 77.05, 34.2),
    "Astana":   ("giga_schools_astana.csv",   51.00, 71.20, 51.30, 71.70, 18.5),
    "Bishkek":  ("giga_schools_bishkek.csv",  42.78, 74.45, 42.95, 74.75, 35.6),
    "Ashgabat": ("giga_schools_ashgabat.csv", 37.85, 58.20, 38.05, 58.55, 22.8),
}

def overpass(q):
    for _ in range(3):
        try:
            r = requests.post("https://overpass-api.de/api/interpreter", data={"data": q}, headers=H, timeout=180)
            if r.status_code == 200: return r.json().get("elements", [])
        except Exception: time.sleep(5)
    return []

def cohort_inf(y):
    return 0.65 if y <= 0 else (0.80 if y <= 1991 else (0.65 if y <= 2010 else 0.50))

summ = []
wsf = rasterio.open(WSF)
for city, (scsv, S, W, N, E, bg) in CITIES.items():
    p = os.path.join(OUT, scsv)
    if not os.path.exists(p): print(city, "no school file"); continue
    sch = [(float(r["lat"]), float(r["lon"])) for r in csv.DictReader(open(p, encoding="utf-8"))]
    if not sch: print(city, "0 schools"); continue
    lat0 = (S + N) / 2; mlat, mlon = 111320.0, 111320.0 * math.cos(math.radians(lat0))
    rd = overpass(f'[out:json][timeout:150];(way[highway~"^(motorway|trunk|primary)$"]({S},{W},{N},{E}););out geom;')
    lines = [LineString([(pt["lon"]*mlon, pt["lat"]*mlat) for pt in e["geometry"]]) for e in rd if e.get("geometry") and len(e["geometry"]) > 1]
    tree = STRtree(lines) if lines else None
    dist = np.array([(Point(lo*mlon, la*mlat).distance(lines[tree.nearest(Point(lo*mlon, la*mlat))]) if tree else 9999) for la, lo in sch])
    win = from_bounds(W-0.02, S-0.02, E+0.02, N+0.02, wsf.transform)
    arr = wsf.read(1, window=win); inv = ~wsf.window_transform(win); Hh, Ww = arr.shape
    infil = []
    for la, lo in sch:
        c = int(inv.a*lo+inv.b*la+inv.c); r = int(inv.d*lo+inv.e*la+inv.f)
        y = int(arr[r, c]) if (0 <= r < Hh and 0 <= c < Ww) else 0
        infil.append(cohort_inf(y))
    infil = np.array(infil)
    indoor = (bg + A*np.exp(-dist/L)) * infil
    with open(os.path.join(OUT, f"giga_exposure_{city.lower()}.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["lat","lon","dist_m","infiltration","indoor_pm25"])
        for i,(la,lo) in enumerate(sch): w.writerow([f"{la:.5f}",f"{lo:.5f}",f"{dist[i]:.0f}",infil[i],f"{indoor[i]:.1f}"])
    summ.append({"capital": city, "bg": bg, "n_schools": len(sch),
                 "pct_soviet": round(100*(infil==0.80).mean(),1), "pct_within_100m": round(100*(dist<=100).mean(),1),
                 "indoor_min": round(indoor.min(),1), "indoor_max": round(indoor.max(),1), "indoor_mean": round(indoor.mean(),1)})
    print(f"  {city:9} GIGA n={len(sch):>3} Soviet {summ[-1]['pct_soviet']:>4}% <=100m {summ[-1]['pct_within_100m']:>4}% indoor {indoor.min():.1f}-{indoor.max():.1f}")
    time.sleep(1)
wsf.close()
with open(os.path.join(OUT, "giga_regional_exposure.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(summ[0].keys())); w.writeheader(); w.writerows(summ)
print("saved giga_regional_exposure.csv (Dushanbe: use OSM b1d, GIGA lacks TJK)")

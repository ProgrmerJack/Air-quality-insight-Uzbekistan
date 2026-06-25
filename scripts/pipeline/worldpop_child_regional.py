"""
REAL WorldPop under-20 child counts per school for ALL SIX Central Asian capitals (consistent method).
Uses the 1 km age-sex product (Global_2000_2020_1km/unconstrained/2020). For each country, downloads each
under-20 band once (f/m x ages 0,1,5,10,15), windowed-clips to every capital AOI in that country,
accumulates the under-20 grid, then deletes the file. Samples the under-20 count of the ~1 km cell
containing each school. Output: data/pipeline/child_regional.csv  (city, lat, lon, child_u20).
"""
import os, csv, sys, requests
import numpy as np, rasterio
from rasterio.windows import from_bounds
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "data", "pipeline")
TMP = os.path.join(OUT, "_wp_tmp"); os.makedirs(TMP, exist_ok=True)
BASE = "https://data.worldpop.org/GIS/AgeSex_structures/Global_2000_2020_1km/unconstrained/2020/{I}/{i}_{s}_{a}_2020_1km.tif"
AGES = [0, 1, 5, 10, 15]          # under-20 bands
H = {"User-Agent": "npjUS-research/1.0"}

# city -> (ISO, exposure_csv with lat/lon school coords)
CITIES = {
    "Tashkent": ("UZB", os.path.join(OUT, "giga_exposure_tashkent.csv")),
    "Almaty":   ("KAZ", os.path.join(OUT, "giga_exposure_almaty.csv")),
    "Astana":   ("KAZ", os.path.join(OUT, "giga_exposure_astana.csv")),
    "Bishkek":  ("KGZ", os.path.join(OUT, "giga_exposure_bishkek.csv")),
    "Ashgabat": ("TKM", os.path.join(OUT, "giga_exposure_ashgabat.csv")),
    "Dushanbe": ("TJK", os.path.normpath(os.path.join(ROOT, "scripts", "legacy_v1", "b1d_dushanbe_school_exposure.csv"))),
}

# load school coords + per-city AOI (school bbox + 0.05 deg buffer)
schools = {}; aoi = {}
for city, (iso, p) in CITIES.items():
    rows = list(csv.DictReader(open(p, encoding="utf-8")))
    la = np.array([float(r["lat"]) for r in rows]); lo = np.array([float(r["lon"]) for r in rows])
    schools[city] = (la, lo)
    aoi[city] = (lo.min()-0.05, la.min()-0.05, lo.max()+0.05, la.max()+0.05)  # W,S,E,N
    print(f"{city:9} {iso}  n={len(rows):>3}  AOI {aoi[city][0]:.2f},{aoi[city][1]:.2f} -> {aoi[city][2]:.2f},{aoi[city][3]:.2f}")

# group cities by ISO so each country's bands download once
iso_cities = {}
for city, (iso, _) in CITIES.items():
    iso_cities.setdefault(iso, []).append(city)

acc = {city: None for city in CITIES}; trans = {city: None for city in CITIES}
for iso, cities in iso_cities.items():
    print(f"\n=== {iso}  (cities: {', '.join(cities)}) ===")
    for s in ("f", "m"):
        for a in AGES:
            url = BASE.format(I=iso, i=iso.lower(), s=s, a=a)
            fp = os.path.join(TMP, f"{iso.lower()}_{s}_{a}.tif")
            if not os.path.exists(fp):
                with requests.get(url, headers=H, stream=True, timeout=900) as r:
                    r.raise_for_status()
                    with open(fp, "wb") as o:
                        for chunk in r.iter_content(1 << 20): o.write(chunk)
            with rasterio.open(fp) as ds:
                for city in cities:
                    W, S, E, N = aoi[city]
                    win = from_bounds(W, S, E, N, ds.transform)
                    arr = ds.read(1, window=win); arr = np.where(arr < 0, 0, arr).astype("float64")
                    if acc[city] is None:
                        acc[city] = arr; trans[city] = ds.window_transform(win)
                    else:
                        acc[city] += arr
            os.remove(fp)
        print(f"  {iso} {s}-bands done")

# sample under-20 at each school (cell value containing the school)
with open(os.path.join(OUT, "child_regional.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["city", "lat", "lon", "child_u20"])
    for city in CITIES:
        la, lo = schools[city]; A = acc[city]; inv = ~trans[city]; Hh, Ww = A.shape
        tot = 0.0
        for laa, loo in zip(la, lo):
            c = int(inv.a*loo + inv.b*laa + inv.c); r = int(inv.d*loo + inv.e*laa + inv.f)
            v = float(A[r, c]) if (0 <= r < Hh and 0 <= c < Ww) else 0.0
            w.writerow([city, f"{laa:.5f}", f"{loo:.5f}", round(v, 1)]); tot += v
        print(f"{city:9} metro under-20 (AOI) ~{int(A.sum()):>8} | mean per-school cell {tot/len(la):.1f}")
print("\nsaved data/pipeline/child_regional.csv")

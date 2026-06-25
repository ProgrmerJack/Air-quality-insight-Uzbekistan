"""
Injustice/Retrofit-Priority Index on the AUTHORITATIVE GIGA school census (Tashkent, n=434),
re-sampling every layer at GIGA points: near-road (OSM roads), objective building age (WSF
windowed COG), neighbourhood wealth (Meta RWI), child/pop density (WorldPop grid).
Output: data/pipeline/giga_school_injustice_index.csv
"""
import os, csv, math, sys
import numpy as np, rasterio
from rasterio.windows import from_bounds
from shapely.geometry import LineString, Point
from shapely.strtree import STRtree
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCH = os.path.join(ROOT, "data", "pipeline", "giga_schools_tashkent.csv")
ROADS = os.path.join(ROOT, "scripts", "legacy_v1", "tashkent_major_roads_osm.csv")
RWIF = os.path.join(ROOT, "data", "pipeline", "tashkent_rwi.csv")
POPF = os.path.join(ROOT, "data", "pipeline", "tashkent_pop_grid.csv")
OUT = os.path.join(ROOT, "data", "pipeline", "giga_school_injustice_index.csv")
BG, A, L, LAT0 = 37.9, 5.0, 150.0, 41.31
MLAT, MLON = 111320.0, 111320.0 * math.cos(math.radians(LAT0))

sch = list(csv.DictReader(open(SCH, encoding="utf-8")))
lat = np.array([float(s["lat"]) for s in sch]); lon = np.array([float(s["lon"]) for s in sch])

# near-road distance (reconstruct OSM major-road lines)
ways = {}
for r in csv.DictReader(open(ROADS, encoding="utf-8")):
    ways.setdefault(r["way_id"], []).append((float(r["lon"]) * MLON, float(r["lat"]) * MLAT))
lines = [LineString(v) for v in ways.values() if len(v) >= 2]
tree = STRtree(lines)
dist = np.array([Point(lo*MLON, la*MLAT).distance(lines[tree.nearest(Point(lo*MLON, la*MLAT))]) for la, lo in zip(lat, lon)])

# objective building age (WSF windowed COG)
with rasterio.open("https://download.geoservice.dlr.de/WSF_EVO/files/WSFevolution_cog.tif") as ds:
    win = from_bounds(69.08, 41.13, 69.47, 41.44, ds.transform)
    arr = ds.read(1, window=win); inv = ~ds.window_transform(win); Hh, Ww = arr.shape
def infil_of(la, lo):
    c = int(inv.a*lo + inv.b*la + inv.c); r = int(inv.d*lo + inv.e*la + inv.f)
    y = int(arr[r, c]) if (0 <= r < Hh and 0 <= c < Ww) else 0
    return 0.65 if y <= 0 else (0.80 if y <= 1991 else (0.65 if y <= 2010 else 0.50))
infil = np.array([infil_of(la, lo) for la, lo in zip(lat, lon)])

# wealth (nearest RWI) + REAL under-20 child counts per school (WorldPop, school-aligned)
rwi = [(float(r["lat"]), float(r["lon"]), float(r["rwi"])) for r in csv.DictReader(open(RWIF, encoding="utf-8"))]
def near(lst, la, lo):
    return min(lst, key=lambda t: (t[0]-la)**2 + ((t[1]-lo)*math.cos(math.radians(la)))**2)[2]
rwi_at = np.array([near(rwi, la, lo) for la, lo in zip(lat, lon)])
child = list(csv.DictReader(open(os.path.join(ROOT, "data", "pipeline", "school_child_pop.csv"), encoding="utf-8")))
assert len(child) == len(sch), "child file must be school-aligned"
dens_at = np.array([float(c["child_u20_500m"]) for c in child])   # WorldPop under-20 children within ~500 m

outdoor = BG + A*np.exp(-dist/L); indoor = outdoor*infil
def norm(x): x = np.asarray(x, float); return (x-x.min())/(x.max()-x.min()) if x.max() > x.min() else x*0
index = (norm(indoor) + norm(infil) + norm(-rwi_at) + norm(dens_at)) / 4.0

oe = np.argsort(-indoor); oi = np.argsort(-index); k = max(1, len(sch)//10)
overlap = len(set(oe[:k].tolist()) & set(oi[:k].tolist()))
from scipy.stats import spearmanr
print(f"GIGA Tashkent schools: {len(sch)} | Soviet-era (infil 0.80): {int((infil==0.80).sum())} ({100*(infil==0.80).mean():.0f}%)")
print(f"near-road <=100m: {int((dist<=100).sum())} ({100*(dist<=100).mean():.1f}%) | indoor {indoor.min():.1f}-{indoor.max():.1f}")
print(f"top-decile (n={k}) exposure-only vs index overlap = {overlap}/{k} -> {k-overlap} enter via equity; Spearman {spearmanr(indoor,index).correlation:.2f}")
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["lat","lon","name","dist_m","infiltration","rwi","dens_km2","indoor_pm25","injustice_index"])
    for i, s in enumerate(sch):
        w.writerow([f"{lat[i]:.5f}", f"{lon[i]:.5f}", s["name"][:40], f"{dist[i]:.0f}", infil[i], f"{rwi_at[i]:.2f}", f"{dens_at[i]:.0f}", f"{indoor[i]:.1f}", f"{index[i]:.3f}"])
print("saved", OUT)

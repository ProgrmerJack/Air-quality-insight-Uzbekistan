"""
Step 3 (objective building-age) -- WSF Evolution settlement-year per school via SMART windowed
COG read (only the Tashkent AOI bytes are fetched from the global COG). Replaces the assumed
60/30/10 Soviet/1990s/post-2010 split with a measured construction-era cohort per school.

Source: DLR WSF Evolution global COG (settlement year 1985-2015, 30 m).
Output: data/pipeline/school_building_age.csv  (+ infiltration assigned objectively)
"""
import os, csv
import numpy as np
import rasterio
from rasterio.windows import from_bounds
from paths import pipeline_path

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
COG = "https://download.geoservice.dlr.de/WSF_EVO/files/WSFevolution_cog.tif"
SCHOOLS = os.path.join(ROOT, "scripts", "legacy_v1", "b1_school_results.csv")
OUT = pipeline_path("school_building_age.csv")
W, S, E, N = 69.08, 41.13, 69.47, 41.44   # Tashkent AOI (slightly padded)

rows = list(csv.DictReader(open(SCHOOLS, encoding="utf-8")))
lons = np.array([float(r["lon"]) for r in rows]); lats = np.array([float(r["lat"]) for r in rows])

with rasterio.open(COG) as ds:
    print("WSF EVO:", ds.crs, ds.width, "x", ds.height, "dtype", ds.dtypes[0])
    win = from_bounds(W, S, E, N, ds.transform)
    arr = ds.read(1, window=win)                 # ONLY the AOI is transferred (windowed range read)
    wt = ds.window_transform(win)
    print("AOI window read:", arr.shape, "settlement-year range", int(arr[arr > 0].min()), "-", int(arr.max()))
    inv = ~wt
    cols = (inv.a * lons + inv.b * lats + inv.c).astype(int)
    r_ = (inv.d * lons + inv.e * lats + inv.f).astype(int)

def cohort(y):
    if y <= 0: return "unknown", 0.65          # nodata -> typical
    if y <= 1991: return "Soviet (<=1991)", 0.80
    if y <= 2010: return "1992-2010", 0.65
    return "post-2010", 0.50

years, coh, infil = [], [], []
H, Wd = arr.shape
for rr, cc in zip(r_, cols):
    y = int(arr[rr, cc]) if (0 <= rr < H and 0 <= cc < Wd) else 0
    c, fi = cohort(y); years.append(y); coh.append(c); infil.append(fi)

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["lat", "lon", "settlement_year", "cohort", "infiltration_obj"])
    for i in range(len(rows)):
        w.writerow([f"{lats[i]:.5f}", f"{lons[i]:.5f}", years[i], coh[i], infil[i]])

from collections import Counter
ct = Counter(coh)
print("cohort distribution:", dict(ct))
print(f"objective infiltration mean {np.mean(infil):.3f} (vs assumed 0.71)")
print("saved", OUT)

"""
WorldPop child-specific (<20) population per school via SMART windowed COG reads (only the Tashkent
AOI is fetched from each global age-sex raster). Replaces the total-population-density proxy.
Sums age bands 0,1,5,10,15 (i.e., 0-19) x {f,m} = under-20, consistent with the GBD <20 baseline.
Output: data/pipeline/school_child_pop.csv
"""
import os, csv, sys
import numpy as np, rasterio
from rasterio.windows import from_bounds
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCH = os.path.join(ROOT, "scripts", "legacy_v1", "b1_school_results.csv")
OUT = os.path.join(ROOT, "data", "pipeline", "school_child_pop.csv")
BASE = "https://data.worldpop.org/GIS/AgeSex_structures/Global_2000_2020/2020/UZB/uzb_{s}_{a}_2020.tif"
AGES = [0, 1, 5, 10, 15]   # 0-19
W, S, E, N = 69.08, 41.13, 69.47, 41.44

acc = None; transform = None
for s in ("f", "m"):
    for a in AGES:
        url = BASE.format(s=s, a=a)
        with rasterio.open(url) as ds:
            win = from_bounds(W, S, E, N, ds.transform)
            arr = ds.read(1, window=win)
            arr = np.where(arr < 0, 0, arr)
            if acc is None:
                acc = arr.astype("float64"); transform = ds.window_transform(win)
            else:
                acc = acc + arr
        print(f"  added {s}_{a}")
print("under-20 grid:", acc.shape, "metro child total ~", int(acc.sum()))

rows = list(csv.DictReader(open(SCH, encoding="utf-8")))
inv = ~transform
H, Wd = acc.shape
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["lat", "lon", "child_u20_100m", "child_u20_500m"])
    for r in rows:
        lo, la = float(r["lon"]), float(r["lat"])
        c = int(inv.a * lo + inv.b * la + inv.c); rr = int(inv.d * lo + inv.e * la + inv.f)
        cell = float(acc[rr, c]) if (0 <= rr < H and 0 <= c < Wd) else 0.0
        # ~500 m buffer = 5x5 cells (100 m grid)
        r0, r1, c0, c1 = max(0, rr-2), min(H, rr+3), max(0, c-2), min(Wd, c+3)
        buf = float(acc[r0:r1, c0:c1].sum())
        w.writerow([f"{la:.5f}", f"{lo:.5f}", round(cell, 1), round(buf, 1)])
print("saved", OUT)

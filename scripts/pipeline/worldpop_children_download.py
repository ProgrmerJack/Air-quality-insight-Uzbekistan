"""
WorldPop under-20 child counts per school -- DOWNLOAD whole age-sex rasters one by one (server has
no range reads), clip each to the Tashkent AOI from the LOCAL file (windowed), accumulate, delete the
big file. Keeps only the compact result. Samples at GIGA Tashkent schools.
Output: data/pipeline/school_child_pop.csv
"""
import os, csv, sys, requests
import numpy as np, rasterio
from rasterio.windows import from_bounds
from paths import pipeline_path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TMP = os.path.join(ROOT, "data", "pipeline", "cache", "_worldpop_tmp"); os.makedirs(TMP, exist_ok=True)
SCH = pipeline_path("giga_schools_tashkent.csv")
OUT = pipeline_path("school_child_pop.csv")
BASE = "https://data.worldpop.org/GIS/AgeSex_structures/Global_2000_2020/2020/UZB/uzb_{s}_{a}_2020.tif"
AGES = [0, 1, 5, 10, 15]; W, S, E, N = 69.08, 41.13, 69.47, 41.44
H = {"User-Agent": "npjUS-research/1.0"}

acc = None; transform = None
for s in ("f", "m"):
    for a in AGES:
        url = BASE.format(s=s, a=a); fp = os.path.join(TMP, f"uzb_{s}_{a}.tif")
        if not os.path.exists(fp):
            with requests.get(url, headers=H, stream=True, timeout=600) as r:
                r.raise_for_status()
                with open(fp, "wb") as out:
                    for chunk in r.iter_content(1 << 20): out.write(chunk)
        with rasterio.open(fp) as ds:                       # local file -> windowed read works
            win = from_bounds(W, S, E, N, ds.transform)
            arr = np.where(ds.read(1, window=win) < 0, 0, ds.read(1, window=win)).astype("float64")
            if acc is None: acc = arr; transform = ds.window_transform(win)
            else: acc = acc + arr
        os.remove(fp)                                       # delete the 237 MB file, keep only AOI sum
        print(f"  {s}_{a} done; running metro child total ~{int(acc.sum())}")
print("under-20 grid:", acc.shape, "Tashkent-metro child total ~", int(acc.sum()))

rows = list(csv.DictReader(open(SCH, encoding="utf-8"))); inv = ~transform; Hh, Ww = acc.shape
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["lat", "lon", "child_u20_100m", "child_u20_500m"])
    for r in rows:
        lo, la = float(r["lon"]), float(r["lat"])
        c = int(inv.a*lo + inv.b*la + inv.c); rr = int(inv.d*lo + inv.e*la + inv.f)
        cell = float(acc[rr, c]) if (0 <= rr < Hh and 0 <= c < Ww) else 0.0
        r0, r1, c0, c1 = max(0, rr-2), min(Hh, rr+3), max(0, c-2), min(Ww, c+3)
        w.writerow([f"{la:.5f}", f"{lo:.5f}", round(cell, 1), round(float(acc[r0:r1, c0:c1].sum()), 1)])
print("saved", OUT)

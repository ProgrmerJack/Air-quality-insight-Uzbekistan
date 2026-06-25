"""
Re-run the near-road NO2 validation on the AUTHORITATIVE GIGA Tashkent census (n=434) so the
NO2 check uses the same school set as the census/exposure/equity analysis (resolves the 434-vs-605
inconsistency). Samples Sentinel-5P/TROPOMI 2022 annual-mean tropospheric NO2 at each GIGA school
(GEE via local ADC) and splits by the road distance already in giga_exposure_tashkent.csv.
Output: data/pipeline/school_no2_giga.csv  (+ printed near-road stats)
"""
import os, csv, sys
import numpy as np
from scipy.stats import spearmanr
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import ee
ee.Initialize(project="project-6304b1d4-77dd-4f92-823")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCH = os.path.join(ROOT, "data", "pipeline", "giga_exposure_tashkent.csv")
OUT = os.path.join(ROOT, "data", "pipeline", "school_no2_giga.csv")

rows = list(csv.DictReader(open(SCH, encoding="utf-8")))
feats = [ee.Feature(ee.Geometry.Point([float(r["lon"]), float(r["lat"])]), {"i": i})
         for i, r in enumerate(rows)]
fc = ee.FeatureCollection(feats)
annual = (ee.ImageCollection("COPERNICUS/S5P/OFFL/L3_NO2")
          .select("tropospheric_NO2_column_number_density")
          .filterDate("2022-01-01", "2022-12-31").mean())
sampled = annual.sampleRegions(collection=fc, scale=1000, geometries=False).getInfo()

no2_by_i = {}
for f in sampled["features"]:
    p = f["properties"]
    if p.get("tropospheric_NO2_column_number_density") is not None:
        no2_by_i[int(p["i"])] = p["tropospheric_NO2_column_number_density"] * 1e6   # mol/m2 -> umol/m2

dist, no2 = [], []
with open(OUT, "w", newline="", encoding="utf-8") as fo:
    w = csv.writer(fo); w.writerow(["school_i", "dist_m", "no2_umol_m2"])
    for i, r in enumerate(rows):
        if i in no2_by_i:
            d = float(r["dist_m"]); v = round(no2_by_i[i], 1)
            w.writerow([i, int(d), v]); dist.append(d); no2.append(v)
dist = np.array(dist); no2 = np.array(no2)
near = no2[dist <= 100]; far = no2[dist > 100]
print(f"GIGA schools with NO2: {len(no2)}/{len(rows)}")
print(f"<=100 m mean {near.mean():.0f} (n={len(near)}) | >100 m mean {far.mean():.0f} | "
      f"Spearman(dist,NO2) {spearmanr(dist,no2).correlation:.2f}")
print(f"pct within 100 m: {100*(dist<=100).mean():.1f}%")
print("saved", OUT)

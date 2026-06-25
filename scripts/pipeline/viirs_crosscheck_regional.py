"""
Independent-deprivation cross-check across ALL SIX capitals (not just Tashkent): re-run the equity
reprioritisation with VIIRS night-time lights replacing Meta RWI. If the ">=half reprioritise" finding
holds under an independent disadvantage layer in every city, it is a real result, not an RWI artifact.
Output: data/pipeline/viirs_crosscheck_regional.csv
"""
import os, csv, sys
import numpy as np
from scipy.stats import spearmanr
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import ee
ee.Initialize(project="project-6304b1d4-77dd-4f92-823")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "data", "pipeline")
CITIES = ["Tashkent", "Almaty", "Astana", "Bishkek", "Ashgabat", "Dushanbe"]
def norm(x): x = np.asarray(x, float); return (x-x.min())/(x.max()-x.min()) if x.max() > x.min() else x*0
viirs = (ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG").filterDate("2022-01-01","2022-12-31")
         .select("avg_rad").mean())

rows = []
for city in CITIES:
    d = list(csv.DictReader(open(os.path.join(OUT, f"regional_index_{city.lower()}.csv"), encoding="utf-8")))
    lat = np.array([float(r["lat"]) for r in d]); lon = np.array([float(r["lon"]) for r in d])
    indoor = np.array([float(r["indoor_pm25"]) for r in d]); infil = np.array([float(r["infiltration"]) for r in d])
    rwi = np.array([float(r["rwi"]) for r in d]); child = np.array([float(r["child_u20"]) for r in d])
    feats = [ee.Feature(ee.Geometry.Point([float(lon[i]), float(lat[i])]), {"i": i}) for i in range(len(d))]
    samp = viirs.sampleRegions(collection=ee.FeatureCollection(feats), scale=500, geometries=False).getInfo()
    ntl = np.full(len(d), np.nan)
    for f in samp["features"]:
        p = f["properties"]
        if p.get("avg_rad") is not None: ntl[int(p["i"])] = p["avg_rad"]
    ntl = np.where(np.isnan(ntl), np.nanmedian(ntl[~np.isnan(ntl)]), ntl)
    disadv = -np.log1p(np.clip(ntl, 0, None))
    k = max(1, len(d)//10); oe = set(np.argsort(-indoor)[:k].tolist())
    idx_rwi = (norm(indoor)+norm(infil)+norm(-rwi)+norm(child))/4.0
    idx_ntl = (norm(indoor)+norm(infil)+norm(disadv)+norm(child))/4.0
    via_rwi = k-len(oe & set(np.argsort(-idx_rwi)[:k].tolist()))
    via_ntl = k-len(oe & set(np.argsort(-idx_ntl)[:k].tolist()))
    agree = len(set(np.argsort(-idx_rwi)[:k].tolist()) & set(np.argsort(-idx_ntl)[:k].tolist()))
    rho_layers = spearmanr(rwi, ntl).correlation
    rho_idx = spearmanr(idx_rwi, idx_ntl).correlation
    rows.append({"capital": city, "k": k, "via_rwi": f"{via_rwi}/{k}", "via_viirs": f"{via_ntl}/{k}",
                 "topdecile_agree": f"{agree}/{k}", "rho_rwi_viirs": round(rho_layers,2), "rho_index": round(rho_idx,2)})
    print(f"{city:9} k={k:>2} | RWI {via_rwi}/{k} | VIIRS {via_ntl}/{k} | agree {agree}/{k} | "
          f"rho(RWI,VIIRS) {rho_layers:.2f} | rho(idx) {rho_idx:.2f}")
with open(os.path.join(OUT, "viirs_crosscheck_regional.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print("saved viirs_crosscheck_regional.csv")

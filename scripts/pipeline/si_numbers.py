import os, csv, math
import numpy as np
ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
D = os.path.join(ROOT, "data", "pipeline")

# --- near-road NO2 split ---
rows = list(csv.DictReader(open(os.path.join(D, "school_no2.csv"), encoding="utf-8")))
d = np.array([float(r["dist_m"]) for r in rows])
no2 = np.array([float(r["no2_umol_m2"]) for r in rows])
near = no2[d <= 100]; far = no2[d > 100]
from scipy.stats import spearmanr
print(f"NO2 schools n={len(rows)} | <=100m mean {near.mean():.0f} (n={len(near)}) | >100m mean {far.mean():.0f} | Spearman(dist,NO2) {spearmanr(d,no2).correlation:.2f}")

# --- GIGA injustice index overlap (Tashkent, real child density) ---
gi = os.path.join(D, "giga_school_injustice_index.csv")
if os.path.exists(gi):
    g = list(csv.DictReader(open(gi, encoding="utf-8")))
    indoor = np.array([float(x["indoor_pm25"]) for x in g])
    idx = np.array([float(x["injustice_index"]) for x in g])
    k = max(1, len(g)//10)
    oe = set(np.argsort(-indoor)[:k].tolist()); oi = set(np.argsort(-idx)[:k].tolist())
    ov = len(oe & oi)
    print(f"GIGA Tashkent index: n={len(g)} top-decile k={k} | overlap {ov}/{k} -> {k-ov} via equity")

# --- ERA5 inversion (monthly BLH) ---
try:
    import xarray as xr
    ds = xr.open_dataset(os.path.join(D, "era5_tashkent_monthly.nc"))
    print("ERA5 vars:", list(ds.data_vars))
    blvar = [v for v in ds.data_vars if "bl" in v.lower() or "blh" in v.lower()]
    print("ERA5 candidate BLH vars:", blvar)
    for v in ds.data_vars:
        arr = ds[v].values.flatten()
        arr = arr[~np.isnan(arr)]
        if len(arr):
            print(f"  {v}: min {arr.min():.1f} max {arr.max():.1f} mean {arr.mean():.1f}")
except Exception as e:
    print("ERA5 read skipped:", e)

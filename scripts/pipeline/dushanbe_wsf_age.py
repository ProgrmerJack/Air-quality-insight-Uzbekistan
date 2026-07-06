"""Fill the Dushanbe building-age gap: GIGA-200m fraction for Tashkent + WSF Evolution Soviet-era
from paths import pipeline_path
share at the 178 Dushanbe OSM schools (windowed remote COG read)."""
import os, csv, sys
import numpy as np, rasterio
from rasterio.windows import from_bounds
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
D = os.path.join(ROOT, "data", "pipeline")

# Tashkent GIGA 200 m fraction
t = list(csv.DictReader(open(pipeline_path("giga_exposure_tashkent.csv"), encoding="utf-8")))
dist = np.array([float(r["dist_m"]) for r in t])
print(f"Tashkent GIGA: within 100 m {100*(dist<=100).mean():.1f}% | within 200 m {100*(dist<=200).mean():.1f}% | median {np.median(dist):.0f} m")

# Dushanbe WSF Evolution building age
dush = list(csv.DictReader(open(os.path.normpath(os.path.join(ROOT, "scripts", "legacy_v1", "b1d_dushanbe_school_exposure.csv")), encoding="utf-8")))
la = np.array([float(r["lat"]) for r in dush]); lo = np.array([float(r["lon"]) for r in dush])
W, S, E, N = lo.min()-0.02, la.min()-0.02, lo.max()+0.02, la.max()+0.02
os.environ["GDAL_HTTP_USERAGENT"] = "npjUS-research/1.0"
with rasterio.open("https://download.geoservice.dlr.de/WSF_EVO/files/WSFevolution_cog.tif") as ds:
    win = from_bounds(W, S, E, N, ds.transform)
    arr = ds.read(1, window=win); inv = ~ds.window_transform(win); Hh, Ww = arr.shape
def yr(laa, loo):
    c = int(inv.a*loo + inv.b*laa + inv.c); r = int(inv.d*loo + inv.e*laa + inv.f)
    return int(arr[r, c]) if (0 <= r < Hh and 0 <= c < Ww) else 0
years = np.array([yr(a, b) for a, b in zip(la, lo)])
soviet = (years > 0) & (years <= 1991)
built = years > 0
print(f"Dushanbe schools n={len(dush)} | WSF-detected built {built.sum()} | Soviet-era (<=1991) {soviet.sum()} "
      f"= {100*soviet.sum()/max(1,built.sum()):.0f}% of detected ({100*soviet.mean():.0f}% of all)")

"""
ERA5 boundary-layer height + 2m temperature over Tashkent (Copernicus CDS) to substantiate the
winter-inversion mechanism quantitatively. Uses the CDS key from .env (//cds keys).
Output: data/pipeline/era5_tashkent_monthly.nc  + a compact CSV summary.
"""
import os, cdsapi
from paths import pipeline_path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
env = {}
for line in open(os.path.join(ROOT, ".env"), encoding="utf-8"):
    if line.strip().startswith("url:"): env["url"] = line.split("url:", 1)[1].strip()
    if line.strip().startswith("key:"): env["key"] = line.split("key:", 1)[1].strip()
OUT = pipeline_path("era5_tashkent_monthly.nc")

c = cdsapi.Client(url=env["url"], key=env["key"])
c.retrieve("reanalysis-era5-single-levels-monthly-means", {
    "product_type": "monthly_averaged_reanalysis",
    "variable": ["boundary_layer_height", "2m_temperature"],
    "year": ["2022", "2023"],
    "month": [f"{m:02d}" for m in range(1, 13)],
    "time": "00:00",
    "area": [42, 69, 41, 70],   # N, W, S, E around Tashkent
    "format": "netcdf",
}, OUT)
print("saved", OUT)

# compact summary: winter vs summer boundary-layer height
import xarray as xr, numpy as np
ds = xr.open_dataset(OUT)
blh = ds["blh"] if "blh" in ds else ds[[v for v in ds.data_vars if "boundary" in v.lower() or v == "blh"][0]]
m = blh.mean(dim=[d for d in blh.dims if d not in ("time", "valid_time")])
print("ERA5 boundary-layer height (m), monthly mean over Tashkent:")
print(m.to_series().round(0).to_string())

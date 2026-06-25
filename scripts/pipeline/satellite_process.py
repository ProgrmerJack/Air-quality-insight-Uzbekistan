"""
Step 4 (satellite fusion) -- SMART processing scaffold.

Why scaffold: ACAG surface-PM2.5 is distributed as large global NetCDF via WashU Box (no public
direct URL / OPeNDAP), and Sentinel-5P/TROPOMI NO2 needs Google Earth Engine / Sentinel-Hub auth.
Neither is pullable head-less here. This script does the SMART part once the file/credential exists:
clip to the Central Asia AOI and write a compact, science-standard NetCDF + CSV (MBs, not GBs).

ACAG (download once): https://sites.wustl.edu/acag/datasets/surface-pm2-5/  (V5.GL.05.02, 0.01 deg, monthly)
  -> place the annual/monthly .nc in data/pipeline/acag/  then run this.
TROPOMI NO2: use GEE collection COPERNICUS/S5P/OFFL/L3_NO2 (tropospheric_NO2_column_number_density),
  export a Tashkent-AOI annual-mean GeoTIFF, then read with rioxarray (after GDAL install).
"""
import os, glob
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ACAG_DIR = os.path.join(ROOT, "data", "pipeline", "acag")
AOI = dict(lat=(37.0, 52.0), lon=(58.0, 78.0))   # Central Asia capitals bbox
TASHKENT = dict(lat=(41.15, 41.42), lon=(69.10, 69.45))

def clip_acag():
    import xarray as xr  # xarray + netCDF4 ARE installed here -> NetCDF works without rasterio
    files = glob.glob(os.path.join(ACAG_DIR, "*.nc"))
    if not files:
        print("No ACAG .nc in data/pipeline/acag/ -- download first (see header)."); return
    for fp in files:
        ds = xr.open_dataset(fp)
        latn = "lat" if "lat" in ds else ("latitude" if "latitude" in ds else list(ds.dims)[0])
        lonn = "lon" if "lon" in ds else ("longitude" if "longitude" in ds else list(ds.dims)[1])
        sub = ds.sel({latn: slice(*AOI["lat"]), lonn: slice(*AOI["lon"])})
        out = fp.replace(".nc", "_centralasia.nc")
        sub.to_netcdf(out)  # compact AOI NetCDF (science-standard, MBs)
        # also a tidy CSV of the variable at AOI
        var = [v for v in sub.data_vars][0]
        df = sub[var].to_dataframe().reset_index().dropna()
        df.to_csv(fp.replace(".nc", "_centralasia.csv"), index=False)
        print(f"clipped {os.path.basename(fp)} -> {os.path.basename(out)} ({len(df)} cells)")

if __name__ == "__main__":
    clip_acag()

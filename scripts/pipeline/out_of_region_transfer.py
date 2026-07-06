"""
Out-of-region transferability stress test: run the IDENTICAL pipeline in three cities on three other
continents (Accra, Ghana; Kathmandu, Nepal; Lima, Peru), each with a reference anchor in OpenAQ and
authoritative GIGA schools. Fully global inputs, all via GEE + GIGA + the WSF COG (no OSM dependency):
GIGA schools; TROPOMI NO2 as the within-city traffic/combustion exposure gradient (validated against
near-road in Tashkent, Spearman -0.34); WSF Evolution building age; WorldPop under-20 child density;
and VIIRS night-time lights as the disadvantage proxy (the RWI substitute validated in Tashkent,
Spearman 0.77). Reports the top-decile equity reprioritisation -- the same headline as Central Asia.
Output: data/pipeline/out_of_region_transfer.csv
"""
import os, csv, sys, math, requests
import numpy as np, rasterio
from rasterio.windows import from_bounds
from scipy.stats import spearmanr
from paths import pipeline_path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import ee
ee.Initialize(project="project-6304b1d4-77dd-4f92-823")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "data", "pipeline")
def load_env(p):
    d = {}
    for line in open(p, encoding="utf-8"):
        if ":" in line and not line.strip().startswith("//"):
            k, v = line.split(":", 1); d[k.strip().lower()] = v.strip()
    return d
GK = (load_env(os.path.join(ROOT, ".env")).get("giga schools") or load_env(os.path.join(ROOT, ".env")).get("giga"))
GH = {"User-Agent": "npjUS/1.0", "Authorization": "Bearer " + GK}

# city: iso3, bbox (W,S,E,N), nominal reference background (context only; does not affect reprioritisation)
CITIES = {
    "Accra":     ("GHA", (-0.32, 5.50, -0.05, 5.72), 27.0),
    "Kathmandu": ("NPL", (85.25, 27.65, 85.45, 27.78), 49.0),
    "Lima":      ("PER", (-77.15, -12.20, -76.80, -11.90), 24.0),
}
A = 5.0
def norm(x): x = np.asarray(x, float); return (x-x.min())/(x.max()-x.min()) if x.max() > x.min() else x*0

rows = []
for city, (iso, (W, S, E, N), bg) in CITIES.items():
    print(f"\n=== {city} ({iso}) ===")
    # 1) GIGA schools -> city bbox
    data = requests.get(f"https://uni-ooi-giga-maps-service.azurewebsites.net/api/v1/schools_location/country/{iso}",
                        headers=GH, timeout=300).json()["data"]
    pts = [(float(d["latitude"]), float(d["longitude"])) for d in data
           if d.get("latitude") and d.get("longitude") and W <= float(d["longitude"]) <= E and S <= float(d["latitude"]) <= N]
    if len(pts) > 600:
        idx = np.random.default_rng(0).choice(len(pts), 600, replace=False); pts = [pts[i] for i in idx]
    lat = np.array([p[0] for p in pts]); lon = np.array([p[1] for p in pts])
    print(f"  GIGA schools in bbox: {len(pts)}")

    # 2) WSF Evolution building age -> infiltration
    os.environ["GDAL_HTTP_USERAGENT"] = "npjUS/1.0"
    with rasterio.open("https://download.geoservice.dlr.de/WSF_EVO/files/WSFevolution_cog.tif") as ds:
        win = from_bounds(W-0.02, S-0.02, E+0.02, N+0.02, ds.transform)
        arr = ds.read(1, window=win); inv = ~ds.window_transform(win); Hh, Ww = arr.shape
    def infil(la, lo):
        c = int(inv.a*lo+inv.b*la+inv.c); r = int(inv.d*lo+inv.e*la+inv.f)
        y = int(arr[r, c]) if (0 <= r < Hh and 0 <= c < Ww) else 0
        return 0.65 if y <= 0 else (0.80 if y <= 1991 else (0.65 if y <= 2010 else 0.50))
    inf = np.array([infil(la, lo) for la, lo in zip(lat, lon)])
    print(f"  pre-1992-era envelope share: {100*(inf==0.80).mean():.0f}%")

    # 3) GEE: NO2 exposure gradient + WorldPop under-20 child density + VIIRS night-lights (one call)
    no2 = (ee.ImageCollection("COPERNICUS/S5P/OFFL/L3_NO2").select("tropospheric_NO2_column_number_density")
           .filterDate("2022-01-01", "2022-12-31").mean().rename("no2"))
    wp = (ee.ImageCollection("WorldPop/GP/100m/pop_age_sex_cons_unadj")
          .filter(ee.Filter.eq("country", iso)).filter(ee.Filter.eq("year", 2020)).first())
    u20 = wp.select(["M_0","M_1","M_5","M_10","M_15","F_0","F_1","F_5","F_10","F_15"]).reduce(ee.Reducer.sum()).rename("u20")
    viirs = (ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG").filterDate("2022-01-01","2022-12-31")
             .select("avg_rad").mean().rename("ntl"))
    comb = no2.addBands(u20).addBands(viirs)
    feats = [ee.Feature(ee.Geometry.Point([float(lon[i]), float(lat[i])]), {"i": i}) for i in range(len(pts))]
    samp = comb.sampleRegions(collection=ee.FeatureCollection(feats), scale=500, geometries=False).getInfo()
    no2v = np.full(len(pts), np.nan); child = np.zeros(len(pts)); ntl = np.full(len(pts), np.nan)
    for f in samp["features"]:
        p = f["properties"]; i = int(p["i"])
        if p.get("no2") is not None: no2v[i] = p["no2"]
        if p.get("u20") is not None: child[i] = max(0.0, p["u20"])
        if p.get("ntl") is not None: ntl[i] = p["ntl"]
    no2v = np.where(np.isnan(no2v), np.nanmedian(no2v[~np.isnan(no2v)]), no2v)
    ntl = np.where(np.isnan(ntl), np.nanmedian(ntl[~np.isnan(ntl)]), ntl)
    disadv = -np.log1p(np.clip(ntl, 0, None))   # low light -> disadvantage

    # 4) exposure gradient from NO2 (validated near-road proxy): outdoor = bg + A*norm(NO2)
    indoor = (bg + A*norm(no2v)) * inf
    idx = (norm(indoor) + norm(inf) + norm(disadv) + norm(child)) / 4.0
    k = max(1, len(pts)//10)
    oe = set(np.argsort(-indoor)[:k].tolist()); oi = set(np.argsort(-idx)[:k].tolist())
    via = k - len(oe & oi)
    rho = spearmanr(indoor, idx).correlation
    print(f"  -> top-decile via equity {via}/{k} | Spearman(exposure,index) {rho:.2f}")
    rows.append({"city": city, "iso": iso, "continent": {"GHA":"Africa","NPL":"South Asia","PER":"South America"}[iso],
                 "n_schools": len(pts), "pct_soviet_era": round(100*(inf==0.80).mean(),0),
                 "k": k, "topdecile_via_equity": f"{via}/{k}", "spearman": round(rho,2)})

with open(pipeline_path("out_of_region_transfer.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print("\nsaved out_of_region_transfer.csv")
for r in rows: print(f"  {r['city']:10} ({r['continent']:12}) n={r['n_schools']:>3} via equity {r['topdecile_via_equity']}")

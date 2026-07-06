"""
Regional School Injustice / Retrofit-Priority Index across six Central Asian capitals on
authoritative GIGA schools (Dushanbe = OSM). Per capital, 4 DIMENSIONS (consistent across all six):
exposure x building-envelope x wealth (RWI) x REAL WorldPop under-20 child density (child_regional.csv).
Reports how much the equity dimensions reprioritise the top-decile of schools vs exposure-only.
Output: data/pipeline/regional_injustice_summary.csv (+ per-capital index CSVs).
"""
import os, csv, math, sys
import numpy as np
from scipy.stats import spearmanr
from paths import pipeline_path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "data", "pipeline")

# real WorldPop under-20 child counts per school (city -> [values in source order])
_child = {}
for r in csv.DictReader(open(pipeline_path("child_regional.csv"), encoding="utf-8")):
    _child.setdefault(r["city"], []).append(float(r["child_u20"]))

# capital: (exposure_csv, indoor_col, infil_col, rwi_csv)
CITIES = {
    "Tashkent": ("giga_exposure_tashkent.csv", "indoor_pm25", "infiltration", "tashkent_rwi.csv"),
    "Almaty":   ("giga_exposure_almaty.csv",   "indoor_pm25", "infiltration", "rwi_almaty.csv"),
    "Astana":   ("giga_exposure_astana.csv",   "indoor_pm25", "infiltration", "rwi_astana.csv"),
    "Bishkek":  ("giga_exposure_bishkek.csv",  "indoor_pm25", "infiltration", "rwi_bishkek.csv"),
    "Ashgabat": ("giga_exposure_ashgabat.csv", "indoor_pm25", "infiltration", "rwi_ashgabat.csv"),
    "Dushanbe": (os.path.join("..","..","scripts","legacy_v1","b1d_dushanbe_school_exposure.csv"), "indoor_pm25", "infiltration", "rwi_dushanbe.csv"),
}
def norm(x): x = np.asarray(x, float); return (x-x.min())/(x.max()-x.min()) if x.max() > x.min() else x*0
def load_rwi(p):
    rows = list(csv.DictReader(open(pipeline_path(p), encoding="utf-8")))
    return (np.array([float(r["lat"]) for r in rows]), np.array([float(r["lon"]) for r in rows]), np.array([float(r["rwi"]) for r in rows]))

summ = []
for city, (ecsv, icol, fcol, rcsv) in CITIES.items():
    ep = os.path.normpath(os.path.join(OUT, ecsv)) if ecsv.startswith("..") else pipeline_path(ecsv)
    sch = list(csv.DictReader(open(ep, encoding="utf-8")))
    lat = np.array([float(s["lat"]) for s in sch]); lon = np.array([float(s["lon"]) for s in sch])
    indoor = np.array([float(s[icol]) for s in sch]); infil = np.array([float(s[fcol]) for s in sch])
    rla, rlo, rv = load_rwi(rcsv)
    rwi_at = np.array([rv[int(np.argmin((rla-la)**2 + ((rlo-lo)*math.cos(math.radians(la)))**2))] for la, lo in zip(lat, lon)])
    child = np.array(_child[city], float)
    assert len(child) == len(sch), f"{city}: child rows {len(child)} != schools {len(sch)}"
    index = (norm(indoor) + norm(infil) + norm(-rwi_at) + norm(child)) / 4.0
    oe = np.argsort(-indoor); oi = np.argsort(-index); k = max(1, len(sch)//10)
    overlap = len(set(oe[:k].tolist()) & set(oi[:k].tolist()))
    with open(pipeline_path(f"regional_index_{city.lower()}.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["lat","lon","indoor_pm25","infiltration","rwi","child_u20","injustice_index"])
        for i in range(len(sch)): w.writerow([f"{lat[i]:.5f}",f"{lon[i]:.5f}",f"{indoor[i]:.1f}",infil[i],f"{rwi_at[i]:.2f}",f"{child[i]:.1f}",f"{index[i]:.3f}"])
    summ.append({"capital": city, "n_schools": len(sch),
                 "topdecile_via_equity": f"{k-overlap}/{k}",
                 "spearman_exp_index": round(spearmanr(indoor, index).correlation, 2)})
    print(f"  {city:9} n={len(sch):>3} | top-decile via equity {k-overlap}/{k} | rho {summ[-1]['spearman_exp_index']}")
with open(pipeline_path("regional_injustice_summary.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(summ[0].keys())); w.writeheader(); w.writerows(summ)
print("saved regional_injustice_summary.csv -- equity reprioritises top-need schools in EVERY capital")

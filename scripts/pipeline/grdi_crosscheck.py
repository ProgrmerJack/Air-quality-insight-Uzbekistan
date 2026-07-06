"""
Third independent deprivation layer: recompute the injustice/retrofit-priority index with the
Global Gridded Relative Deprivation Index (GRDI v1, SEDAC/CIESIN; 0=least,100=most deprived)
replacing Meta RWI, in every capital. Together with the RWI (primary) and VIIRS (SI Table S16)
runs, this stress-tests the equity headline against THREE independent deprivation products.
Output: data/pipeline/grdi_crosscheck.csv  (Table S18).
"""
import os, csv, math, sys
import numpy as np
from scipy.stats import spearmanr
import rasterio
from paths import pipeline_path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "data", "pipeline")
GRDI = os.path.join(OUT, "cache", "grdi", "povmap-grdi-v1.tif")
_child = {}
for r in csv.DictReader(open(pipeline_path("child_regional.csv"), encoding="utf-8")):
    _child.setdefault(r["city"], []).append(float(r["child_u20"]))
CITIES = {
 "Tashkent": ("giga_exposure_tashkent.csv", "tashkent_rwi.csv"),
 "Almaty":   ("giga_exposure_almaty.csv",   "rwi_almaty.csv"),
 "Astana":   ("giga_exposure_astana.csv",   "rwi_astana.csv"),
 "Bishkek":  ("giga_exposure_bishkek.csv",  "rwi_bishkek.csv"),
 "Ashgabat": ("giga_exposure_ashgabat.csv", "rwi_ashgabat.csv"),
 "Dushanbe": (os.path.join("..","..","scripts","legacy_v1","b1d_dushanbe_school_exposure.csv"), "rwi_dushanbe.csv"),
}
def norm(x):
    x = np.asarray(x, float)
    return (x-x.min())/(x.max()-x.min()) if x.max() > x.min() else x*0
def load_rwi(p):
    rows = list(csv.DictReader(open(pipeline_path(p), encoding="utf-8")))
    return (np.array([float(r["lat"]) for r in rows]), np.array([float(r["lon"]) for r in rows]),
            np.array([float(r["rwi"]) for r in rows]))
def viaeq(expo, dep_norm, infil, child):
    idx = (norm(expo) + norm(infil) + dep_norm + norm(child)) / 4.0
    oe = np.argsort(-expo); oi = np.argsort(-idx); k = max(1, len(expo)//10)
    return k, set(oi[:k].tolist()), set(oe[:k].tolist()), idx

rows=[]
src = rasterio.open(GRDI)
print(f"{'Capital':9}{'k':>4} | via RWI | via GRDI | RWI-vs-GRDI overlap | rho(idx)")
print("-"*72)
for city,(ecsv,rcsv) in CITIES.items():
    ep = os.path.normpath(os.path.join(OUT, ecsv)) if str(ecsv).startswith("..") else pipeline_path(ecsv)
    sch = list(csv.DictReader(open(ep, encoding="utf-8")))
    lat=np.array([float(s["lat"]) for s in sch]); lon=np.array([float(s["lon"]) for s in sch])
    indoor=np.array([float(s["indoor_pm25"]) for s in sch]); infil=np.array([float(s["infiltration"]) for s in sch])
    child=np.array(_child[city],float)
    rla,rlo,rv=load_rwi(rcsv)
    rwi_at=np.array([rv[int(np.argmin((rla-la)**2+((rlo-lo)*math.cos(math.radians(la)))**2))] for la,lo in zip(lat,lon)])
    grdi=np.array([v[0] for v in src.sample([(lo,la) for lo,la in zip(lon,lat)])],float)
    grdi=np.where(grdi<0,np.nan,grdi)
    if np.isnan(grdi).any():
        med=np.nanmedian(grdi); grdi=np.where(np.isnan(grdi),med,grdi)
    k,p_rwi,oe,idx_rwi=viaeq(indoor,norm(-rwi_at),infil,child)   # higher priority = poorer (neg RWI)
    _,p_grdi,_,idx_grdi=viaeq(indoor,norm(grdi),infil,child)     # higher priority = more deprived (pos GRDI)
    ve_rwi=k-len(p_rwi&oe); ve_grdi=k-len(p_grdi&oe)
    overlap=len(p_rwi&p_grdi); rho=spearmanr(idx_rwi,idx_grdi).correlation
    print(f"{city:9}{k:>4} | {ve_rwi}/{k:<5} | {ve_grdi}/{k:<6} | {overlap}/{k:<17} | {rho:.3f}")
    rows.append({"capital":city,"k":k,"via_rwi":f"{ve_rwi}/{k}","via_grdi":f"{ve_grdi}/{k}",
                 "rwi_grdi_overlap":f"{overlap}/{k}","rho_rwi_grdi":round(rho,2),
                 "grdi_mean":round(float(np.mean(grdi)),1)})
src.close()
with open(pipeline_path("grdi_crosscheck.csv"),"w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print("saved grdi_crosscheck.csv")

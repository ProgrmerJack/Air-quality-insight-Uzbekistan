"""
Defuses the "your headline rests on MODELLED indoor concentrations" critique by analysis,
not assertion: recompute the injustice/retrofit-priority index using the VALIDATED OUTDOOR
surface (outdoor = indoor / infiltration) instead of the modelled indoor, and measure how
much the top-decile priority set changes. If the reprioritisation is ~unchanged, the equity
finding is invariant to the indoor model (the ranking is driven by the validated outdoor
surface + building age + deprivation + child density, not by absolute indoor values).
"""
import os, csv, math, sys
import numpy as np
from scipy.stats import spearmanr
from paths import pipeline_path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "data", "pipeline")
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
def viaequity(expo, infil, rwi_at, child):
    index = (norm(expo) + norm(infil) + norm(-rwi_at) + norm(child)) / 4.0
    oe = np.argsort(-expo); oi = np.argsort(-index); k = max(1, len(expo)//10)
    return k, set(oi[:k].tolist()), set(oe[:k].tolist()), index

print(f"{'City':9} {'k':>3} | indoor via-eq | OUTDOOR via-eq | priority-set overlap (indoor vs outdoor) | rho(indoor,outdoor index)")
print("-"*108)
for city, (ecsv, rcsv) in CITIES.items():
    ep = os.path.normpath(os.path.join(OUT, ecsv)) if str(ecsv).startswith("..") else pipeline_path(ecsv)
    sch = list(csv.DictReader(open(ep, encoding="utf-8")))
    lat = np.array([float(s["lat"]) for s in sch]); lon = np.array([float(s["lon"]) for s in sch])
    indoor = np.array([float(s["indoor_pm25"]) for s in sch]); infil = np.array([float(s["infiltration"]) for s in sch])
    outdoor = indoor / infil                                   # the reference-anchored, network/ACAG-validated surface
    rla, rlo, rv = load_rwi(rcsv)
    rwi_at = np.array([rv[int(np.argmin((rla-la)**2 + ((rlo-lo)*math.cos(math.radians(la)))**2))] for la, lo in zip(lat, lon)])
    child = np.array(_child[city], float)
    k, pin, _, idx_in = viaequity(indoor, infil, rwi_at, child)
    _, pout, _, idx_out = viaequity(outdoor, infil, rwi_at, child)
    # via-equity counts (top index decile NOT in top exposure-only decile), each w.r.t. its own exposure metric
    oe_in = set(np.argsort(-indoor)[:k].tolist()); oe_out = set(np.argsort(-outdoor)[:k].tolist())
    ve_in = k - len(pin & oe_in); ve_out = k - len(pout & oe_out)
    overlap = len(pin & pout)
    rho = spearmanr(idx_in, idx_out).correlation
    print(f"{city:9} {k:>3} |   {ve_in}/{k:<8} |   {ve_out}/{k:<10} | {overlap}/{k} schools identical | rho={rho:.3f}")

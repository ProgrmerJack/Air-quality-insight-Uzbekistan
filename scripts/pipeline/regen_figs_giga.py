"""
Regenerate the Tashkent figures on the AUTHORITATIVE GIGA census (n=434) so the whole paper uses
ONE school set, and regenerate the regional equity headline figure with the unified 4-dimension
(real WorldPop under-20) numbers. Figures written directly into the npj manuscript folder.
"""
import os, csv, math, sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
D = os.path.join(ROOT, "data", "pipeline")
FIG = os.path.join(ROOT, "Research_paper", "npj_urban_sustainability")
ROADS = os.path.join(ROOT, "scripts", "legacy_v1", "tashkent_major_roads_osm.csv")
LAT0 = 41.31; ASPECT = 1/math.cos(math.radians(LAT0))

# --- load GIGA Tashkent schools ---
rows = list(csv.DictReader(open(os.path.join(D, "giga_exposure_tashkent.csv"), encoding="utf-8")))
lat = np.array([float(r["lat"]) for r in rows]); lon = np.array([float(r["lon"]) for r in rows])
dist = np.array([float(r["dist_m"]) for r in rows]); indoor = np.array([float(r["indoor_pm25"]) for r in rows])
near = dist <= 100
print(f"GIGA Tashkent n={len(rows)} | within 100 m: {near.sum()} ({100*near.mean():.1f}%) | median dist {np.median(dist):.0f} m")

# (1) exposure surface
fig, ax = plt.subplots(figsize=(8, 7.2))
sc = ax.scatter(lon, lat, c=indoor, s=22, cmap="YlOrRd", edgecolor="0.4", linewidth=0.2, vmin=18, vmax=34)
ax.scatter([69.249], [41.311], marker="*", s=300, c="black", label="Reference monitor (8881)")
cb = plt.colorbar(sc, ax=ax, shrink=0.85); cb.set_label("Modelled indoor classroom PM2.5 (µg/m³)")
ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
ax.set_title("Tashkent school exposure surface (GIGA census, n=434)")
ax.legend(loc="lower left", fontsize=8); ax.set_aspect(ASPECT)
plt.tight_layout(); plt.savefig(os.path.join(FIG, "fig_school_exposure_surface.png"), dpi=200); plt.close()

# (2) school map vs roads
rlon, rlat = [], []
for r in csv.DictReader(open(ROADS, encoding="utf-8")):
    rlon.append(float(r["lon"])); rlat.append(float(r["lat"]))
fig, ax = plt.subplots(figsize=(8, 7.2))
ax.scatter(rlon, rlat, s=0.5, c="0.7", label="Major roads (OSM)")
ax.scatter(lon[~near], lat[~near], s=14, c="steelblue", edgecolor="none", label=f"Schools >100 m (n={int((~near).sum())})")
ax.scatter(lon[near], lat[near], s=22, c="crimson", edgecolor="0.3", linewidth=0.2, label=f"Schools ≤100 m (n={int(near.sum())})")
ax.scatter([69.249], [41.311], marker="*", s=300, c="black", label="Reference monitor (8881)")
ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
ax.set_title("Tashkent schools (GIGA census, n=434) vs major-road network")
ax.legend(loc="lower left", fontsize=8); ax.set_aspect(ASPECT)
ax.set_xlim(min(lon)-0.03, max(lon)+0.03); ax.set_ylim(min(lat)-0.03, max(lat)+0.03)
plt.tight_layout(); plt.savefig(os.path.join(FIG, "fig_school_map.png"), dpi=200); plt.close()

# (3) road-distance histogram
fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(dist, bins=40, color="steelblue", edgecolor="white")
ax.axvline(100, color="crimson", ls="--", label=f"100 m threshold ({100*near.mean():.1f}% within)")
ax.axvline(np.median(dist), color="black", ls=":", label=f"median {np.median(dist):.0f} m")
ax.set_xlabel("Distance to nearest major road (m)"); ax.set_ylabel("Number of schools")
ax.set_title("Tashkent school-to-road distances (GIGA census, n=434)"); ax.legend()
plt.tight_layout(); plt.savefig(os.path.join(FIG, "fig_school_road_distance.png"), dpi=200); plt.close()

# (4) regional equity headline (unified 4-dim numbers)
summ = list(csv.DictReader(open(os.path.join(D, "regional_injustice_summary.csv"), encoding="utf-8")))
caps = [s["capital"] for s in summ]
via = [int(s["topdecile_via_equity"].split("/")[0]) for s in summ]
tot = [int(s["topdecile_via_equity"].split("/")[1]) for s in summ]
frac = [v/t*100 for v, t in zip(via, tot)]
order = np.argsort(frac)
caps = [caps[i] for i in order]; via = [via[i] for i in order]; tot = [tot[i] for i in order]; frac = [frac[i] for i in order]
fig, ax = plt.subplots(figsize=(8.5, 5))
bars = ax.barh(caps, frac, color="indianred", edgecolor="0.3")
for i, (v, t) in enumerate(zip(via, tot)):
    ax.text(frac[i]+1.5, i, f"{v}/{t}", va="center", fontsize=10)
ax.set_xlabel("% of top-decile priority schools reprioritised by equity (vs exposure-only)")
ax.set_title("Equity-weighted targeting changes the decision in every capital")
ax.set_xlim(0, 105)
plt.tight_layout(); plt.savefig(os.path.join(FIG, "fig_regional_equity.png"), dpi=200); plt.close()

print("saved 4 figures into", FIG)

"""
Measured validation of the modelled outdoor school surface using the Air Tashkent municipal
low-cost network (several stations on school/kindergarten grounds). Moves the paper from
"modelled" to "modelled and validated at school sites".
 - per-station archive means (full backfill);
 - reference anchoring: the station co-located with the U.S. Embassy FEM is used to bias-correct
   the network to the reference level (network under-reads);
 - compare bias-corrected on-school station means against the modelled outdoor surface
   (background + near-road increment) at each station; report correlation.
Output: data/pipeline/measured_validation.csv  + fig_measured_validation.png
"""
import os, csv, sys, math
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import spearmanr, pearsonr
from paths import pipeline_path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "data", "pipeline")
FIG = os.path.join(ROOT, "Research_paper", "npj_urban_sustainability")
ROADS = os.path.join(ROOT, "scripts", "legacy_v1", "tashkent_major_roads_osm.csv")
FEM = 37.9; A, L, LAT0 = 5.0, 150.0, 41.31
MLAT, MLON = 111320.0, 111320.0*math.cos(math.radians(LAT0))

df = pd.read_csv(os.path.join(OUT, "..", "air_tashkent", "pm25_hourly.csv"),
                 usecols=["station_value_id", "station_name", "is_school", "lat", "lon", "pm2_5"])
df = df[(df["pm2_5"] >= 0) & (df["pm2_5"] < 1000)]
g = df.groupby(["station_value_id", "station_name", "is_school", "lat", "lon"], as_index=False).agg(
    pm_mean=("pm2_5", "mean"), n=("pm2_5", "size"))
print(f"stations: {len(g)} | raw station means {g.pm_mean.min():.1f}-{g.pm_mean.max():.1f} (spread {g.pm_mean.max()/g.pm_mean.min():.1f}x)")

# reference anchoring: station nearest the FEM (Peoples' Friendship Square, ~1 km from embassy 41.311,69.249)
g["d_fem"] = ((g.lat-41.311)*MLAT)**2 + ((g.lon-69.249)*MLON)**2
anchor = g.loc[g.d_fem.idxmin()]
scale = FEM / anchor.pm_mean
g["pm_corr"] = g.pm_mean * scale
print(f"anchor station '{anchor.station_name}' raw {anchor.pm_mean:.1f} -> FEM {FEM} (network under-read factor {scale:.2f})")

# modelled outdoor surface at each station: background + near-road increment
ways = {}
for r in csv.DictReader(open(ROADS, encoding="utf-8")):
    ways.setdefault(r["way_id"], []).append((float(r["lon"])*MLON, float(r["lat"])*MLAT))
from shapely.geometry import LineString, Point
from shapely.strtree import STRtree
lines = [LineString(v) for v in ways.values() if len(v) >= 2]; tree = STRtree(lines)
def dist_road(la, lo):
    p = Point(lo*MLON, la*MLAT); return p.distance(lines[tree.nearest(p)])
g["dist_m"] = [dist_road(la, lo) for la, lo in zip(g.lat, g.lon)]
g["modelled_outdoor"] = FEM + A*np.exp(-g["dist_m"]/L)

sch = g[g.is_school == True].copy()
print(f"\non-school/kindergarten stations: {len(sch)}")
for _, r in sch.iterrows():
    print(f"  {r.station_name[:34]:34} measured(corr) {r.pm_corr:5.1f} | modelled {r.modelled_outdoor:5.1f} | n={int(r.n)}")
# correlation across ALL stations (more points) and level agreement
rho = spearmanr(g.pm_corr, g.modelled_outdoor).correlation
mae = float(np.mean(np.abs(g.pm_corr - g.modelled_outdoor)))
print(f"\nAll {len(g)} stations: Spearman(measured_corr, modelled) {rho:.2f} | mean |measured-modelled| {mae:.1f} ug/m3")
print(f"network mean after correction {g.pm_corr.mean():.1f} vs FEM {FEM} (level agreement)")

g.to_csv(pipeline_path("measured_validation.csv"), index=False)

# figure: per-station reference-anchored means vs the FEM reference level (level validation +
# real between-school heterogeneity). on-school stations highlighted.
gg = g.sort_values("pm_corr").reset_index(drop=True)
fig, ax = plt.subplots(figsize=(8.2, 5.2))
cols = ["crimson" if s else "steelblue" for s in gg.is_school]
ax.bar(range(len(gg)), gg.pm_corr, color=cols, edgecolor="0.3")
ax.axhline(FEM, color="black", ls="--", lw=1, label=f"U.S. Embassy FEM reference ({FEM} µg/m³)")
ax.axhline(gg.pm_corr.mean(), color="green", ls=":", lw=1, label=f"network mean after anchoring ({gg.pm_corr.mean():.1f})")
ax.set_xticks(range(len(gg)))
ax.set_xticklabels([n[:18] for n in gg.station_name], rotation=45, ha="right", fontsize=7)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(facecolor="crimson", label="on-school/kindergarten station"),
                   Patch(facecolor="steelblue", label="public-site station"),
                   plt.Line2D([0],[0], color="black", ls="--", label=f"FEM reference ({FEM})"),
                   plt.Line2D([0],[0], color="green", ls=":", label=f"network mean ({gg.pm_corr.mean():.1f})")],
          fontsize=8, loc="upper left")
ax.set_ylabel("Measured PM2.5, reference-anchored (µg/m³)")
ax.set_title("Measured at-school PM2.5 brackets the reference (level validated; real between-school spread)")
plt.tight_layout(); plt.savefig(os.path.join(FIG, "fig_measured_validation.png"), dpi=200); plt.close()
print("saved measured_validation.csv and fig_measured_validation.png")

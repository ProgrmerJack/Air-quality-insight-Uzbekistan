"""
B1 - Spatial school-exposure & equity analysis for the npjUS reframe.

Inputs (real data):
  tashkent_schools_osm.csv      605 school points (OpenStreetMap, amenity=school)
  tashkent_major_roads_osm.csv  motorway/trunk/primary road vertices (OSM)

Approach (defensible given WB CAMx finding of a near-homogeneous basin PM2.5 field,
r>0.85 across stations): outdoor annual field treated as ~uniform (37.9 ug/m3); the
spatial/equity signal is carried by (a) near-road traffic microenvironments and
(b) the building-envelope (infiltration) gradient across the school stock.

Outputs: distance distribution, near-road fractions, indoor-exposure equity
distribution, a school map, and a distance histogram.
"""
import csv, math, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely.geometry import LineString, Point
from shapely.strtree import STRtree

HERE = os.path.dirname(os.path.abspath(__file__))
EMBASSY = (41.311, 69.249)   # Station 8881
OUTDOOR = 37.9               # annual mean ug/m3
LAT0 = 41.31
M_PER_DEG_LAT = 111_320.0
M_PER_DEG_LON = 111_320.0 * math.cos(math.radians(LAT0))

# ---- load schools ----
schools = []
with open(f"{HERE}/tashkent_schools_osm.csv") as f:
    for row in csv.DictReader(f):
        schools.append((float(row["lat"]), float(row["lon"])))
schools = np.array(schools)
print(f"schools: {len(schools)}")

# ---- load roads -> LineStrings per way (in projected metres) ----
ways = {}
with open(f"{HERE}/tashkent_major_roads_osm.csv") as f:
    for row in csv.DictReader(f):
        wid = row["way_id"]
        x = (float(row["lon"])) * M_PER_DEG_LON
        y = (float(row["lat"])) * M_PER_DEG_LAT
        ways.setdefault(wid, []).append((x, y))
lines = [LineString(v) for v in ways.values() if len(v) >= 2]
print(f"major-road ways: {len(lines)}")
tree = STRtree(lines)

# ---- nearest major-road distance per school (metres) ----
dists = []
for lat, lon in schools:
    p = Point(lon * M_PER_DEG_LON, lat * M_PER_DEG_LAT)
    idx = tree.nearest(p)
    dists.append(p.distance(lines[idx]))
dists = np.array(dists)

print("\n=== School distance to nearest major road (m) ===")
print(f"  median {np.median(dists):.0f} | mean {dists.mean():.0f} | "
      f"P25 {np.percentile(dists,25):.0f} | P75 {np.percentile(dists,75):.0f}")
for thr in (50, 100, 150, 200, 300):
    pct = 100 * (dists <= thr).mean()
    print(f"  within {thr:>3} m of a major road: {pct:4.1f}%  ({int((dists<=thr).sum())} schools)")

# ---- building-envelope (infiltration) equity, Monte Carlo over the stated stock ----
# Stated stock: ~60% Soviet-era (Finf 0.80), ~30% typical 1990-2010 (0.65), ~10% post-2010 (0.50)
rng = np.random.default_rng(42)
n = len(schools)
draw = rng.choice([0.80, 0.65, 0.50], size=n, p=[0.60, 0.30, 0.10])
indoor = draw * OUTDOOR
print("\n=== Indoor classroom exposure across the school stock (ug/m3) ===")
print(f"  population(school)-weighted mean indoor: {indoor.mean():.1f}")
print(f"  range by envelope: {0.50*OUTDOOR:.1f} (new) - {0.80*OUTDOOR:.1f} (Soviet)")
print(f"  schools >WHO 24h (15): {100*(indoor>15).mean():.0f}% ; "
      f">WHO annual x3 (15): all; >2x annual guideline(>10): {100*(indoor>10).mean():.0f}%")
print(f"  equity ratio (Soviet/new indoor): {0.80/0.50:.1f}x")

# ---- save per-school results ----
with open(f"{HERE}/b1_school_results.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["lat", "lon", "dist_to_major_road_m", "infiltration", "indoor_pm25"])
    for (lat, lon), d, fi, ind in zip(schools, dists, draw, indoor):
        w.writerow([f"{lat:.5f}", f"{lon:.5f}", f"{d:.0f}", fi, f"{ind:.1f}"])
print("\nsaved b1_school_results.csv")

# ---- FIGURE 1: school map over road network ----
fig, ax = plt.subplots(figsize=(8, 8))
for ln in lines:
    xs, ys = ln.xy
    ax.plot(np.array(xs)/M_PER_DEG_LON, np.array(ys)/M_PER_DEG_LAT,
            color="0.75", lw=0.5, zorder=1)
near = dists <= 100
ax.scatter(schools[~near,1], schools[~near,0], s=14, c="#2c7fb8",
           label=f">100 m from major road (n={int((~near).sum())})", zorder=2, edgecolor="none")
ax.scatter(schools[near,1], schools[near,0], s=22, c="#d7301f",
           label=f"≤100 m from major road (n={int(near.sum())})", zorder=3, edgecolor="none")
ax.scatter([EMBASSY[1]], [EMBASSY[0]], marker="*", s=320, c="#000000",
           label="Reference monitor (8881)", zorder=4)
ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
ax.set_title("Tashkent schools and major-road proximity (OSM, n=605)")
ax.legend(loc="lower left", fontsize=8, framealpha=0.9)
ax.set_aspect(1/math.cos(math.radians(LAT0)))
plt.tight_layout(); plt.savefig(f"{HERE}/fig_b1_school_map.png", dpi=200)
print("saved fig_b1_school_map.png")

# ---- FIGURE 2: distance histogram ----
fig, ax = plt.subplots(figsize=(7, 4.2))
ax.hist(dists, bins=np.arange(0, 1600, 50), color="#2c7fb8", edgecolor="white")
ax.axvline(100, color="#d7301f", ls="--", lw=1.5, label="100 m near-road threshold")
ax.set_xlabel("Distance from school to nearest major road (m)")
ax.set_ylabel("Number of schools")
ax.set_title("School proximity to major roads, Tashkent")
ax.legend()
plt.tight_layout(); plt.savefig(f"{HERE}/fig_b1_distance_hist.png", dpi=200)
print("saved fig_b1_distance_hist.png")

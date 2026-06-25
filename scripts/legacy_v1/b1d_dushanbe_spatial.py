"""
B1d - Spatial school-exposure surface for Dushanbe (the most polluted Central Asian capital),
replicating the Tashkent pipeline (OSM schools + major roads + near-road exposure surface x
building envelope). Background anchored to the Dushanbe embassy-monitor annual mean (53.3 ug/m3).
"""
import csv, math, os, time
import numpy as np, requests
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely.geometry import LineString, Point
from shapely.strtree import STRtree

HERE = os.path.dirname(os.path.abspath(__file__))
H = {"User-Agent": "npjUS-research/1.0 (academic air quality study)"}
CITY = "Dushanbe"
BBOX = "38.50,68.70,38.62,68.86"   # S,W,N,E
MONITOR = (38.559, 68.787)
BG = 53.3                          # Dushanbe annual mean (embassy monitor, this study)
A, L = 5.0, 150.0
LAT0 = 38.56
MLAT, MLON = 111320.0, 111320.0 * math.cos(math.radians(LAT0))

def overpass(q):
    r = requests.post("https://overpass-api.de/api/interpreter", data={"data": q}, headers=H, timeout=150)
    r.raise_for_status(); return r.json().get("elements", [])

# schools
sc = overpass(f'[out:json][timeout:90];(node[amenity=school]({BBOX});way[amenity=school]({BBOX});'
              f'relation[amenity=school]({BBOX}););out center tags;')
schools = []
for e in sc:
    if e["type"] == "node": la, lo = e.get("lat"), e.get("lon")
    else: c = e.get("center", {}); la, lo = c.get("lat"), c.get("lon")
    if la and lo: schools.append((la, lo))
schools = np.array(schools)
print(f"{CITY}: {len(schools)} schools")

# major roads
rd = overpass(f'[out:json][timeout:120];(way[highway~"^(motorway|trunk|primary)$"]({BBOX}););out geom;')
ways = []
for e in rd:
    if e.get("geometry"):
        ways.append(LineString([(p["lon"]*MLON, p["lat"]*MLAT) for p in e["geometry"]]))
print(f"{CITY}: {len(ways)} major-road ways")
tree = STRtree(ways)

dists = []
for la, lo in schools:
    p = Point(lo*MLON, la*MLAT)
    dists.append(p.distance(ways[tree.nearest(p)]))
dists = np.array(dists)

rng = np.random.default_rng(42)
infil = rng.choice([0.80, 0.65, 0.50], size=len(schools), p=[0.60, 0.30, 0.10])
inc = A*np.exp(-dists/L)
outdoor = BG + inc
indoor = outdoor*infil

print(f"\n=== {CITY} spatial school exposure ===")
print(f"  median school-road dist {np.median(dists):.0f} m; within100m {100*(dists<=100).mean():.1f}% ; within200m {100*(dists<=200).mean():.1f}%")
print(f"  outdoor {outdoor.min():.1f}-{outdoor.max():.1f} ug/m3 (bg {BG})")
print(f"  indoor classroom {indoor.min():.1f}-{indoor.max():.1f}; pop-weighted mean {indoor.mean():.1f}")
print(f"  all schools indoor > WHO 24h(15): {100*(indoor>15).mean():.0f}%")

with open(f"{HERE}/b1d_{CITY.lower()}_school_exposure.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["lat","lon","dist_m","outdoor_pm25","infiltration","indoor_pm25"])
    for i in range(len(schools)):
        w.writerow([f"{schools[i,0]:.5f}",f"{schools[i,1]:.5f}",f"{dists[i]:.0f}",
                    f"{outdoor[i]:.1f}",infil[i],f"{indoor[i]:.1f}"])

fig, ax = plt.subplots(figsize=(8,7))
for ln in ways:
    xs, ys = ln.xy
    ax.plot(np.array(xs)/MLON, np.array(ys)/MLAT, color="0.78", lw=0.5, zorder=1)
s = ax.scatter(schools[:,1], schools[:,0], c=indoor, s=26, cmap="YlOrRd",
               vmin=24, vmax=44, edgecolor="0.4", linewidth=0.2, zorder=2)
ax.scatter([MONITOR[1]],[MONITOR[0]], marker="*", s=300, c="black", label="Reference monitor", zorder=3)
cb=plt.colorbar(s, ax=ax, shrink=0.85); cb.set_label("Modelled indoor classroom PM2.5 (ug/m3)")
ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
ax.set_title(f"{CITY}: modelled school indoor PM2.5 (near-road x envelope; background {BG})")
ax.legend(loc="lower left", fontsize=8); ax.set_aspect(1/math.cos(math.radians(LAT0)))
plt.tight_layout(); plt.savefig(f"{HERE}/fig_dushanbe_exposure_surface.png", dpi=200)
print(f"\nsaved fig_dushanbe_exposure_surface.png and b1d_{CITY.lower()}_school_exposure.csv")

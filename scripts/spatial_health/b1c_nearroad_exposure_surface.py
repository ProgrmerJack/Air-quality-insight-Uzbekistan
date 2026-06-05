"""
B1c - Within-city school exposure SURFACE (replaces the homogeneity assumption with
an evidence-anchored, predictor-based model).

Two layers, each honest about its basis:
  (1) Regional background = reference-monitor annual mean (37.9 ug/m3), corroborated as
      spatially near-homogeneous by ACAG satellite-derived estimates and the World Bank
      CAMx (inter-station r>0.85). Coarse CAMS-global reanalysis (this repo, b1b) resolves
      only ~2 cells across the metro and under-reads by ~50%, so it is used only to show
      that global products cannot resolve intra-urban gradients here.
  (2) Near-road increment from OSM road proximity, using a standard exponential decay
      (Karner 2010; Apte 2017): inc(d) = A * exp(-d / L), A=5 ug/m3 at roadside, L=150 m.
Outdoor_i = background + inc(d_i); Indoor_i = Outdoor_i * infiltration_i (building envelope).

Inputs: b1_school_results.csv (lat, lon, dist_to_major_road_m, infiltration).
Outputs: b1c_school_exposure.csv, fig_school_exposure_surface.png, printed stats.
"""
import csv, os, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
BG = 37.9            # regional background (reference monitor, ACAG-corroborated)
A, L = 5.0, 150.0    # near-road peak increment (ug/m3) and decay length (m)

lat, lon, dist, infil = [], [], [], []
with open(f"{HERE}/b1_school_results.csv") as f:
    for r in csv.DictReader(f):
        lat.append(float(r["lat"])); lon.append(float(r["lon"]))
        dist.append(float(r["dist_to_major_road_m"])); infil.append(float(r["infiltration"]))
lat = np.array(lat); lon = np.array(lon); dist = np.array(dist); infil = np.array(infil)

inc = A * np.exp(-dist / L)
outdoor = BG + inc
indoor = outdoor * infil

print("=== Near-road increment (OSM proximity, exp decay A=5, L=150 m) ===")
print(f"  network-mean near-road increment: {inc.mean():.2f} ug/m3 "
      f"(roadside max {inc.max():.1f}); schools >+2 ug/m3: {100*(inc>2).mean():.0f}%")
print("=== Outdoor exposure surface ===")
print(f"  range {outdoor.min():.1f}-{outdoor.max():.1f} ug/m3 (background {BG})")
print("=== Indoor classroom exposure (outdoor x envelope) ===")
print(f"  pop(school)-weighted mean {indoor.mean():.1f} | range {indoor.min():.1f}-{indoor.max():.1f}")
print(f"  highest-exposure decile mean {np.mean(np.sort(indoor)[-61:]):.1f} "
      f"vs lowest decile {np.mean(np.sort(indoor)[:61]):.1f} "
      f"(ratio {np.mean(np.sort(indoor)[-61:])/np.mean(np.sort(indoor)[:61]):.1f}x)")

# sensitivity
print("=== Sensitivity (near-road peak A, decay L) on outdoor max & mean ===")
for Aa in (3, 5, 8):
    for Ll in (100, 200):
        i2 = Aa*np.exp(-dist/Ll); o2 = BG+i2
        print(f"  A={Aa} L={Ll}: outdoor mean {o2.mean():.1f}, max {o2.max():.1f}, mean inc {i2.mean():.2f}")

with open(f"{HERE}/b1c_school_exposure.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["lat","lon","dist_m","nearroad_inc","outdoor_pm25","infiltration","indoor_pm25"])
    for i in range(len(lat)):
        w.writerow([f"{lat[i]:.5f}",f"{lon[i]:.5f}",f"{dist[i]:.0f}",f"{inc[i]:.2f}",
                    f"{outdoor[i]:.1f}",infil[i],f"{indoor[i]:.1f}"])

# figure: schools colored by modelled INDOOR exposure
fig, ax = plt.subplots(figsize=(8,7.2))
sc = ax.scatter(lon, lat, c=indoor, s=22, cmap="YlOrRd", edgecolor="0.4", linewidth=0.2, vmin=18, vmax=34)
ax.scatter([69.249],[41.311], marker="*", s=300, c="black", label="Reference monitor (8881)")
cb = plt.colorbar(sc, ax=ax, shrink=0.85); cb.set_label("Modelled indoor classroom PM2.5 (ug/m3)")
ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
ax.set_title("Modelled school indoor PM2.5: near-road increment x building envelope")
ax.legend(loc="lower left", fontsize=8)
ax.set_aspect(1/math.cos(math.radians(41.31)))
plt.tight_layout(); plt.savefig(f"{HERE}/fig_school_exposure_surface.png", dpi=200)
print("\nsaved b1c_school_exposure.csv and fig_school_exposure_surface.png")

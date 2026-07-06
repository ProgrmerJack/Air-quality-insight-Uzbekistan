"""
Formal multi-source fusion -> one calibrated per-school outdoor PM2.5 surface (closes the
'formal fusion' gap). Blends: reference level (FEM 8881, ACAG-validated 37.9) + the bias-corrected
municipal NETWORK spatial anomaly (IDW of corrected station annual means) + OSM near-road increment.
Output: data/pipeline/fused_school_surface.csv
"""
import os, csv, math
import numpy as np
from paths import pipeline_path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BG = 37.9                       # reference level (FEM 8881; ACAG satellite agrees to 0.5 ug/m3)
A, L = 5.0, 150.0
a, b, c = 0.951, 0.123, 3.88   # bias-correction coefficients (network->FEM), from bias_correction.py

# corrected annual mean per municipal station
net = list(csv.DictReader(open(os.path.join(ROOT, "data", "air_tashkent", "pm25_hourly.csv"), encoding="utf-8")))
st = {}
for r in net:
    if r["pm2_5"] in ("", "None", None) or r["humidity"] in ("", "None", None): continue
    p = float(r["pm2_5"]); h = float(r["humidity"])
    if p <= 0: continue
    st.setdefault((r["station_name"], float(r["lat"]), float(r["lon"])), []).append(a*p + b*h + c)
stations = [(k[1], k[2], float(np.mean(v))) for k, v in st.items()]
net_mean = float(np.mean([s[2] for s in stations]))
print(f"network stations: {len(stations)} | corrected annual range {min(s[2] for s in stations):.1f}-{max(s[2] for s in stations):.1f} (mean {net_mean:.1f})")

# schools (GIGA authoritative) with near-road distance from the GIGA index output
sch = list(csv.DictReader(open(pipeline_path("giga_school_injustice_index.csv"), encoding="utf-8")))
def idw(la, lo):
    num = den = 0.0
    for sla, slo, val in stations:
        d2 = (sla-la)**2 + ((slo-lo)*math.cos(math.radians(la)))**2
        if d2 < 1e-9: return val
        w = 1.0/d2; num += w*val; den += w
    return num/den

out = []
for s in sch:
    la, lo, dist = float(s["lat"]), float(s["lon"]), float(s["dist_m"])
    anomaly = idw(la, lo) - net_mean                      # network-measured within-city spatial pattern
    fused_outdoor = BG + anomaly + A*math.exp(-dist/L)    # reference level + measured anomaly + near-road
    out.append({"lat": s["lat"], "lon": s["lon"], "name": s["name"], "dist_m": s["dist_m"],
                "network_anomaly": round(anomaly, 2), "fused_outdoor_pm25": round(fused_outdoor, 1)})
fo = np.array([o["fused_outdoor_pm25"] for o in out])
print(f"fused outdoor surface (n={len(out)} GIGA schools): {fo.min():.1f}-{fo.max():.1f} ug/m3 (mean {fo.mean():.1f})")
print(f"  (reference-anchored level {BG}, network anomaly range {min(o['network_anomaly'] for o in out):+.1f}/{max(o['network_anomaly'] for o in out):+.1f}, + near-road)")
with open(pipeline_path("fused_school_surface.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
print("saved data/pipeline/fused_school_surface.csv")

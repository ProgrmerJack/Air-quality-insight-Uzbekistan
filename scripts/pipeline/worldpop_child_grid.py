"""
Step 3 (child-density layer) via the WorldPop stats API -- server-side aggregation, NO raster
download (the 'smart' route). Builds a population-density surface over the Tashkent metro on a
grid; child fraction is treated as ~uniform citywide, so relative child density ~ relative
population density (stated as a limitation). Output: data/pipeline/tashkent_pop_grid.csv
"""
import requests, json, time, csv, os
from paths import pipeline_path
H = {"User-Agent": "npjUS-research/1.0"}
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = pipeline_path("tashkent_pop_grid.csv")
S, W, N, E = 41.15, 69.10, 41.42, 69.45
NX = NY = 7                      # 49 cells (~3.5 km) -> modest API load
dx = (E - W) / NX; dy = (N - S) / NY

def cell_poly(i, j):
    x0, y0 = W + i*dx, S + j*dy
    return [[ [x0,y0],[x0+dx,y0],[x0+dx,y0+dy],[x0,y0+dy],[x0,y0] ]]

# 1) submit all tasks
tasks = []
for i in range(NX):
    for j in range(NY):
        geom = {"type": "Polygon", "coordinates": cell_poly(i, j)}
        try:
            r = requests.get("https://api.worldpop.org/v1/services/stats",
                             params={"dataset": "wpgppop", "year": "2020", "geojson": json.dumps(geom)},
                             headers=H, timeout=60)
            tid = r.json().get("taskid")
            cx, cy = W + (i+0.5)*dx, S + (j+0.5)*dy
            tasks.append({"i": i, "j": j, "clat": round(cy,4), "clon": round(cx,4), "tid": tid})
        except Exception as e:
            print("submit err", i, j, e)
        time.sleep(0.15)
print(f"submitted {len(tasks)} WorldPop tasks")

# 2) poll until all finished
import math
AREA = (dx*111.32) * (dy*111.32*math.cos(math.radians((S+N)/2)))  # km^2 per cell
rows = []
pending = {t["tid"]: t for t in tasks if t["tid"]}
for _ in range(40):
    done = []
    for tid, t in list(pending.items()):
        try:
            s = requests.get("https://api.worldpop.org/v1/tasks/" + tid, headers=H, timeout=30).json()
            if s.get("status") == "finished":
                pop = (s.get("data") or {}).get("total_population", 0) or 0
                rows.append({"clat": t["clat"], "clon": t["clon"], "pop": round(pop), "dens_per_km2": round(pop/AREA, 1)})
                done.append(tid)
        except Exception:
            pass
    for tid in done: pending.pop(tid, None)
    if not pending: break
    time.sleep(4)

rows.sort(key=lambda r: -r["dens_per_km2"])
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["clat","clon","pop","dens_per_km2"]); w.writeheader(); w.writerows(rows)
tot = sum(r["pop"] for r in rows)
print(f"cells with data: {len(rows)} | total pop ~{tot:,} | density {rows[-1]['dens_per_km2']}..{rows[0]['dens_per_km2']} /km2")
print("saved", OUT)

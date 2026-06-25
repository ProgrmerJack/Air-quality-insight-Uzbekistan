"""
Step 2 headline: validate/correct the municipal low-cost network against the U.S. Embassy
FEM reference and test whether the humidity bias REORDERS which schools look worst.

- Reference: OpenAQ Station 8881 (FEM BAM), sensor 25916.
- Network: nearest Air Tashkent station to the embassy = "Peoples' Friendship Square"
  (value_id 036112022, ~1 km away) -> near-co-location for calibration.
- Correction: Barkjohn-style multilinear (PM_corr = a*PM_raw + b*RH + c).
- Governance test: rank all network stations by raw vs corrected mean; report reordering.
"""
import os, re, csv, json, time, datetime as dt
import requests, numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
KEY = re.search(r"API_KEY\s*=\s*'([^']+)'",
                open(os.path.join(ROOT, "scripts", "fetch", "fetch_us_embassy_2022_2023.py"), encoding="utf-8").read()).group(1)
H = {"X-API-Key": KEY}
NET = os.path.join(ROOT, "data", "air_tashkent", "pm25_hourly.csv")

# 1) FEM reference 8881 / sensor 25916 over the network overlap window
def fem(date_from="2023-06-01", date_to="2025-03-04"):
    out = {}
    cur = dt.date.fromisoformat(date_from); end = dt.date.fromisoformat(date_to)
    while cur < end:
        nxt = (cur + dt.timedelta(days=32)).replace(day=1)
        page = 1
        while True:
            r = requests.get("https://api.openaq.org/v3/sensors/25916/measurements", headers=H,
                             params={"datetime_from": cur.isoformat(), "datetime_to": min(nxt, end).isoformat(),
                                     "limit": 1000, "page": page}, timeout=60)
            if r.status_code != 200: break
            res = r.json().get("results", [])
            if not res: break
            for m in res:
                loc = (m.get("period", {}).get("datetimeFrom", {}) or {}).get("local", "")
                v = m.get("value")
                if loc and v is not None and v >= 0:
                    out[loc[:13]] = v   # key by 'YYYY-MM-DDTHH' local
            if page * 1000 >= r.json().get("meta", {}).get("found", 0): break
            page += 1; time.sleep(0.2)
        cur = nxt
    return out

print("pulling FEM 8881 reference ...")
ref = fem()
print(f"  FEM hourly points: {len(ref)}")

# 2) network nearest-station hourly + RH
rows = list(csv.DictReader(open(NET, encoding="utf-8")))
NEAR = "036112022"   # Peoples' Friendship Square
pairs = []
for r in rows:
    if r["station_value_id"] != NEAR: continue
    k = (r["datetime"] or "")[:13]
    if k in ref and r["pm2_5"] not in ("", "None", None) and r["humidity"] not in ("", "None", None):
        pairs.append((float(r["pm2_5"]), float(r["humidity"]), float(r["temperature"] or "nan"), ref[k]))
pairs = [p for p in pairs if p[0] > 0 and p[3] > 0]
raw = np.array([p[0] for p in pairs]); rh = np.array([p[1] for p in pairs]); fe = np.array([p[3] for p in pairs])
print(f"co-located hourly pairs: {len(pairs)}")
if len(pairs) < 50:
    print("WARNING: too few overlapping pairs; widen window or pick another near station."); raise SystemExit

# raw agreement + RH-dependent bias
print(f"raw network mean {raw.mean():.1f} vs FEM mean {fe.mean():.1f}  (raw bias {100*(raw.mean()/fe.mean()-1):+.0f}%)")
print(f"raw correlation r = {np.corrcoef(raw, fe)[0,1]:.2f}")
for lo, hi in [(0,40),(40,60),(60,80),(80,101)]:
    msk = (rh >= lo) & (rh < hi)
    if msk.sum() > 20:
        print(f"  RH {lo}-{hi}% (n={msk.sum()}): network/FEM ratio = {raw[msk].mean()/fe[msk].mean():.2f}")

# 3) Barkjohn-style correction PM_corr = a*raw + b*RH + c (fit to FEM)
X = np.column_stack([raw, rh, np.ones_like(raw)])
coef, *_ = np.linalg.lstsq(X, fe, rcond=None)
corr = X @ coef
def rmse(a, b): return float(np.sqrt(np.mean((a - b) ** 2)))
print(f"\ncorrection: PM_corr = {coef[0]:.3f}*raw + {coef[1]:.3f}*RH + {coef[2]:.2f}")
print(f"RMSE raw->FEM {rmse(raw,fe):.1f} -> corrected {rmse(corr,fe):.1f} ug/m3 | "
      f"R2 {1-np.var(fe-corr)/np.var(fe):.2f}")

# 4) governance test: rank stations by raw vs corrected annual-ish mean
a, b, c = coef
st_raw, st_cor = {}, {}
for r in rows:
    if r["pm2_5"] in ("", "None", None) or r["humidity"] in ("", "None", None): continue
    p = float(r["pm2_5"]); h = float(r["humidity"])
    if p <= 0: continue
    st_raw.setdefault(r["station_name"], []).append(p)
    st_cor.setdefault(r["station_name"], []).append(a*p + b*h + c)
names = list(st_raw)
mean_raw = {n: np.mean(st_raw[n]) for n in names}
mean_cor = {n: np.mean(st_cor[n]) for n in names}
rank_raw = sorted(names, key=lambda n: -mean_raw[n])
rank_cor = sorted(names, key=lambda n: -mean_cor[n])
print("\n=== Does humidity bias misrank schools? ===")
print(f"{'station':40}{'raw':>7}{'corr':>7}{'dRank':>7}")
for n in rank_raw:
    dr = rank_cor.index(n) - rank_raw.index(n)
    print(f"{n.encode('ascii','replace').decode()[:38]:40}{mean_raw[n]:7.1f}{mean_cor[n]:7.1f}{dr:+7d}")
moved = sum(1 for n in names if rank_cor.index(n) != rank_raw.index(n))
print(f"\n{moved}/{len(names)} stations change rank after humidity correction; "
      f"top-ranked raw='{rank_raw[0].encode('ascii','replace').decode()}' vs corrected='{rank_cor[0].encode('ascii','replace').decode()}'")

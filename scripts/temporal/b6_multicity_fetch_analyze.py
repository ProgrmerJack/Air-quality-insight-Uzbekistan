"""
B6 (real) - Comparative school-exposure framework across six Central Asian capitals.
Fetches each U.S. Embassy reference monitor (OpenAQ v3) for Jan 2022-Jun 2023 and runs
the identical pipeline used for Tashkent. Key reused from repo fetch script.

Outputs: outputs/multicity/<city>_hourly.csv (cached) and outputs/multicity_comparison.csv
"""
import re, os, time, requests
from datetime import datetime, timedelta
import pandas as pd, numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
KEY = re.search(r"API_KEY\s*=\s*'([^']+)'",
                open(os.path.join(ROOT, "scripts", "fetch", "fetch_us_embassy_2022_2023.py"), encoding="utf-8").read()).group(1)
H = {"X-API-Key": KEY}
OUT = os.path.join(ROOT, "outputs", "multicity"); os.makedirs(OUT, exist_ok=True)

CITIES = {  # city: location_id
    "Tashkent": 8881, "Almaty": 8876, "Astana": 7094,
    "Bishkek": 8827, "Dushanbe": 8684, "Ashgabat": 8870,
}
START, END = datetime(2022, 1, 1), datetime(2023, 6, 30)

def pm25_sensor(loc_id):
    r = requests.get(f"https://api.openaq.org/v3/locations/{loc_id}/sensors", headers=H, timeout=60)
    for s in r.json().get("results", []):
        if s.get("parameter", {}).get("name") == "pm25":
            return s["id"]
    return None

def fetch_city(loc_id):
    sid = pm25_sensor(loc_id)
    if not sid: return None
    rows, cur = [], START
    while cur < END:
        nxt = (cur + timedelta(days=32)).replace(day=1)
        if nxt > END: nxt = END
        page = 1
        while True:
            r = requests.get(f"https://api.openaq.org/v3/sensors/{sid}/measurements", headers=H,
                             params={"datetime_from": cur.strftime("%Y-%m-%d"),
                                     "datetime_to": nxt.strftime("%Y-%m-%d"),
                                     "limit": 1000, "page": page}, timeout=60)
            if r.status_code != 200: break
            res = r.json().get("results", [])
            if not res: break
            for m in res:
                p = m.get("period", {}).get("datetimeFrom", {})
                rows.append({"local": p.get("local", ""), "value": m.get("value")})
            if page * 1000 >= r.json().get("meta", {}).get("found", 0): break
            page += 1; time.sleep(0.25)
        cur = nxt
    df = pd.DataFrame(rows)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df[df["value"] > 0].dropna(subset=["value"]).copy()

def season(m): return {12:"Winter",1:"Winter",2:"Winter",3:"Spring",4:"Spring",5:"Spring",
                       6:"Summer",7:"Summer",8:"Summer",9:"Fall",10:"Fall",11:"Fall"}[m]
def paf(c, rr=1.08, c0=5): return 1 - rr ** (-(c - c0) / 10.0)

summary = []
for city, lid in CITIES.items():
    cache = os.path.join(OUT, f"{city}_hourly.csv")
    if os.path.exists(cache):
        df = pd.read_csv(cache)
    else:
        print(f"fetching {city} (loc {lid}) ...")
        df = fetch_city(lid)
        if df is None or df.empty:
            print(f"  no data for {city}"); continue
        df.to_csv(cache, index=False)
    df["dt"] = pd.to_datetime(df["local"], format="mixed", errors="coerce")
    df = df.dropna(subset=["dt"])
    df["hour"] = df["dt"].dt.hour; df["dow"] = df["dt"].dt.dayofweek
    df["date"] = df["dt"].dt.date; df["mon"] = df["dt"].dt.month
    daily = df.groupby("date")["value"].agg(["size", "mean"])
    d18 = daily[daily["size"] >= 18]
    annual = d18["mean"].mean()
    wexc = 100 * (d18["mean"] > 15).mean()
    d18m = d18.copy(); d18m["season"] = pd.to_datetime(d18m.index).month.map(season)
    winter = d18m[d18m.season == "Winter"]["mean"].mean()
    summer = d18m[d18m.season == "Summer"]["mean"].mean()
    school = df[(df.dow < 5) & (df.hour.between(8, 15))]["value"].mean()
    summary.append({
        "City": city, "n_hourly": len(df), "n_days": len(d18),
        "annual_mean": round(annual, 1), "winter_mean": round(winter, 1),
        "summer_mean": round(summer, 1),
        "winter_summer_pct": round(100 * (winter / summer - 1)) if summer else None,
        "pct_days_gt15": round(wexc, 1), "school_hours_mean": round(school, 1),
        "fold_WHO_annual": round(annual / 5, 1),
        "PAF_resp_pct": round(100 * paf(annual), 1),
        "classroom_typical": round(annual * 0.65, 1),
    })
    print(f"  {city}: annual {annual:.1f}, winter {winter:.1f}, %days>15 {wexc:.0f}, "
          f"school {school:.1f}, PAF {100*paf(annual):.0f}%  (n={len(df)})")

comp = pd.DataFrame(summary).sort_values("annual_mean", ascending=False)
comp.to_csv(os.path.join(ROOT, "outputs", "multicity", "multicity_comparison.csv"), index=False)
print("\n=== Comparative table ==="); print(comp.to_string(index=False))
print("\nsaved outputs/multicity_comparison.csv")

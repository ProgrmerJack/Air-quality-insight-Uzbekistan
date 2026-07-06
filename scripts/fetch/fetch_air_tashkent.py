"""
Air Tashkent municipal network harvester (measured-at-school PM2.5).

The public air.tashkent.uz React app calls the city API gateway with HTTP Basic Auth
credentials embedded in its public JS bundle; the endpoint serves the same public
air-quality data the site displays, with a deep retrospective archive (>= mid-2023).
This script pulls per-station hourly PM2.5 + meteorology and writes a tidy long CSV.

Several stations sit on school / kindergarten grounds -> measured at-school exposure.

Usage (run from repo root):
  python scripts/fetch/fetch_air_tashkent.py --start 2023-06 --end 2025-12        # full backfill
  python scripts/fetch/fetch_air_tashkent.py --start 2025-11 --end 2025-11 --schools-only --test
Resumable: months already present in the output CSV are skipped.

Credentials are app-embedded (public); override via env AIR_TASHKENT_USER / AIR_TASHKENT_PASS.
Respect the site's terms; this is intended for academic use of public environmental data.
"""
import os, csv, json, time, argparse, datetime as dt, sys
import requests

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BASE = "https://apigateway.digitaltashkent.uz/api/v1"
INFO_EP = "/meteo_stations/meteo_stations_info/"
DATA_EP = "/uzgidro/meteostations_data/"
AUTH = (os.environ.get("AIR_TASHKENT_USER", "meteo_user"),
        os.environ.get("AIR_TASHKENT_PASS", "65hzngd4dZPH8i5"))
H = {"User-Agent": "npjUS-academic-research/1.0", "Content-Type": "application/json"}

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUTDIR = os.path.join(ROOT, "data", "air_tashkent")
os.makedirs(OUTDIR, exist_ok=True)
STATIONS_CSV = os.path.join(OUTDIR, "stations.csv")
DATA_CSV = os.path.join(OUTDIR, "pm25_hourly.csv")

SCHOOL_KW = ("school", "kindergarten", "maktab", "bog'cha", "bogcha", "gimnaziya", "lyceum", "litsey")
FIELDS = ["station_value_id", "station_name", "is_school", "lat", "lon", "datetime",
          "pm2_5", "pm2_5_who", "pm2_5_uzb", "pm10", "pm1", "humidity", "temperature", "aqi"]


def get_stations():
    r = requests.get(BASE + INFO_EP, auth=AUTH, headers=H, timeout=40)
    r.raise_for_status()
    info = r.json()["data"]
    # station_id holds the station list
    lst = info[0]["station_id"] if isinstance(info, list) else info["station_id"]
    out = []
    for s in lst:
        name = s.get("en_name") or s.get("uz_name") or str(s.get("value_id"))
        is_school = any(k in name.lower() for k in SCHOOL_KW)
        out.append({"value_id": str(s.get("value_id")), "name": name,
                    "is_school": is_school,
                    "lat": s.get("lat"), "lon": s.get("lon")})
    return out


def month_iter(start, end):
    y, m = int(start[:4]), int(start[5:7]); ey, em = int(end[:4]), int(end[5:7])
    while (y, m) <= (ey, em):
        yield y, m
        m += 1
        if m > 12: m = 1; y += 1


def fetch(value_id, s, e):
    body = {"start_date": s, "end_date": e, "params": "pm2_5", "station_id": value_id}
    for attempt in range(4):
        try:
            r = requests.post(BASE + DATA_EP, auth=AUTH, headers=H, data=json.dumps(body), timeout=90)
            if r.status_code == 200:
                return r.json().get("data", [])
            if r.status_code in (429, 500, 502, 503): time.sleep(5 * (attempt + 1)); continue
            return []
        except requests.RequestException:
            time.sleep(4 * (attempt + 1))
    return []


def done_keys():
    """(value_id, YYYY-MM) already in the output, for resumability."""
    seen = set()
    if os.path.exists(DATA_CSV):
        with open(DATA_CSV, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                seen.add((row["station_value_id"], row["datetime"][:7]))
    return seen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2023-06"); ap.add_argument("--end", default="2025-12")
    ap.add_argument("--schools-only", action="store_true")
    ap.add_argument("--test", action="store_true", help="one week of the start month only")
    a = ap.parse_args()

    stations = get_stations()
    with open(STATIONS_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["value_id", "name", "is_school", "lat", "lon"]); w.writeheader(); w.writerows(stations)
    n_sch = sum(s["is_school"] for s in stations)
    print(f"stations: {len(stations)} ({n_sch} on school/kindergarten grounds) -> {STATIONS_CSV}")
    if a.schools_only:
        stations = [s for s in stations if s["is_school"]]

    seen = done_keys()
    new = not os.path.exists(DATA_CSV)
    f = open(DATA_CSV, "a", newline="", encoding="utf-8"); w = csv.DictWriter(f, fieldnames=FIELDS)
    if new: w.writeheader()
    total = 0
    for st in stations:
        for y, m in month_iter(a.start, a.end):
            if (st["value_id"], f"{y:04d}-{m:02d}") in seen:
                continue
            s = f"{y:04d}-{m:02d}-01"
            if a.test:
                e = f"{y:04d}-{m:02d}-07"
            else:
                nm = (dt.date(y, m, 28) + dt.timedelta(days=7)).replace(day=1)
                e = (nm - dt.timedelta(days=1)).isoformat()
            recs = fetch(st["value_id"], s, e)
            for rec in recs:
                w.writerow({
                    "station_value_id": st["value_id"], "station_name": st["name"],
                    "is_school": st["is_school"], "lat": st["lat"], "lon": st["lon"],
                    "datetime": rec.get("datetime"),
                    "pm2_5": rec.get("pm2_5"), "pm2_5_who": rec.get("pm2_5_who"),
                    "pm2_5_uzb": rec.get("pm2_5_uzb"), "pm10": rec.get("pm10"), "pm1": rec.get("pm1"),
                    "humidity": rec.get("humidity"), "temperature": rec.get("temperature"),
                    "aqi": rec.get("aqi")})
            total += len(recs)
            print(f"  {st['name'][:34]:34} {y}-{m:02d}: {len(recs)} rows")
            f.flush(); time.sleep(0.6)
            if a.test: break
    f.close()
    print(f"done: +{total} rows -> {DATA_CSV}")


if __name__ == "__main__":
    main()

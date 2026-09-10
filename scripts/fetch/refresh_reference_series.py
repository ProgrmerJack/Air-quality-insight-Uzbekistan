#!/usr/bin/env python3
"""
refresh_reference_series.py -- pull the FEM reference series for an arbitrary window.

This one script closes the three biggest open weaknesses in the project at once
(CANONICAL_NUMBERS.md §4 and §8):

  1. The withdrawn "12,243 paired hours, r ~ 0.65" claim. It came from bias_correction.py
     pulling 2023-06 -> 2025-03 live; that window was never archived, so nobody can check it.
  2. The anchor-period limitation. The published reference record stops 29 June 2023 while
     the network archive starts 1 June 2023, so the x1.325 anchor compares non-overlapping
     periods and has to assume the city level was stable. With a contemporaneous reference
     series that assumption disappears entirely.
  3. The 52.3 ug/m3 discrepancy. Ecological Questions 37(1), DOI 10.12775/eq.2026.002 reports
     52.3 for Tashkent in 2024 from THIS SAME STATION, against our 37.9 for 2022-H1 2023.
     The per-calendar-year table this script prints answers that directly.

Needs a free OpenAQ key -- see openaq_key.py. Roughly an hour of wall-clock for 2.5 years.

    python scripts/fetch/refresh_reference_series.py --from 2023-06-01 --to 2025-12-31
    python scripts/fetch/refresh_reference_series.py --from 2024-01-01 --to 2024-12-31 \
        --out outputs/reference/reference_fem_openaq8881_2024.csv

Then re-run, in order:
    python scripts/pipeline/reconcile_pairing.py --reference <the new file> --out CANONICAL_NUMBERS.md
    python scripts/pipeline/bias_correction.py
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import sys
import time
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from openaq_key import openaq_headers  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
STATION_ID, SENSOR_ID = 8881, 25916
API = f"https://api.openaq.org/v3/sensors/{SENSOR_ID}/measurements"


def fetch_window(headers: dict, a: dt.date, b: dt.date, pause: float = 0.3) -> list[dict]:
    rows, page = [], 1
    while True:
        r = requests.get(API, headers=headers, timeout=90, params={
            "datetime_from": a.isoformat(), "datetime_to": b.isoformat(),
            "limit": 1000, "page": page})
        if r.status_code == 401:
            raise SystemExit("! HTTP 401 -- the OpenAQ key is invalid or revoked.\n"
                             "  Get a fresh one at https://explore.openaq.org/register")
        if r.status_code != 200:
            print(f"    ! HTTP {r.status_code} on page {page}: {r.text[:120]}", file=sys.stderr)
            break
        payload = r.json()
        res = payload.get("results", [])
        if not res:
            break
        rows.extend(res)
        if page * 1000 >= payload.get("meta", {}).get("found", 0):
            break
        page += 1
        time.sleep(pause)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="start", default="2023-06-01")
    ap.add_argument("--to", dest="end", default="2025-12-31")
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()

    start, end = dt.date.fromisoformat(a.start), dt.date.fromisoformat(a.end)
    out = a.out or (ROOT / "outputs" / "reference" /
                    f"reference_fem_openaq8881_{start:%Y%m%d}_{end:%Y%m%d}.csv")
    headers = openaq_headers()

    print(f"OpenAQ station {STATION_ID} / sensor {SENSOR_ID}: {start} .. {end}")
    all_rows, cur = [], start
    while cur < end:
        nxt = min((cur + dt.timedelta(days=32)).replace(day=1), end)
        got = fetch_window(headers, cur, nxt)
        all_rows.extend(got)
        print(f"  {cur:%Y-%m}  {len(got):5d} records   (total {len(all_rows):,})")
        cur = nxt
    if not all_rows:
        print("! nothing retrieved")
        return 1

    df = pd.DataFrame([{
        "datetime_utc": (m.get("period", {}).get("datetimeFrom", {}) or {}).get("utc", ""),
        "datetime_local": (m.get("period", {}).get("datetimeFrom", {}) or {}).get("local", ""),
        "value": m.get("value"),
        "coverage_pct": (m.get("coverage", {}) or {}).get("percentComplete"),
    } for m in all_rows])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df[(df.value >= 0) & (df.value < 1000)].dropna(subset=["value"])
    df = df.drop_duplicates(subset=["datetime_utc"]).sort_values("datetime_utc")

    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"\nwrote {len(df):,} valid hours -> {out.relative_to(ROOT)}")

    ts = pd.to_datetime(df.datetime_local, errors="coerce", utc=True)
    print(f"period mean: {df.value.mean():.2f} ug/m3")
    print("\nper calendar year -- compare against the 52.3 claim for 2024:")
    print(f"  {'year':6s}{'n':>8s}{'mean':>9s}{'completeness':>14s}")
    for y, g in df.assign(y=ts.dt.year).groupby("y"):
        hours = 8784 if int(y) % 4 == 0 else 8760
        print(f"  {int(y):<6d}{len(g):>8,}{g.value.mean():>9.2f}{100*len(g)/hours:>13.1f}%")
    print("\nNext: python scripts/pipeline/reconcile_pairing.py --reference "
          f"{out.relative_to(ROOT)} --out CANONICAL_NUMBERS.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())

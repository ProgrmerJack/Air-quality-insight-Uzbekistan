#!/usr/bin/env python3
"""
reconcile_pairing.py -- settle the 633 vs 12,243 paired-hours conflict.

docs/MINISTRY_ENGAGEMENT_PLAN.md claims 12,243 paired hours, r ~ 0.65.
docs/ministry/01_bias_correction_note_* claims 633 paired hours, r = 0.55.

Recomputes overlap and correlation under four pairing rules so the numbers can be
labelled rather than one of them retracted. Reads only published files -- no API call.

    python scripts/pipeline/reconcile_pairing.py

TIMEZONE (the reason a naive version of this script gets r wrong):
data/air_tashkent/pm25_hourly.csv carries a NAIVE `datetime` in Tashkent local time,
while the reference series carries `datetime_utc`. Parsing both with utc=True shifts
the network 5 hours late and drags the correlation down for no physical reason.
Uzbekistan has been UTC+5 with no DST since 1995, so a fixed +05:00 is exact.

Exit 0 = a rule reproduced 12,243 (conflict explained); 1 = none did.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
NETWORK = ROOT / "data" / "air_tashkent" / "pm25_hourly.csv"
REFERENCE = ROOT / "outputs" / "reference" / "reference_fem_openaq8881_2022_2023.csv"
TASHKENT = "+05:00"  # fixed since 1995, no DST


def load_network(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    ts = pd.to_datetime(df["datetime"], errors="coerce")
    out = pd.DataFrame({
        # naive local -> UTC. tz_localize, NOT utc=True: the latter would mislabel
        # local clock time as UTC and misalign every pair by five hours.
        "ts": ts.dt.tz_localize(TASHKENT).dt.tz_convert("UTC").dt.floor("h"),
        "pm25": pd.to_numeric(df["pm2_5"], errors="coerce"),
        "station": df["station_name"].astype(str).str.strip(),
        "sid": df["station_value_id"].astype(str).str.strip(),
    })
    before = len(out)
    out = out.dropna(subset=["ts", "pm25"])
    out = out[(out.pm25 >= 0) & (out.pm25 < 1000)]  # same filter as measured_validation.py
    print(f"  network   : {before:,} rows -> {len(out):,} valid  "
          f"[{out.ts.min()} .. {out.ts.max()}]  {out.station.nunique()} stations")
    return out


def load_reference(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    out = pd.DataFrame({
        "ts": pd.to_datetime(df["datetime_utc"], utc=True, errors="coerce").dt.floor("h"),
        "ref": pd.to_numeric(df["value"], errors="coerce"),
    })
    before = len(out)
    out = out.dropna(subset=["ts", "ref"])
    out = out[(out.ref >= 0) & (out.ref < 1000)]
    out = out.groupby("ts", as_index=False).ref.mean()
    print(f"  reference : {before:,} rows -> {len(out):,} valid hours  "
          f"[{out.ts.min()} .. {out.ts.max()}]  mean {out.ref.mean():.2f}")
    return out


def stats(m: pd.DataFrame, netcol="net", refcol="ref") -> dict:
    if len(m) < 3:
        return dict(n=len(m), r=np.nan, net_mean=np.nan, ref_mean=np.nan, factor=np.nan)
    nm, rm = float(m[netcol].mean()), float(m[refcol].mean())
    return dict(n=len(m), r=float(m[netcol].corr(m[refcol])), net_mean=nm, ref_mean=rm,
                factor=rm / nm if nm else np.nan)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--network", type=Path, default=NETWORK)
    ap.add_argument("--reference", type=Path, default=None)
    ap.add_argument("--nearest-station", default="Friendship")
    ap.add_argument("--out", type=Path, default=None, help="append a report block to this file")
    a = ap.parse_args()

    ref_path = a.reference or REFERENCE
    for p in (a.network, ref_path):
        if not p.exists():
            sys.exit(f"! not found: {p}")

    print("Loading:")
    net = load_network(a.network)
    ref = load_reference(ref_path)

    lo, hi = max(net.ts.min(), ref.ts.min()), min(net.ts.max(), ref.ts.max())
    span = 0 if hi < lo else (hi - lo).total_seconds() / 3600
    print(f"\nCalendar overlap: {lo} .. {hi}  ({span:,.0f} h)")

    results: dict[str, dict] = {}

    # Rule A -- strict: nearest station only, same hour, both reporting.
    sel = net[net.station.str.contains(a.nearest_station, case=False, na=False)]
    if sel.empty:
        print(f"! no station matched '{a.nearest_station}'; have {sorted(net.station.unique())}")
    else:
        s = sel.groupby("ts", as_index=False).pm25.mean().rename(columns={"pm25": "net"})
        results["strict (nearest station, hourly)"] = stats(s.merge(ref, on="ts"))

    # Rule B -- pooled: every station-hour paired to that hour's reference value.
    results["pooled (all stations x ref hour)"] = stats(
        net.rename(columns={"pm25": "net"}).merge(ref, on="ts"))

    # Rule C -- city mean: network stations averaged to one value per hour.
    city = net.groupby("ts", as_index=False).pm25.mean().rename(columns={"pm25": "net"})
    results["city hourly mean vs reference"] = stats(city.merge(ref, on="ts"))

    # Rule D -- daily means.
    nd = (net.assign(d=net.ts.dt.date).groupby("d", as_index=False).pm25.mean()
          .rename(columns={"pm25": "net"}))
    rd = ref.assign(d=ref.ts.dt.date).groupby("d", as_index=False).ref.mean()
    results["daily means"] = stats(nd.merge(rd, on="d"))

    hdr = f"{'pairing rule':<40}{'n':>9}{'r':>8}{'net':>8}{'ref':>8}{'factor':>9}"
    print("\n" + hdr + "\n" + "-" * len(hdr))
    for name, s in results.items():
        f = lambda x, p=1, pre="": "n/a" if np.isnan(x) else f"{pre}{x:.{p}f}"
        print(f"{name:<40}{s['n']:>9,}{f(s['r'],3):>8}{f(s['net_mean']):>8}"
              f"{f(s['ref_mean']):>8}{f(s['factor'],3,'x'):>9}")

    print("\nVerdict")
    hit633 = [k for k, s in results.items() if abs(s["n"] - 633) <= 25]
    hit12k = [k for k, s in results.items() if abs(s["n"] - 12243) <= 400]
    print(f"  633   reproduced by: {', '.join(hit633) or 'NOTHING'}")
    print(f"  12243 reproduced by: {', '.join(hit12k) or 'NOTHING'}")
    rc = 0 if (hit633 and hit12k) else 1
    if rc:
        print("\n  -> label only what is reproduced here; mark the other UNRESOLVED.")

    if a.out:
        lines = ["", "## Hour-matching reconciliation", "",
                 "<!-- regenerate: python scripts/pipeline/reconcile_pairing.py "
                 "--out CANONICAL_NUMBERS.md -->", "",
                 f"Calendar overlap of the two published series: `{lo}` .. `{hi}` "
                 f"({span:,.0f} h).", "",
                 "| pairing rule | n | r | network mean | reference mean | implied factor |",
                 "|---|---:|---:|---:|---:|---:|"]
        for name, s in results.items():
            f = lambda x, p=1: "n/a" if np.isnan(x) else f"{x:.{p}f}"
            lines.append(f"| {name} | {s['n']:,} | {f(s['r'],3)} | {f(s['net_mean'])} | "
                         f"{f(s['ref_mean'])} | {f(s['factor'],3)} |")
        lines.append("")
        with open(a.out, "a", encoding="utf-8") as fh:
            fh.write("\n".join(lines))
        print(f"\n  appended to {a.out}")
    return rc


if __name__ == "__main__":
    sys.exit(main())

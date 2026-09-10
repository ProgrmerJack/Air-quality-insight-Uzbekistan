"""Audit of the public alert scale published by air.tashkent.uz.

Survey before writing this file (CLAUDE.md rule 2): searched scripts/ for
`aqi|AQI|breakpoint|alert`. The only quantitative hit is
scripts/temporal/comprehensive_analysis.py:140, which bins *reference* concentrations into
EPA categories for a distribution summary. Nothing audits the portal's own `aqi` field,
identifies which breakpoint set produces it, or compares published against
reference-anchored categories. This is new.

Two questions, both bearing on PF-46 Annex 2 item 33(a) (public alerting by risk level):

  Q1  Which AQI breakpoint set reproduces the portal's published `aqi` field?
      Candidates: the legacy US EPA PM2.5 breakpoints, and the set revised by the US EPA
      in the final rule published 6 March 2024, effective 6 May 2024, which lowered the
      annual PM2.5 NAAQS from 12.0 to 9.0 ug/m3 and moved the upper breakpoints.
      The archive runs to 31 December 2025, i.e. entirely after that effective date.

  Q2  How many published hours sit in a *better* alert category than the same hour would
      sit in after reference anchoring (x1.325)? The category boundary that matters for
      PF-46 item 33(b) is "Unhealthy for sensitive groups", which is the level at which
      protective measures for children are triggered.

Run:  python3 scripts/pipeline/alert_scale_audit.py
Out:  data/pipeline/validation/alert_scale_audit.csv
"""
from __future__ import annotations

import hashlib
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data" / "air_tashkent" / "pm25_hourly.csv"
OUT = ROOT / "data" / "pipeline" / "validation" / "alert_scale_audit.csv"

FACTOR = 1.325  # reference anchor from scripts/pipeline/bias_correction.py

# (C_low, C_high, AQI_low, AQI_high)
LEGACY = [(0.0, 12.0, 0, 50), (12.1, 35.4, 51, 100), (35.5, 55.4, 101, 150),
          (55.5, 150.4, 151, 200), (150.5, 250.4, 201, 300), (250.5, 500.4, 301, 500)]
CURRENT = [(0.0, 9.0, 0, 50), (9.1, 35.4, 51, 100), (35.5, 55.4, 101, 150),
           (55.5, 125.4, 151, 200), (125.5, 225.4, 201, 300), (225.5, 325.4, 301, 500)]

CATEGORIES = ["Good", "Moderate", "Unhealthy for sensitive groups",
              "Unhealthy", "Very unhealthy", "Hazardous"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def make_aqi(bps):
    def f(c: float) -> float:
        if not np.isfinite(c):
            return np.nan
        for c_lo, c_hi, a_lo, a_hi in bps:
            if c_lo <= c <= c_hi:
                return round((a_hi - a_lo) / (c_hi - c_lo) * (c - c_lo) + a_lo)
        return 500.0
    return f


def category(aqi: np.ndarray) -> np.ndarray:
    return np.select([aqi <= 50, aqi <= 100, aqi <= 150, aqi <= 200, aqi <= 300],
                     [0, 1, 2, 3, 4], default=5)


def main() -> None:
    if not SRC.exists():
        sys.exit(f"missing input: {SRC}")

    df = pd.read_csv(SRC, dtype={"station_value_id": str}, parse_dates=["datetime"])
    d = df.dropna(subset=["pm2_5", "aqi"]).copy()

    # ---- Q1: which breakpoint set reproduces the published aqi? ----------------------
    fits = {}
    for name, bps in (("legacy (pre-2024)", LEGACY), ("current (2024 revision)", CURRENT)):
        pred = d["pm2_5"].map(make_aqi(bps))
        fits[name] = (100 * (pred == d["aqi"]).mean(), 100 * ((pred - d["aqi"]).abs() <= 1).mean())

    # ---- Q2: category understatement from the uncorrected level ---------------------
    f_leg = make_aqi(LEGACY)
    pub_cat = category(d["pm2_5"].map(f_leg).to_numpy())
    anc_cat = category((d["pm2_5"] * FACTOR).map(f_leg).to_numpy())

    better = int((anc_cat > pub_cat).sum())
    pairs = (pd.DataFrame({"published": pub_cat, "anchored": anc_cat})
             .value_counts().reset_index(name="hours"))
    pairs = pairs[pairs["published"] != pairs["anchored"]].copy()
    pairs["published"] = [CATEGORIES[i] for i in pairs["published"]]
    pairs["anchored"] = [CATEGORIES[i] for i in pairs["anchored"]]
    pairs = pairs.sort_values("hours", ascending=False)

    # hours that cross INTO the child-protection category specifically
    SENSITIVE = 2
    into_sensitive = int(((pub_cat < SENSITIVE) & (anc_cat >= SENSITIVE)).sum())

    OUT.parent.mkdir(parents=True, exist_ok=True)
    pairs.to_csv(OUT, index=False)

    print("=" * 78)
    print("air.tashkent.uz - public alert scale audit")
    print("=" * 78)
    print(f"input    : {SRC.relative_to(ROOT)}")
    print(f"sha256   : {sha256(SRC)}")
    print(f"hours    : {len(d):,} with both pm2_5 and aqi")
    print(f"period   : {d['datetime'].min()} -> {d['datetime'].max()}")
    print(f"python   : {platform.python_version()}  pandas {pd.__version__}  numpy {np.__version__}")
    print(f"command  : python3 scripts/pipeline/alert_scale_audit.py")
    print("-" * 78)
    print("Q1  Which breakpoint set reproduces the published aqi field?")
    for name, (exact, near) in fits.items():
        print(f"      {name:<26} exact {exact:6.2f}%   within +/-1 {near:6.2f}%")
    print("-" * 78)
    print(f"Q2  Published category better than reference-anchored category:")
    print(f"      {better:,} hours of {len(d):,}  ({100*better/len(d):.1f}%)")
    print(f"      of which cross INTO '{CATEGORIES[SENSITIVE]}' or worse: {into_sensitive:,} hours")
    print()
    print(pairs.head(8).to_string(index=False))
    print("-" * 78)
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

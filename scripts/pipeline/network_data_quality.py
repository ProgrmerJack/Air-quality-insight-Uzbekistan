"""Data-quality audit of the public air.tashkent.uz hourly archive.

Survey before writing this file (CLAUDE.md rule 2): searched the repo for
`outlier|implausib|qc_|quality_control|sanity|anomal` and for the API host names across
all *.py. Only hits were scripts/fetch/fetch_air_tashkent.py (fetches raw, no filtering),
scripts/temporal/process_air_quality.py (dropna only) and scripts/pipeline/fusion_surface.py
(spatial anomaly, not data quality). No existing script audits the archive, so this is new.

Defect classes D1-D9 were fixed BEFORE the first run (pre-specified analysis plan). Any
class added after seeing results is marked POST-HOC in the output.

Definitions used:
  PM2.5 is by definition a subset of PM10, and PM1 a subset of PM2.5, so pm2_5 > pm10 and
  pm1 > pm2_5 are internal contradictions in the same record, not merely improbable values.
  National norms are SanKvaN 0053-23: PM2.5 daily 60 ug/m3, annual 35 ug/m3.

Run:  python3 scripts/pipeline/network_data_quality.py
Out:  data/pipeline/validation/network_data_quality.csv   (per-defect, per-station counts)
      stdout run-log with input hash, versions and the headline numbers.
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
OUT = ROOT / "data" / "pipeline" / "validation" / "network_data_quality.csv"

# SanKvaN 0053-23 (07.08.2023 no.18; PM2.5 as amended 21.05.2024 no.13)
MAC_DAILY = 60.0
MAC_ANNUAL = 35.0
# The two ratio fields in the API are documented as pm2_5 divided by these constants.
WHO_ANNUAL = 5.0
UZB_ANNUAL = 35.0
STUCK_HOURS = 24          # consecutive identical values that count as a stuck sensor
PLAUSIBLE_MAX = 1000.0    # ug/m3; above this a 1-hour PM2.5 value is not physical for this city


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def stuck_runs(g: pd.DataFrame, col: str = "pm2_5", n: int = STUCK_HOURS) -> int:
    """Hours belonging to a run of >= n consecutive identical, non-null values.

    Sorted by time within a station. Nulls break a run: a gap is not evidence of sticking.
    """
    s = g.sort_values("datetime")[col]
    grp = (s != s.shift()).cumsum()
    sizes = s.groupby(grp).transform("size")
    return int(((sizes >= n) & s.notna()).sum())


def main() -> None:
    if not SRC.exists():
        sys.exit(f"missing input: {SRC}")

    df = pd.read_csv(SRC, dtype={"station_value_id": str}, parse_dates=["datetime"])
    n_rows = len(df)
    n_valid = int(df["pm2_5"].notna().sum())

    # ---- pre-specified defect masks -------------------------------------------------
    pm, p10, p1 = df["pm2_5"], df["pm10"], df["pm1"]
    masks = {
        "D1 pm2_5 > 1000 ug/m3 (implausible)": pm > PLAUSIBLE_MAX,
        "D2 pm2_5 > pm10 (PM2.5 is a subset of PM10)": pm > p10,
        "D3 pm1 > pm2_5 (PM1 is a subset of PM2.5)": p1 > pm,
        "D4a pm2_5_who != pm2_5/5": (df["pm2_5_who"] - pm / WHO_ANNUAL).abs() > 0.05,
        "D4b pm2_5_uzb != pm2_5/35": (df["pm2_5_uzb"] - pm / UZB_ANNUAL).abs() > 0.05,
        "D5 pm2_5 <= 0": pm <= 0,
        "D7 duplicate station-hour": df.duplicated(["station_value_id", "datetime"], keep=False),
        "D9 temperature exactly 0.0": df["temperature"] == 0.0,
    }
    # ---- POST-HOC classes -----------------------------------------------------------
    # Added AFTER the first run, when D1 returned zero and the >1000 values turned out to
    # be in pm10 rather than pm2_5. Labelled post-hoc per the pre-specified-plan protocol.
    masks["D10 pm10 > 1000 ug/m3 (POST-HOC)"] = p10 > PLAUSIBLE_MAX
    masks["D12 pm1 == pm2_5 exactly, channel echo (POST-HOC)"] = (p1 == pm) & p1.notna()
    masks["D13 temperature > 50 C (POST-HOC)"] = df["temperature"] > 50

    # D6 needs a per-station run-length pass rather than a row-wise mask.
    stuck = df.groupby("station_value_id", group_keys=False).apply(stuck_runs, include_groups=False)

    rows = []
    for name, m in masks.items():
        m = m.fillna(False)
        per_st = df.loc[m].groupby("station_value_id").size()
        rows.append({
            "defect": name,
            "hours_affected": int(m.sum()),
            "pct_of_valid": round(100 * int(m.sum()) / n_valid, 3),
            "stations_affected": int(per_st.gt(0).sum()),
        })
    # D11 POST-HOC: pm10 frozen for >=3 h while pm2_5 keeps moving -> a stuck PM10 channel,
    # which a plain "identical value" test on pm10 alone would not distinguish from calm air.
    def _run(g, col, n=3):
        s_ = g.sort_values("datetime")[col]
        grp = (s_ != s_.shift()).cumsum()
        return (s_.groupby(grp).transform("size") >= n) & s_.notna()
    p10_stuck = df.groupby("station_value_id", group_keys=False).apply(_run, col="pm10", include_groups=False)
    p25_stuck = df.groupby("station_value_id", group_keys=False).apply(_run, col="pm2_5", include_groups=False)
    frozen = (p10_stuck & ~p25_stuck).fillna(False)
    rows.append({
        "defect": "D11 pm10 frozen >=3h while pm2_5 varies (POST-HOC)",
        "hours_affected": int(frozen.sum()),
        "pct_of_valid": round(100 * int(frozen.sum()) / n_valid, 3),
        "stations_affected": int(df.loc[frozen, "station_value_id"].nunique()),
    })

    rows.append({
        "defect": f"D6 stuck sensor (>= {STUCK_HOURS} identical consecutive hours)",
        "hours_affected": int(stuck.sum()),
        "pct_of_valid": round(100 * int(stuck.sum()) / n_valid, 3),
        "stations_affected": int((stuck > 0).sum()),
    })

    # ---- D8 completeness -------------------------------------------------------------
    span = df["datetime"].max() - df["datetime"].min()
    expected = int(span.total_seconds() // 3600) + 1
    comp = (df.groupby("station_value_id")["pm2_5"].apply(lambda s: s.notna().sum()) / expected * 100)
    rows.append({
        "defect": "D8 completeness shortfall (mean across stations)",
        "hours_affected": int(expected * len(comp) - int(df["pm2_5"].notna().sum())),
        "pct_of_valid": round(100 - comp.mean(), 3),
        "stations_affected": int((comp < 90).sum()),
    })

    res = pd.DataFrame(rows).sort_values("hours_affected", ascending=False)

    # ---- decision impact: the PF-46 Annex-1 KPI --------------------------------------
    # KPI = number of days on which the national PM2.5 norm is exceeded. Computed on
    # daily means per station, with and without the internally-contradictory rows.
    d = df.dropna(subset=["pm2_5"]).copy()
    d["date"] = d["datetime"].dt.date
    bad = (masks["D1 pm2_5 > 1000 ug/m3 (implausible)"]
           | masks["D2 pm2_5 > pm10 (PM2.5 is a subset of PM10)"]
           | masks["D5 pm2_5 <= 0"]).fillna(False)
    clean = df.loc[~bad].dropna(subset=["pm2_5"]).copy()
    clean["date"] = clean["datetime"].dt.date

    def exceed_days(frame: pd.DataFrame, thr: float) -> int:
        daily = frame.groupby(["station_value_id", "date"])["pm2_5"].mean()
        return int((daily > thr).sum())

    kpi = {
        "station-days>60, as published": exceed_days(d, MAC_DAILY),
        "station-days>60, defect rows removed": exceed_days(clean, MAC_DAILY),
        "station-days>35, as published": exceed_days(d, MAC_ANNUAL),
        "station-days>35, defect rows removed": exceed_days(clean, MAC_ANNUAL),
    }

    # The decision-relevant comparison is not defects-vs-clean but published-vs-anchored:
    # the 24.5% under-read is what moves the KPI, and the KPI is computed on the raw series.
    FACTOR = 1.325
    city = d.groupby("date")["pm2_5"].mean()
    bias = {}
    for thr, lbl in ((MAC_DAILY, "60 (daily MAC)"), (MAC_ANNUAL, "35 (annual MAC)")):
        a, b = int((city > thr).sum()), int((city * FACTOR > thr).sum())
        bias[f"city-days>{lbl}"] = (a, b, b - a, round(b / a, 2) if a else float("nan"))
    n_city_days = int(city.size)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    res.to_csv(OUT, index=False)

    # ---- run log (reproducibility metadata) ------------------------------------------
    print("=" * 78)
    print("air.tashkent.uz archive - data-quality audit")
    print("=" * 78)
    print(f"input      : {SRC.relative_to(ROOT)}")
    print(f"sha256     : {sha256(SRC)}")
    print(f"rows       : {n_rows:,}   valid pm2_5: {n_valid:,}")
    print(f"period     : {df['datetime'].min()}  ->  {df['datetime'].max()}")
    print(f"stations   : {df['station_value_id'].nunique()}")
    print(f"python     : {platform.python_version()}  pandas {pd.__version__}  numpy {np.__version__}")
    print(f"command    : python3 scripts/pipeline/network_data_quality.py")
    print("-" * 78)
    print(res.to_string(index=False))
    print("-" * 78)
    print("Decision impact - PF-46 Annex 1 KPI (station-days above the national norm):")
    for k, v in kpi.items():
        print(f"  {k:<42} {v:>6}")
    print("-" * 78)
    print(f"Bias impact on the same KPI ({n_city_days} city-days in archive, factor x{FACTOR}):")
    for k, (a, b, dlt, r) in bias.items():
        print(f"  {k:<24} as published {a:>5}   anchored {b:>5}   +{dlt:<4} (x{r})")
    print("-" * 78)
    print(f"max pm2_5 observed : {pm.max():,.1f} ug/m3")
    print(f"max pm10  observed : {p10.max():,.1f} ug/m3")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

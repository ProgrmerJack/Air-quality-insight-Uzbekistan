"""What children breathe during the airing that СанПиН 0341-16 makes compulsory.

Survey before writing this file (CLAUDE.md rule 2): searched scripts/ for
`temperature`, `dt.hour`, `diurnal`, `school_hour`, `airing`, `проветрив`. Two scripts
define a school-hours window on OTHER series -- scripts/temporal/generate_canonical_ledger.py
(07:00-17:00, on the reference monitor) and scripts/temporal/b6_multicity_fetch_analyze.py
(08:00-15:00, multi-city) -- and scripts/pipeline/era5_inversion.py fetches ERA5 MONTHLY means
for 2022-2023 only. Nothing bands hours by the temperature the regulation actually keys on, and
nothing touches the municipal archive's own temperature channel. This is new.

THE REGULATION. СанПиН РУз 0341-16 (approved by the Chief State Sanitary Doctor, 22.12.2016):
  §6.6      classrooms are aired during breaks; before and after lessons, cross-airing.
  Table 4   prescribes cross-airing DURATION as a function of OUTDOOR TEMPERATURE ALONE:
              +10..+6 C  ->  4-10 min short break, 25-35 min long break
              +5..0   C  ->  3-7  min,             20-30 min
               0..-5  C  ->  2-5  min,             15-25 min
              -5..-10 C  ->  1-3  min,             10-15 min
              below -10  ->  1-1.5 min,             5-10 min
            (verified at nrm.uz doc 511380; values identical to the Russian source table,
             SanPiN 2.4.2.2821-10 Annex VI Table 2, checked at sudact.ru)
  §10.4     lessons start no earlier than 08:00; three shifts are not permitted.
  §10.9     a lesson is 45 minutes (40 in grade 1).
  §10.12    short breaks are at least 10 minutes; the long break, after lesson 2 or 3, is 20-30.
There is NO air-quality condition anywhere in Table 4.

QUESTIONS (all pre-specified before the data was touched; post-hoc items are labelled).
  A1  What is outdoor PM2.5 during school hours, banded by the Table 4 temperature band that
      determines how long the windows must be open?
  A2  On how many school-days does Table 4 prescribe a LONG airing (>=15 min) while the citywide
      daily mean PM2.5 is above the national daily norm of 60 ug/m3?
  A3  How many prescribed airing-minutes per school year fall on days above that norm?
  A4  How does school-hour PM2.5 in the coldest band compare with the mildest band?

TIME BASE. `datetime` in the archive is LOCAL time (UTC+5), not UTC. Evidence, internal to the
file and independent of any external source: mean temperature minimises at hour 06 and peaks at
hour 15, and PM2.5 peaks at 22:00-01:00. Under a UTC reading those would sit at 01, 10 and
17:00-20:00 respectively, which is not a physical diurnal cycle for Tashkent.

TEMPERATURE CHANNEL. 2,578 readings are exactly 0.0 C. They are not all placeholders and not all
genuine: October holds 751 of them against ONE genuine reading in [-0.5, +0.5], which is
impossible if 0.0 were a measurement; December holds 919 against 1,176 genuine near-zeros, where
some are plausible. Each 0.0 is therefore classified from its own neighbours at the same station
(genuine if the hours either side are within +-3 C of zero, placeholder otherwise) rather than
dropped wholesale, and the sensitivity arms report the answer under both extremes.

Run:  python3 scripts/pipeline/airing_window_exposure.py
Out:  data/pipeline/validation/airing_window_exposure.csv
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
OUT = ROOT / "data" / "pipeline" / "validation" / "airing_window_exposure.csv"
ERA5 = ROOT / "data" / "pipeline" / "cache" / "era5_tashkent_hourly_openmeteo.csv"

FACTOR = 1.325          # reference anchor, scripts/pipeline/bias_correction.py
MAC_DAILY = 60.0        # ug/m3, daily MAC, SanKvaN 0053-23
MAC_ANNUAL = 35.0       # ug/m3, annual MAC, SanKvaN 0053-23

SCHOOL_HOURS = range(8, 18)      # 08:00-17:59: shift 1 from 08:00 (§10.4), shift 2 to ~18:00
SHIFT1_HOURS = range(8, 14)      # first shift only
SCHOOL_MONTHS = {9, 10, 11, 12, 1, 2, 3, 4, 5}
ZERO_NEIGHBOUR_C = 3.0           # a 0.0 C reading is genuine if both neighbours are within this
MIN_HOURS_PER_DAY = 18           # a citywide daily mean needs 18 of 24 distinct hours (the 75 %
                                 # data-capture rule used throughout this work, after US EPA
                                 # EPA/600/R-20/280 §3.1.1)

# Table 4: (label, lower_exclusive, upper_inclusive, short_min, short_max, long_min, long_max)
BANDS = [
    ("above +10 (not in Table 4)",  10.0,  np.inf, np.nan, np.nan, np.nan, np.nan),
    ("+10 to +6",                    5.0,   10.0,   4.0,   10.0,  25.0,  35.0),
    ("+5 to 0",                      0.0,    5.0,   3.0,    7.0,  20.0,  30.0),
    ("0 to -5",                     -5.0,    0.0,   2.0,    5.0,  15.0,  25.0),
    ("-5 to -10",                  -10.0,   -5.0,   1.0,    3.0,  10.0,  15.0),
    ("below -10",                 -np.inf, -10.0,   1.0,    1.5,   5.0,  10.0),
]
BAND_ORDER = [b[0] for b in BANDS]
LONG_MID = {b[0]: (np.nan if np.isnan(b[5]) else (b[5] + b[6]) / 2) for b in BANDS}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def band_of(t: float) -> str:
    if not np.isfinite(t):
        return "unknown"
    for label, lo, hi, *_ in BANDS:
        if lo < t <= hi:
            return label
    return "unknown"


def classify_zeros(df: pd.DataFrame) -> pd.Series:
    """True where a 0.0 C reading is judged genuine from the same station's adjacent hours.

    Two conditions, and the second is the one that matters. A 0.0 is genuine only if
      (a) both adjacent hours lie within +-ZERO_NEIGHBOUR_C of zero -- a real 0 C sits inside a
          smooth temperature curve, a placeholder is a spike out of, say, 15 C; AND
      (b) it is ISOLATED, i.e. neither neighbour is itself exactly 0.0.
    Without (b) the test certifies its own failure mode: 89.9 % of the zero readings lie inside a
    run of two or more (the longest is 185 consecutive hours of "0.0 C"), and inside such a run
    every neighbour is 0.0 and therefore trivially within +-3 C. Only 260 of the zeros are
    isolated, and those are the only ones a neighbour test can adjudicate at all.
    """
    out = pd.Series(False, index=df.index)
    for _, g in df.groupby("station_value_id", sort=False):
        g = g.sort_values("datetime")
        t = g["temperature"]
        prev, nxt = t.shift(1), t.shift(-1)
        isolated = (prev != 0.0) & (nxt != 0.0)
        genuine = ((t == 0.0) & isolated
                   & prev.between(-ZERO_NEIGHBOUR_C, ZERO_NEIGHBOUR_C)
                   & nxt.between(-ZERO_NEIGHBOUR_C, ZERO_NEIGHBOUR_C))
        out.loc[g.index] = genuine.fillna(False)
    return out


def usable_temperature(df: pd.DataFrame, zeros: str) -> pd.Series:
    """zeros: 'classify' (default), 'drop' (all 0.0 are placeholders), 'keep' (all genuine)."""
    t = df["temperature"].copy()
    t[t > 50] = np.nan                      # D13: one reading of 80 C
    if zeros == "drop":
        t[t == 0.0] = np.nan
    elif zeros == "classify":
        t[(t == 0.0) & ~df["_zero_genuine"]] = np.nan
    return t


def school_mask(dt: pd.Series, weekdays: int) -> pd.Series:
    return dt.dt.month.isin(SCHOOL_MONTHS) & (dt.dt.dayofweek < weekdays)


def main() -> None:
    if not SRC.exists():
        sys.exit(f"missing input: {SRC}")

    df = pd.read_csv(SRC, dtype={"station_value_id": str}, parse_dates=["datetime"])
    df = df[df["pm2_5"].notna() & (df["pm2_5"] > 0)].copy()
    df["_zero_genuine"] = classify_zeros(df)
    n_zero = int((df["temperature"] == 0.0).sum())
    n_zero_genuine = int(df["_zero_genuine"].sum())

    df["temp_use"] = usable_temperature(df, "classify")
    df["band"] = df["temp_use"].map(band_of)
    df["pm_anchored"] = df["pm2_5"] * FACTOR
    df["hour"] = df["datetime"].dt.hour
    df["date"] = df["datetime"].dt.normalize()

    # ---- A1 (pre-specified): school-hour PM2.5 by Table 4 band ------------------------------
    sch = df[df["hour"].isin(SCHOOL_HOURS) & school_mask(df["datetime"], 6)
             & (df["band"] != "unknown")]
    rows = []
    for b in BAND_ORDER:
        g = sch[sch["band"] == b]
        if g.empty:
            continue
        rows.append({
            "analysis": "A1 school-hour PM2.5 by Table 4 band (PRE-SPECIFIED)",
            "band": b,
            "long_break_airing_min": LONG_MID[b],
            "n_station_hours": len(g),
            "mean_published": round(g["pm2_5"].mean(), 1),
            "mean_anchored": round(g["pm_anchored"].mean(), 1),
            "median_anchored": round(g["pm_anchored"].median(), 1),
            "p95_anchored": round(g["pm_anchored"].quantile(0.95), 1),
            "pct_hours_ge_60_published": round(100 * (g["pm2_5"] >= MAC_DAILY).mean(), 1),
            "pct_hours_ge_60_anchored": round(100 * (g["pm_anchored"] >= MAC_DAILY).mean(), 1),
        })
    a1 = pd.DataFrame(rows)

    # ---- city-day frame: citywide daily mean, and the band of that day's school hours -------
    daily = (df.groupby("date")
               .agg(pm_pub=("pm2_5", "mean"), pm_anc=("pm_anchored", "mean"),
                    n_station_hours=("pm2_5", "size"), n_hours=("hour", "nunique"))
               .reset_index())
    day_temp = (df[df["hour"].isin(SCHOOL_HOURS)]
                .groupby("date")["temp_use"].mean().rename("school_temp").reset_index())
    daily = daily.merge(day_temp, on="date", how="left")
    daily["band"] = daily["school_temp"].map(band_of)
    daily["long_min"] = daily["band"].map(LONG_MID)
    daily["is_school_day"] = school_mask(daily["date"], 6).values
    sd = daily[daily["is_school_day"] & (daily["band"] != "unknown") & (daily["n_hours"] >= MIN_HOURS_PER_DAY)]

    # ---- A2 (pre-specified): school-days with long airing prescribed above the norm ----------
    rows = []
    for b in BAND_ORDER:
        g = sd[sd["band"] == b]
        if g.empty:
            continue
        rows.append({
            "analysis": "A2 school-days by band and daily-norm status (PRE-SPECIFIED)",
            "band": b,
            "long_break_airing_min": LONG_MID[b],
            "n_school_days": len(g),
            "days_gt60_published": int((g["pm_pub"] > MAC_DAILY).sum()),
            "days_gt60_anchored": int((g["pm_anc"] > MAC_DAILY).sum()),
            "days_gt35_published": int((g["pm_pub"] > MAC_ANNUAL).sum()),
            "days_gt35_anchored": int((g["pm_anc"] > MAC_ANNUAL).sum()),
        })
    a2 = pd.DataFrame(rows)

    long_airing = sd[sd["long_min"] >= 15]           # bands +10..+6, +5..0, 0..-5
    n_long_over60_pub = int((long_airing["pm_pub"] > MAC_DAILY).sum())
    n_long_over60_anc = int((long_airing["pm_anc"] > MAC_DAILY).sum())

    # ---- A3 (pre-specified): prescribed airing-minutes falling on days above the norm --------
    sd = sd.copy()
    sd["school_year"] = np.where(sd["date"].dt.month >= 9,
                                 sd["date"].dt.year.astype(str) + "/" + (sd["date"].dt.year + 1).astype(str).str[-2:],
                                 (sd["date"].dt.year - 1).astype(str) + "/" + sd["date"].dt.year.astype(str).str[-2:])
    rows = []
    for sy, g in sd.groupby("school_year"):
        over = g[g["pm_anc"] > MAC_DAILY]
        rows.append({
            "analysis": "A3 prescribed long-break airing minutes per school year (PRE-SPECIFIED)",
            "school_year": sy,
            "n_school_days_with_data": len(g),
            "total_long_airing_min": int(g["long_min"].sum()),
            "long_airing_min_on_days_gt60_anchored": int(over["long_min"].sum()),
            "pct_of_airing_on_days_gt60_anchored": round(100 * over["long_min"].sum() / g["long_min"].sum(), 1)
                if g["long_min"].sum() else np.nan,
        })
    a3 = pd.DataFrame(rows)

    # ---- A4 (pre-specified): coldest vs mildest band ----------------------------------------
    def band_mean(b):
        g = sch[sch["band"] == b]
        return g["pm_anchored"].mean() if len(g) else np.nan
    mild, cold = band_mean("+10 to +6"), band_mean("below -10")
    ratio = cold / mild if np.isfinite(mild) and np.isfinite(cold) and mild else np.nan

    # ---- sensitivities ----------------------------------------------------------------------
    sens = []
    for label, zeros, weekdays in [("zeros classified by neighbours (primary)", "classify", 6),
                                   ("all 0.0 C dropped", "drop", 6),
                                   ("all 0.0 C kept as genuine", "keep", 6),
                                   ("Mon-Fri school week", "classify", 5)]:
        d2 = df.copy()
        d2["temp_use"] = usable_temperature(d2, zeros)
        d2["band"] = d2["temp_use"].map(band_of)
        s2 = d2[d2["hour"].isin(SCHOOL_HOURS) & school_mask(d2["datetime"], weekdays)
                & (d2["band"] != "unknown")]
        dd = (d2.groupby("date").agg(pm_anc=("pm_anchored", "mean"), n_hours=("hour", "nunique")).reset_index())
        dt2 = (d2[d2["hour"].isin(SCHOOL_HOURS)].groupby("date")["temp_use"].mean().rename("st").reset_index())
        dd = dd.merge(dt2, on="date", how="left")
        dd["band"] = dd["st"].map(band_of)
        dd["long_min"] = dd["band"].map(LONG_MID)
        dd = dd[school_mask(dd["date"], weekdays).values & (dd["n_hours"] >= MIN_HOURS_PER_DAY) & (dd["band"] != "unknown")]
        la = dd[dd["long_min"] >= 15]
        sens.append({
            "analysis": "SENSITIVITY",
            "arm": label,
            "n_school_hours_banded": len(s2),
            "mean_anchored_school_hours": round(s2["pm_anchored"].mean(), 1),
            "n_school_days_long_airing": len(la),
            "days_long_airing_gt60_anchored": int((la["pm_anc"] > MAC_DAILY).sum()),
        })
    sens = pd.DataFrame(sens)

    # ---- verification arm: repeat the banding on an INDEPENDENT temperature series -----------
    # ERA5 reanalysis 2 m temperature for Tashkent, Asia/Tashkent local time, retrieved from the
    # Open-Meteo archive API. It shares no instrument, no operator and no processing chain with
    # the municipal network, so it is a genuine external check on the band assignment -- which is
    # the weakest link in this analysis, because the network's own temperature channel is the
    # field that carries the 0.0 C placeholders.
    era_rows = []
    if ERA5.exists():
        era = pd.read_csv(ERA5, parse_dates=["datetime"]).rename(columns={"t2m_c": "t_era5"})
        d3 = df.merge(era, on="datetime", how="left")
        d3["band"] = d3["t_era5"].map(band_of)
        s3 = d3[d3["hour"].isin(SCHOOL_HOURS) & school_mask(d3["datetime"], 6) & (d3["band"] != "unknown")]
        dd3 = d3.groupby("date").agg(pm_anc=("pm_anchored", "mean"), n_hours=("hour", "nunique")).reset_index()
        t3 = d3[d3["hour"].isin(SCHOOL_HOURS)].groupby("date")["t_era5"].mean().rename("st").reset_index()
        dd3 = dd3.merge(t3, on="date", how="left")
        dd3["band"] = dd3["st"].map(band_of)
        dd3["long_min"] = dd3["band"].map(LONG_MID)
        dd3 = dd3[school_mask(dd3["date"], 6).values & (dd3["n_hours"] >= MIN_HOURS_PER_DAY) & (dd3["band"] != "unknown")]
        la3 = dd3[dd3["long_min"] >= 15]
        # agreement between the two temperature sources, hour by hour
        both = d3.dropna(subset=["temp_use", "t_era5"])
        agree = 100 * (both["temp_use"].map(band_of) == both["t_era5"].map(band_of)).mean()
        era_rows.append({
            "analysis": "VERIFICATION vs independent ERA5 temperature",
            "arm": "band assigned from ERA5 2 m temperature (Open-Meteo archive)",
            "n_school_hours_banded": len(s3),
            "mean_anchored_school_hours": round(s3["pm_anchored"].mean(), 1),
            "n_school_days_long_airing": len(la3),
            "days_long_airing_gt60_anchored": int((la3["pm_anc"] > MAC_DAILY).sum()),
            "band_agreement_pct_vs_network": round(agree, 1),
        })
        for b in BAND_ORDER:
            g = s3[s3["band"] == b]
            if g.empty:
                continue
            era_rows.append({
                "analysis": "VERIFICATION A1 recomputed on ERA5 temperature",
                "band": b,
                "long_break_airing_min": LONG_MID[b],
                "n_station_hours": len(g),
                "mean_published": round(g["pm2_5"].mean(), 1),
                "mean_anchored": round(g["pm_anchored"].mean(), 1),
                "pct_hours_ge_60_anchored": round(100 * (g["pm_anchored"] >= MAC_DAILY).mean(), 1),
            })
    era_df = pd.DataFrame(era_rows)

    # ---- A5 (POST-HOC): hour-of-day inside the first shift, heating season -------------------
    heat = df[df["datetime"].dt.month.isin({11, 12, 1, 2, 3}) & school_mask(df["datetime"], 6)]
    a5 = (heat[heat["hour"].isin(SHIFT1_HOURS)]
          .groupby("hour")
          .agg(n=("pm2_5", "size"), mean_published=("pm2_5", "mean"), mean_anchored=("pm_anchored", "mean"))
          .round(1).reset_index())
    a5.insert(0, "analysis", "A5 first-shift hour-of-day, heating season (POST-HOC)")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    pd.concat([a1, a2, a3, sens, era_df, a5], ignore_index=True).to_csv(OUT, index=False)

    # ---- report -----------------------------------------------------------------------------
    W = 96
    print("=" * W)
    print("PM2.5 during the airing that SanPiN 0341-16 Table 4 makes compulsory")
    print("=" * W)
    print(f"input     : {SRC.relative_to(ROOT)}")
    print(f"sha256    : {sha256(SRC)}")
    print(f"period    : {df['datetime'].min()} -> {df['datetime'].max()}  (LOCAL time, UTC+5)")
    print(f"valid rows: {len(df):,} station-hours with pm2_5 > 0")
    print(f"temp 0.0 C: {n_zero:,} readings, of which {n_zero_genuine:,} judged genuine by neighbours "
          f"({100*n_zero_genuine/n_zero:.0f}%)")
    print(f"python    : {platform.python_version()}  pandas {pd.__version__}  numpy {np.__version__}")
    print(f"command   : python3 scripts/pipeline/airing_window_exposure.py")
    print(f"factor    : x{FACTOR}   norms: {MAC_DAILY:.0f} daily / {MAC_ANNUAL:.0f} annual ug/m3")
    print("-" * W)
    print("A1  School-hour PM2.5 (08:00-17:59, Sep-May, Mon-Sat) by Table 4 temperature band")
    print(a1[["band", "long_break_airing_min", "n_station_hours", "mean_published",
              "mean_anchored", "p95_anchored", "pct_hours_ge_60_anchored"]].to_string(index=False))
    print("-" * W)
    print("A2  School-days by band, against the national daily norm (citywide 24-h mean)")
    print(a2[["band", "long_break_airing_min", "n_school_days", "days_gt60_published",
              "days_gt60_anchored", "days_gt35_anchored"]].to_string(index=False))
    print()
    print(f"    Days on which Table 4 prescribes >=15 min of long-break airing:")
    print(f"      total such school-days in archive        {len(long_airing):,}")
    print(f"      of which above 60 ug/m3, as published    {n_long_over60_pub:,}")
    print(f"      of which above 60 ug/m3, anchored        {n_long_over60_anc:,}")
    print("-" * W)
    print("A3  Prescribed long-break airing minutes, and how many fall on days above the norm")
    print(a3.drop(columns=["analysis"]).to_string(index=False))
    print("-" * W)
    print(f"A4  Coldest band (below -10) mean anchored school-hour PM2.5 : {cold:.1f} ug/m3")
    print(f"    Mildest band (+10 to +6) mean anchored school-hour PM2.5 : {mild:.1f} ug/m3")
    print(f"    ratio coldest/mildest                                    : {ratio:.2f}")
    print("-" * W)
    print("Sensitivity arms")
    print(sens.drop(columns=["analysis"]).to_string(index=False))
    print("-" * W)
    if not era_df.empty:
        print("VERIFICATION  same banding on independent ERA5 2 m temperature (Open-Meteo archive)")
        head = era_df[era_df["analysis"].str.startswith("VERIFICATION vs")]
        print(head[["n_school_hours_banded", "mean_anchored_school_hours", "n_school_days_long_airing",
                    "days_long_airing_gt60_anchored", "band_agreement_pct_vs_network"]].to_string(index=False))
        tail = era_df[era_df["analysis"].str.startswith("VERIFICATION A1")]
        print(tail[["band", "long_break_airing_min", "n_station_hours", "mean_anchored",
                    "pct_hours_ge_60_anchored"]].to_string(index=False))
    else:
        print("VERIFICATION  skipped: no ERA5 cache at " + str(ERA5.relative_to(ROOT)))
    print("-" * W)
    print("A5  First shift (08:00-13:59), heating season Nov-Mar (POST-HOC)")
    print(a5.drop(columns=["analysis"]).to_string(index=False))
    print("-" * W)
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

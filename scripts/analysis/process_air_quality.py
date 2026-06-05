"""
Air Quality Data Processing Pipeline
Processes PM2.5 data from U.S. Embassy Tashkent station

Author: Abduxoliq Ashuraliyev
ORCID: 0009-0003-5482-5526
Affiliation: Air Quality Research - Uzbekistan
"""

import pandas as pd
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent
# Use verified U.S. Embassy Station 8881 data (StateAir program)
INPUT_FILE = DATA_PATH / "us_embassy_2022_2023.csv"
WHO_FILE = DATA_PATH / "who_ambient_air_quality_database_version_2024_(v6.1).xlsx"


def load_openaq():
    """Load the verified U.S. Embassy PM2.5 measurements and return a clean DataFrame."""
    df = pd.read_csv(INPUT_FILE)
    df["datetime_local"] = pd.to_datetime(df["datetime_local"])
    # Data is already PM2.5 only from US Embassy station
    df["parameter"] = "pm25"
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value"])
    df["hour"] = df["datetime_local"].dt.hour
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["weekday"] = df["datetime_local"].dt.weekday
    df["is_weekend"] = df["weekday"] >= 5
    df["period"] = pd.cut(
        df["datetime_local"].dt.hour,
        bins=[-1, 5, 10, 15, 19, 24],
        labels=["overnight", "morning_commute", "school_hours", "afternoon", "late_evening"],
    )
    return df


def save_diurnal_profiles(df: pd.DataFrame):
    """Aggregate mean hourly concentrations split by weekday/weekend for Datawrapper."""
    group_cols = ["parameter", "hour", "is_weekend"]
    diurnal = (
        df.groupby(group_cols)["value"]
        .mean()
        .reset_index()
        .pivot_table(
            index=["parameter", "hour"],
            columns="is_weekend",
            values="value",
        )
        .rename(columns={False: "weekday_mean", True: "weekend_mean"})
        .reset_index()
    )
    diurnal["hour_label"] = diurnal["hour"].map(lambda h: f"{h:02d}:00")
    diurnal = diurnal[["parameter", "hour", "hour_label", "weekday_mean", "weekend_mean"]]
    diurnal.to_csv(DATA_PATH / "outputs" / "pm25_diurnal_profile.csv", index=False)


def save_school_hour_windows(df: pd.DataFrame):
    """Summaries for school-hour exposure and comparison windows."""
    windows = (
        df.groupby(["parameter", "period"])["value"]
        .agg(["mean", "median", "count"])
        .reset_index()
        .pivot_table(
            index="parameter",
            columns="period",
            values=["mean", "median", "count"],
        )
    )
    windows.columns = ["_".join(col).strip() for col in windows.columns.to_flat_index()]
    windows = windows.reset_index()
    windows.to_csv(DATA_PATH / "outputs" / "pm25_period_summary.csv", index=False)


def save_weekday_box(df: pd.DataFrame):
    """Daily mean concentrations split by weekday/weekend for box-plot style charts."""
    daily = (
        df.groupby(["parameter", "date", "is_weekend"])["value"]
        .mean()
        .reset_index()
        .rename(columns={"value": "daily_mean"})
    )
    daily.to_csv(DATA_PATH / "outputs" / "pm25_daily_means.csv", index=False)


def extract_who_context():
    """Filter WHO 2024 database for Uzbekistan city annual means."""
    who = pd.read_excel(WHO_FILE, sheet_name="Update 2024 (V6.1)")
    keep_cols = [
        "country_name",
        "city",
        "year",
        "pm25_concentration",
        "pm25_tempcov",
        "population",
        "who_ms",
    ]
    who = who[keep_cols]
    who = who[who["country_name"].str.contains("Uzbekistan", na=False)]
    who.to_csv(DATA_PATH / "outputs" / "who_pm25_context.csv", index=False)


def ensure_output_dir():
    out_dir = DATA_PATH / "outputs"
    out_dir.mkdir(exist_ok=True)


def main():
    ensure_output_dir()
    df = load_openaq()
    if df.empty:
        raise SystemExit("OpenAQ dataset contains no PM2.5 or NO2 records.")
    save_diurnal_profiles(df[df["parameter"] == "pm25"])
    save_school_hour_windows(df[df["parameter"] == "pm25"])
    save_weekday_box(df[df["parameter"] == "pm25"])
    extract_who_context()


if __name__ == "__main__":
    main()

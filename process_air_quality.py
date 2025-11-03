import pandas as pd
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent
INPUT_FILE = DATA_PATH / "openaq_location_4902926_measurments.csv"
WHO_FILE = DATA_PATH / "who_ambient_air_quality_database_version_2024_(v6.1).xlsx"


def load_openaq():
    """Load the harmonized OpenAQ measurements and return a clean DataFrame."""
    df = pd.read_csv(INPUT_FILE)
    df["datetimeLocal"] = pd.to_datetime(df["datetimeLocal"])
    df = df[df["parameter"].str.lower().isin(["pm25", "no2"])]
    df["unit"] = df["unit"].str.replace("�", "u", regex=False)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value"])
    df["hour"] = df["datetimeLocal"].dt.hour
    df["date"] = df["datetimeLocal"].dt.date
    df["weekday"] = df["datetimeLocal"].dt.weekday
    df["is_weekend"] = df["weekday"] >= 5
    df["period"] = pd.cut(
        df["datetimeLocal"].dt.hour,
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

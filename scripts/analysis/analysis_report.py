"""
Advanced Air Quality Analysis Report Generator
Generates comprehensive statistical analysis, health impact assessment, and policy recommendations

Author: Abduxoliq Ashuraliyev
ORCID: 0009-0003-5482-5526
Affiliation: Air Quality Research - Uzbekistan
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

DATA_PATH = Path(__file__).resolve().parent
# Use verified U.S. Embassy Station 8881 data (StateAir program)
INPUT_FILE = DATA_PATH / "us_embassy_2022_2023.csv"
OUTPUT_DIR = DATA_PATH / "outputs"


def load_processed_data():
    """Load and prepare the verified U.S. Embassy PM2.5 dataset with additional analytics"""
    df = pd.read_csv(INPUT_FILE)
    df["datetimeLocal"] = pd.to_datetime(df["datetime_local"])
    # Data is already PM2.5 only from US Embassy station
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value"])

    # Enhanced time features
    df["hour"] = df["datetimeLocal"].dt.hour
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["weekday"] = df["datetimeLocal"].dt.weekday
    df["is_weekend"] = df["weekday"] >= 5
    df["month"] = df["datetimeLocal"].dt.month
    # Use season from data if available, otherwise derive from month
    if "season" not in df.columns:
        df["season"] = df["month"].map({
            12: "Winter", 1: "Winter", 2: "Winter",
            3: "Spring", 4: "Spring", 5: "Spring",
            6: "Summer", 7: "Summer", 8: "Summer",
            9: "Fall", 10: "Fall", 11: "Fall"
        })

    return df


def calculate_who_exceedances(df: pd.DataFrame) -> dict:
    """Calculate exceedances of WHO guidelines"""
    WHO_24H = 15  # µg/m³ (2021 guideline)
    WHO_ANNUAL = 5  # µg/m³ (2021 guideline)
    
    daily_means = df.groupby("date")["value"].mean()
    
    exceedances = {
        "total_days": len(daily_means),
        "days_exceeding_who_24h": (daily_means > WHO_24H).sum(),
        "percent_exceeding_who_24h": (daily_means > WHO_24H).mean() * 100,
        "period_mean": df["value"].mean(),
        "exceeds_who_annual": df["value"].mean() > WHO_ANNUAL,
        "who_annual_guideline": WHO_ANNUAL,
        "who_24h_guideline": WHO_24H,
        "max_24h_mean": daily_means.max(),
        "median_24h_mean": daily_means.median(),
    }
    
    return exceedances


def health_impact_assessment(df: pd.DataFrame) -> dict:
    """Estimate health impacts based on PM2.5 exposure"""
    
    # Population at risk (example: students in nearby schools)
    STUDENT_POPULATION = 5000  # Estimate
    
    # WHO concentration-response relationships (simplified)
    # Per 10 µg/m³ increase above baseline
    
    mean_pm25 = df["value"].mean()
    baseline_pm25 = 5  # WHO guideline
    excess_pm25 = max(0, mean_pm25 - baseline_pm25)
    
    # Relative risk estimates (literature-based, simplified)
    # RR per 10 µg/m³ increase
    RR_respiratory = 1.08  # 8% increase in respiratory illness
    RR_absenteeism = 1.05  # 5% increase in school absence
    
    increments = excess_pm25 / 10
    
    impact = {
        "mean_exposure_ugm3": round(mean_pm25, 2),
        "excess_exposure_ugm3": round(excess_pm25, 2),
        "student_population_estimate": STUDENT_POPULATION,
        "estimated_additional_respiratory_cases_pct": round((RR_respiratory ** increments - 1) * 100, 2),
        "estimated_increased_absenteeism_pct": round((RR_absenteeism ** increments - 1) * 100, 2),
        "note": "Estimates are indicative and based on simplified concentration-response models"
    }
    
    return impact


def temporal_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Detailed temporal pattern analysis"""
    
    temporal = df.groupby(["hour", "is_weekend"])["value"].agg([
        ("mean", "mean"),
        ("median", "median"),
        ("p25", lambda x: x.quantile(0.25)),
        ("p75", lambda x: x.quantile(0.75)),
        ("p95", lambda x: x.quantile(0.95)),
        ("count", "count")
    ]).reset_index()
    
    temporal["day_type"] = temporal["is_weekend"].map({True: "Weekend", False: "Weekday"})
    temporal = temporal.drop("is_weekend", axis=1)
    
    return temporal


def seasonal_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Seasonal variation analysis"""
    
    seasonal = df.groupby("season")["value"].agg([
        ("mean", "mean"),
        ("median", "median"),
        ("std", "std"),
        ("min", "min"),
        ("max", "max"),
        ("count", "count")
    ]).reset_index()
    
    seasonal = seasonal.sort_values("mean", ascending=False)
    
    return seasonal


def school_exposure_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Detailed school hours exposure analysis"""
    
    # Define critical time windows
    school_hours = (df["hour"] >= 8) & (df["hour"] <= 15)
    commute_hours = (df["hour"] >= 7) & (df["hour"] <= 9) | (df["hour"] >= 14) & (df["hour"] <= 16)
    after_school = (df["hour"] >= 16) & (df["hour"] <= 19)
    
    df_school = df[school_hours & ~df["is_weekend"]]
    df_commute = df[commute_hours & ~df["is_weekend"]]
    df_after = df[after_school & ~df["is_weekend"]]
    
    analysis = pd.DataFrame([
        {
            "period": "School Hours (08:00-15:00)",
            "mean_pm25": df_school["value"].mean(),
            "median_pm25": df_school["value"].median(),
            "max_pm25": df_school["value"].max(),
            "hours_above_who_24h": (df_school["value"] > 15).sum(),
            "percent_above_who": (df_school["value"] > 15).mean() * 100
        },
        {
            "period": "Commute Times",
            "mean_pm25": df_commute["value"].mean(),
            "median_pm25": df_commute["value"].median(),
            "max_pm25": df_commute["value"].max(),
            "hours_above_who_24h": (df_commute["value"] > 15).sum(),
            "percent_above_who": (df_commute["value"] > 15).mean() * 100
        },
        {
            "period": "After School (16:00-19:00)",
            "mean_pm25": df_after["value"].mean(),
            "median_pm25": df_after["value"].median(),
            "max_pm25": df_after["value"].max(),
            "hours_above_who_24h": (df_after["value"] > 15).sum(),
            "percent_above_who": (df_after["value"] > 15).mean() * 100
        }
    ])
    
    return analysis


def generate_policy_recommendations(exceedances: dict, health_impact: dict, school_exposure: pd.DataFrame) -> list:
    """Generate evidence-based policy recommendations"""
    
    recommendations = []
    
    # Critical exceedances
    if exceedances["percent_exceeding_who_24h"] > 75:
        recommendations.append({
            "priority": "CRITICAL",
            "area": "Air Quality Management",
            "recommendation": "Implement emergency air quality action plan - over 75% of days exceed WHO guidelines",
            "evidence": f"{exceedances['percent_exceeding_who_24h']:.1f}% of days exceed WHO 24-hour guideline"
        })
    
    # School protection
    school_mean = school_exposure[school_exposure["period"] == "School Hours (08:00-15:00)"]["mean_pm25"].values[0]
    if school_mean > 15:
        recommendations.append({
            "priority": "HIGH",
            "area": "School Health",
            "recommendation": "Install air filtration systems (HEPA or Corsi-Rosenthal boxes) in all classrooms",
            "evidence": f"School hours mean PM2.5 = {school_mean:.1f} µg/m³ (WHO guideline = 15 µg/m³)"
        })
    
    # Traffic management
    commute_mean = school_exposure[school_exposure["period"] == "Commute Times"]["mean_pm25"].values[0]
    if commute_mean > 20:
        recommendations.append({
            "priority": "HIGH",
            "area": "Traffic Management",
            "recommendation": "Create vehicle-free zones within 250m of schools during peak hours (07:00-09:00, 14:00-16:00)",
            "evidence": f"Commute time mean PM2.5 = {commute_mean:.1f} µg/m³"
        })
    
    # Heating/cooking sources
    if health_impact["excess_exposure_ugm3"] > 10:
        recommendations.append({
            "priority": "MEDIUM",
            "area": "Emission Sources",
            "recommendation": "Accelerate transition from solid fuel to clean energy for residential heating and cooking",
            "evidence": f"Excess exposure = {health_impact['excess_exposure_ugm3']:.1f} µg/m³ above WHO guideline"
        })
    
    # Monitoring expansion
    recommendations.append({
        "priority": "MEDIUM",
        "area": "Data Infrastructure",
        "recommendation": "Expand air quality monitoring network to capture spatial variability across city",
        "evidence": "Current analysis based on single monitoring location"
    })
    
    # Public awareness
    if exceedances["percent_exceeding_who_24h"] > 50:
        recommendations.append({
            "priority": "MEDIUM",
            "area": "Public Health Communication",
            "recommendation": "Establish real-time air quality alert system for schools and vulnerable populations",
            "evidence": f"Frequent guideline exceedances ({exceedances['percent_exceeding_who_24h']:.1f}% of days)"
        })
    
    return recommendations


def _print_header():
    """Print report header"""
    print("=" * 80)
    print("AIR QUALITY INSIGHT - UZBEKISTAN")
    print("Comprehensive Analysis Report")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()


def _print_who_exceedances(exceedances: dict):
    """Print WHO guideline exceedance statistics"""
    print("-" * 80)
    print("WHO GUIDELINE EXCEEDANCES")
    print("-" * 80)
    print(f"Period mean PM2.5: {exceedances['period_mean']:.2f} µg/m³")
    print(f"WHO Annual Guideline: {exceedances['who_annual_guideline']} µg/m³")
    print(f"WHO 24-hour Guideline: {exceedances['who_24h_guideline']} µg/m³")
    print(f"Days analyzed: {exceedances['total_days']}")
    print(f"Days exceeding WHO 24-hour guideline: {exceedances['days_exceeding_who_24h']} "
          f"({exceedances['percent_exceeding_who_24h']:.1f}%)")
    print(f"Maximum 24-hour mean: {exceedances['max_24h_mean']:.2f} µg/m³")
    print(f"Median 24-hour mean: {exceedances['median_24h_mean']:.2f} µg/m³")
    print()


def _print_health_impact(health_impact: dict):
    """Print health impact assessment"""
    print("-" * 80)
    print("HEALTH IMPACT ASSESSMENT")
    print("-" * 80)
    print(f"Mean PM2.5 exposure: {health_impact['mean_exposure_ugm3']} µg/m³")
    print(f"Excess above WHO guideline: {health_impact['excess_exposure_ugm3']} µg/m³")
    print(f"Estimated student population: {health_impact['student_population_estimate']:,}")
    print(f"Estimated additional respiratory cases: "
          f"{health_impact['estimated_additional_respiratory_cases_pct']}%")
    print(f"Estimated increased absenteeism: {health_impact['estimated_increased_absenteeism_pct']}%")
    print(f"Note: {health_impact['note']}")
    print()


def _print_recommendations(recommendations: list):
    """Print policy recommendations"""
    print("-" * 80)
    print("POLICY RECOMMENDATIONS")
    print("-" * 80)
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. [{rec['priority']}] {rec['area']}")
        print(f"   Recommendation: {rec['recommendation']}")
        print(f"   Evidence: {rec['evidence']}")


def generate_comprehensive_report():
    """Generate complete analysis report"""
    OUTPUT_DIR.mkdir(exist_ok=True)
    _print_header()

    # Load data
    print("Loading and processing data...")
    df = load_processed_data()
    date_range = f"{df['datetimeLocal'].min().date()} to {df['datetimeLocal'].max().date()}"
    print(f"Analysis period: {date_range}")
    print(f"Total measurements: {len(df):,}")
    print()

    # WHO Exceedances
    exceedances = calculate_who_exceedances(df)
    _print_who_exceedances(exceedances)

    # Health Impact
    health_impact = health_impact_assessment(df)
    _print_health_impact(health_impact)

    # Temporal Analysis
    print("-" * 80)
    print("TEMPORAL PATTERNS")
    print("-" * 80)
    temporal = temporal_analysis(df)
    temporal_file = OUTPUT_DIR / "detailed_temporal_analysis.csv"
    temporal.to_csv(temporal_file, index=False)
    print(f"Detailed hourly patterns saved to: {temporal_file.name}")
    print()

    # Seasonal Analysis
    print("-" * 80)
    print("SEASONAL VARIATION")
    print("-" * 80)
    seasonal = seasonal_analysis(df)
    print(seasonal.to_string(index=False))
    seasonal_file = OUTPUT_DIR / "seasonal_analysis.csv"
    seasonal.to_csv(seasonal_file, index=False)
    print(f"\nSaved to: {seasonal_file.name}")
    print()

    # School Exposure
    print("-" * 80)
    print("SCHOOL EXPOSURE ANALYSIS")
    print("-" * 80)
    school_exposure = school_exposure_analysis(df)
    print(school_exposure.to_string(index=False))
    school_file = OUTPUT_DIR / "school_exposure_detailed.csv"
    school_exposure.to_csv(school_file, index=False)
    print(f"\nSaved to: {school_file.name}")
    print()

    # Policy Recommendations
    recommendations = generate_policy_recommendations(exceedances, health_impact, school_exposure)
    _print_recommendations(recommendations)
    rec_df = pd.DataFrame(recommendations)
    rec_file = OUTPUT_DIR / "policy_recommendations.csv"
    rec_df.to_csv(rec_file, index=False)
    print(f"\nRecommendations saved to: {rec_file.name}")
    print()

    # Summary Statistics
    summary_stats = {
        "analysis_date": datetime.now().strftime('%Y-%m-%d'),
        "period_start": str(df['datetimeLocal'].min().date()),
        "period_end": str(df['datetimeLocal'].max().date()),
        "total_measurements": len(df),
        "mean_pm25_ugm3": round(df["value"].mean(), 2),
        "median_pm25_ugm3": round(df["value"].median(), 2),
        "max_pm25_ugm3": round(df["value"].max(), 2),
        "days_analyzed": exceedances["total_days"],
        "days_exceeding_who_24h": exceedances["days_exceeding_who_24h"],
        "percent_exceeding_who": round(exceedances["percent_exceeding_who_24h"], 1),
        "school_hours_mean_pm25": round(
            school_exposure[school_exposure["period"] == "School Hours (08:00-15:00)"]
            ["mean_pm25"].values[0], 2
        ),
        "recommendations_count": len(recommendations)
    }
    summary_df = pd.DataFrame([summary_stats])
    summary_file = OUTPUT_DIR / "analysis_summary.csv"
    summary_df.to_csv(summary_file, index=False)

    print("=" * 80)
    print(f"ANALYSIS COMPLETE - All outputs saved to: {OUTPUT_DIR}")
    print("=" * 80)


if __name__ == "__main__":
    generate_comprehensive_report()

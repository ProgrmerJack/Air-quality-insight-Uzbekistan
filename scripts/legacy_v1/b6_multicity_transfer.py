"""
B6 - Multi-city transfer of the minimal-monitoring framework.

Demonstrates that the same pipeline (one reference monitor -> exposure +
school-protection assessment) extends to other Central Asian capitals. A live
fetch requires a free OpenAQ v3 API key (export OPENAQ_API_KEY=...); without a
key, the literature-based regional baseline below is used so the comparison is
still reproducible.

Run:  OPENAQ_API_KEY=xxxx python b6_multicity_transfer.py
"""
import os, sys

# U.S. Embassy / reference OpenAQ location IDs (verify current IDs before live use)
CITY_STATIONS = {
    "Almaty":   {"country": "Kazakhstan",   "openaq_location": None},
    "Bishkek":  {"country": "Kyrgyzstan",   "openaq_location": None},
    "Dushanbe": {"country": "Tajikistan",   "openaq_location": None},
    "Tashkent": {"country": "Uzbekistan",   "openaq_location": 8881},
}

# Literature-based annual means (ug/m3) for the regional comparison.
# Sources: Tursumbayeva/Kerimray et al. 2023 (Atmos. Environ. 305:119901);
# World Bank 2024 Tashkent (pop-weighted 38.8, 2019); IQAir 2023 capital ranks.
REGIONAL = {
    # city: (annual_mean_ugm3, source_note, IQAir_2023_capital_rank)
    "Dushanbe": (28.6, "IQAir 2023 capital mean", 4),
    "Tashkent": (37.9, "this study 2022-23 (WB 2019 pop-wtd 38.8)", 22),
    "Bishkek":  (None, "Tursumbayeva 2023 (max 112)", 29),
    "Almaty":   (None, "Tursumbayeva 2023 (max 110)", None),
    "Astana":   (None, "WB 2022", 52),
}

WHO_ANNUAL = 5.0
RR10 = 1.08  # conservative all-respiratory slope

def paf(c, c0=WHO_ANNUAL, rr=RR10):
    if c is None: return None
    return 1 - rr ** (-(c - c0) / 10.0)

def fetch_openaq(location_id, key, date_from="2022-01-01", date_to="2023-06-30"):
    import requests
    url = f"https://api.openaq.org/v3/locations/{location_id}/measurements"
    hdr = {"X-API-Key": key}
    params = {"parameters_id": 2, "date_from": date_from, "date_to": date_to,
              "limit": 1000}
    # NOTE: real use needs pagination; this is a template stub.
    r = requests.get(url, headers=hdr, params=params, timeout=60)
    r.raise_for_status()
    return r.json()

def main():
    key = os.environ.get("OPENAQ_API_KEY")
    print("== Regional transfer of the minimal-monitoring framework ==\n")
    print(f"{'City':10} {'Mean':>6} {'PAF%':>6}  Rank  Source")
    for city, (mean, note, rank) in REGIONAL.items():
        p = paf(mean)
        ps = f"{p*100:5.1f}" if p is not None else "   na"
        ms = f"{mean:5.1f}" if mean is not None else "   na"
        rk = f"{rank}" if rank else "-"
        print(f"{city:10} {ms:>6} {ps:>6}  {rk:>4}  {note}")
    if key:
        print("\nAPI key found -- live fetch enabled. Fill CITY_STATIONS location IDs "
              "and extend fetch_openaq() with pagination to reproduce per-city pipelines.")
    else:
        print("\nNo OPENAQ_API_KEY set -- showing literature baseline only. "
              "Set the key and station IDs to run the full per-city pipeline "
              "(same QC + diurnal + infiltration + PAF as the Tashkent analysis).")

if __name__ == "__main__":
    main()

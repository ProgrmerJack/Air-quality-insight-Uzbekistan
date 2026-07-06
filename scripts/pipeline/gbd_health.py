"""
Step 5 (health) -- attributable childhood (<20) asthma using REAL GBD 2023 (2021) baselines.

Avoids the over-extrapolation the reviewer flagged: we do NOT compound a steep per-ug/m3 asthma
RR across a ~30 ug/m3 range. We apply the CONSERVATIVE all-respiratory slope (RR 1.08 per 10
ug/m3, the manuscript's anchor) to the GBD asthma-incidence baseline, and note that asthma-specific
functions (Anenberg 2018) imply a larger burden (cited, not computed here).
Output: data/pipeline/health_asthma_attributable.csv
"""
import os, csv, math
from paths import pipeline_path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GBD = pipeline_path("IHME-GBD_2023_DATA-05fce0b4-1.csv")
OUT = pipeline_path("health_asthma_attributable.csv")

rows = list(csv.DictReader(open(GBD, encoding="utf-8")))
def get(loc, cause, measure, metric):
    for r in rows:
        if (r["location_name"] == loc and r["cause_name"] == cause
                and r["measure_name"] == measure and r["metric_name"] == metric):
            return float(r["val"])
    return None

CITY = {  # city -> (country, embassy-FEM annual PM2.5)
    "Tashkent": ("Uzbekistan", 37.9), "Almaty": ("Kazakhstan", 34.2),
    "Astana": ("Kazakhstan", 18.5), "Bishkek": ("Kyrgyzstan", 35.6),
    "Dushanbe": ("Tajikistan", 53.3), "Ashgabat": ("Turkmenistan", 22.8),
}
RR, C0 = 1.08, 5.0
def paf(c): return 1 - RR ** (-(c - C0) / 10.0)

print("locations in GBD file:", sorted(set(r["location_name"] for r in rows)))
out = []
for city, (ctry, pm) in CITY.items():
    inc = get(ctry, "Asthma", "Incidence", "Number")
    prev = get(ctry, "Asthma", "Prevalence", "Number")
    if inc is None:
        print(f"  {city}: no GBD asthma incidence for {ctry}"); continue
    f = paf(pm)
    out.append({"city": city, "country": ctry, "pm25": pm,
                "asthma_incidence_u20": round(inc), "asthma_prevalence_u20": round(prev) if prev else "",
                "paf_conservative_pct": round(100 * f, 1),
                "attributable_incident_cases": round(inc * f)})
    print(f"  {city:9} ({ctry:12}) PM2.5={pm:>5} | asthma incidence <20 = {inc:>9,.0f} | "
          f"conservative PAF {100*f:4.1f}% -> attributable {inc*f:>8,.0f} cases/yr")

with open(OUT, "w", newline="", encoding="utf-8") as fo:
    w = csv.DictWriter(fo, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
print("saved", OUT)
print("NOTE: conservative all-respiratory slope; asthma-specific ERFs (Anenberg 2018) imply higher.")

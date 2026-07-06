"""
Health sensitivity (closes the 'Achakulwisut/GEMM' and 'cost-per-DALY' gaps as LABELLED analyses).
Uses real GBD 2023(2021) asthma Incidence + YLDs for Uzbekistan.

ERF panel (Tashkent, C=37.9, C0=5):
  - conservative all-respiratory  RR 1.08/10           (manuscript anchor)
  - Anenberg 2018 paediatric asthma RR 1.34-1.93/10    (capped at derivation ceiling 34 ug/m3)
  - Achakulwisut 2019              RR 1.03/ug           (capped)
GEMM (Burnett 2018) is an ADULT non-accidental-mortality function and is NOT applied to the
paediatric-asthma endpoint; noted for transparency.

Cost-per-DALY: GBD asthma YLDs (Uzbekistan, <20) x Tashkent child share -> attributable YLDs;
cost per *attributable* DALY = annual cost / attributable YLDs (upper-bound effectiveness).
"""
import os, csv, math
from paths import pipeline_path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
rows = list(csv.DictReader(open(pipeline_path("IHME-GBD_2023_DATA-05fce0b4-1.csv"), encoding="utf-8")))
def g(loc, meas, metric, cause="Asthma"):
    for r in rows:
        if r["location_name"]==loc and r["measure_name"].startswith(meas) and r["metric_name"]==metric and r["cause_name"]==cause:
            return float(r["val"])
C, C0, CAP = 37.9, 5.0, 34.0
inc = min(C, CAP) - C0
panel = {
    "conservative all-respiratory (1.08/10)": 1 - 1.08 ** (-(C-C0)/10),
    "Anenberg low (1.34/10, capped)":         1 - 1.34 ** (-inc/10),
    "Anenberg high (1.93/10, capped)":        1 - 1.93 ** (-inc/10),
    "Achakulwisut (1.03/ug, capped)":         1 - math.exp(-math.log(1.03)*inc),
}
print("=== PAF panel (Tashkent childhood asthma) ===")
for k, v in panel.items(): print(f"  {k:42} {100*v:5.1f}%")
print("  GEMM: adult non-accidental mortality function; not applied to paediatric asthma (noted).")

ylds = g("Uzbekistan", "YLDs", "Number")
inc_n = g("Uzbekistan", "Incidence", "Number")
TASH_SHARE = 0.082   # Tashkent ~2.6M of ~31.6M Uzbekistan (population proxy for child share)
paf_cons = panel["conservative all-respiratory (1.08/10)"]
att_ylds_uz = paf_cons * ylds
att_ylds_tash = att_ylds_uz * TASH_SHARE
COST = 15e6  # citywide HEPA $/yr (Tashkent)
print(f"\n=== Cost-per-DALY (Tashkent, conservative PAF {100*paf_cons:.1f}%) ===")
print(f"  GBD Uzbekistan asthma <20: incidence {inc_n:,.0f}/yr, YLDs {ylds:,.0f}/yr")
print(f"  attributable YLDs: Uzbekistan {att_ylds_uz:,.0f}; Tashkent (~{TASH_SHARE:.0%}) {att_ylds_tash:,.0f}")
print(f"  cost per *attributable* DALY (upper-bound effectiveness) = ${COST/att_ylds_tash:,.0f}/DALY")
print(f"  (realistic cost/DALY is higher: classroom filtration averts only part of total exposure;")
print(f"   asthma-specific ERFs would raise PAF and LOWER cost/DALY. Report as a labelled range.)")

with open(pipeline_path("health_sensitivity.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["erf", "tashkent_paf_pct"])
    for k, v in panel.items(): w.writerow([k, round(100*v, 1)])
    w.writerow([]); w.writerow(["uzb_asthma_ylds_u20", round(ylds)])
    w.writerow(["tashkent_attributable_ylds", round(att_ylds_tash)])
    w.writerow(["cost_per_attributable_daly_usd", round(COST/att_ylds_tash)])
print("saved data/pipeline/health_sensitivity.csv")

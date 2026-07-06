"""
Global applicability of the method (honest, tiered, data-grounded). Figure 1.

Binding layers (all others -- ACAG PM2.5, WSF building age, WorldPop child density, OSM roads,
GIGA+OSM schools -- are global):
  Equity layer  : Meta Relative Wealth Index, published for low- and middle-income countries (LMICs).
  Reference anchor : >= 1 reference-grade PM2.5 monitor (OpenAQ isMonitor=True; anchor-agnostic --
                    embassy, national reference station, or one calibrated unit). REAL coverage from
                    openaq_anchor_coverage.py.
Tiers (country level):
  Immediate          : LMIC with an existing reference anchor (all four binding layers present now).
  Near-term          : LMIC with no current anchor -> deploy one reference unit.
  Adaptable          : high-income -> substitute a wealth proxy for RWI (anchor already present).
Output: data/pipeline/global_applicability.csv + Research_paper/.../fig_global_applicability.png
"""
import os, csv, sys, io, requests
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import geopandas as gpd
from paths import pipeline_path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "data", "pipeline")
FIG = os.path.join(ROOT, "Research_paper", "npj_urban_sustainability")
H = {"User-Agent": "npjUS-research/1.0"}

# --- World Bank income + ISO2->ISO3 map ---
wb = requests.get("https://api.worldbank.org/v2/country?format=json&per_page=400", timeout=90, headers=H).json()[1]
income = {}; iso2to3 = {}
for c in wb:
    if c["region"]["id"] == "NA":  # skip aggregates
        continue
    income[c["id"]] = c["incomeLevel"]["id"]
    iso2to3[c["iso2Code"]] = c["id"]
LMIC = {"UMC", "LMC", "LIC"}

# --- OpenAQ reference-anchor coverage (iso2 -> iso3) ---
anchor = {}; cities = {}; active = {}
for r in csv.DictReader(open(pipeline_path("openaq_reference_coverage.csv"), encoding="utf-8")):
    iso3 = iso2to3.get(r["country_code"])
    if iso3:
        anchor[iso3] = int(r["n_monitors"]); cities[iso3] = int(r["n_cities"]); active[iso3] = int(r["n_active_2023plus"])

def tier(iso):
    g = income.get(iso)
    if g is None: return 0
    has = anchor.get(iso, 0) > 0
    if g in LMIC: return 3 if has else 2   # immediate / near-term
    return 1 if g == "HIC" else 0          # high income -> adaptable; else unclassified

# counts
imm = [i for i in income if tier(i) == 3]; near = [i for i in income if tier(i) == 2]; adapt = [i for i in income if tier(i) == 1]
imm_cities = sum(cities.get(i, 0) for i in imm)
print(f"Economies: {len(income)} | LMIC {sum(1 for v in income.values() if v in LMIC)} | HIC {sum(1 for v in income.values() if v=='HIC')}")
print(f"TIER immediate (LMIC + anchor): {len(imm)} countries, ~{imm_cities} cities with a reference anchor")
print(f"TIER near-term (LMIC, deploy anchor): {len(near)} countries")
print(f"TIER adaptable (high income): {len(adapt)} countries")
print(f"Total countries with a reference anchor: {sum(1 for i in income if anchor.get(i,0)>0)}")

with open(pipeline_path("global_applicability.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["iso3", "income_group", "n_ref_monitors", "n_anchor_cities", "tier"])
    nм = {3: "immediate", 2: "near_term_deploy_anchor", 1: "adaptable_high_income", 0: "unclassified"}
    for iso, g in sorted(income.items()):
        w.writerow([iso, g, anchor.get(iso, 0), cities.get(iso, 0), nм[tier(iso)]])

# --- map ---
url = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"
world = gpd.read_file(io.BytesIO(requests.get(url, timeout=120, headers=H).content))
isocol = "ISO_A3_EH" if "ISO_A3_EH" in world.columns else "ISO_A3"
world["tier"] = world[isocol].map(tier)
caps = {"Tashkent": (69.25, 41.31), "Almaty": (76.89, 43.24), "Astana": (71.45, 51.17),
        "Bishkek": (74.61, 42.87), "Dushanbe": (68.79, 38.56), "Ashgabat": (58.33, 37.96)}
transfer = {"Accra": (-0.19, 5.60), "Kathmandu": (85.32, 27.70), "Lima": (-77.0, -12.05)}
fig, ax = plt.subplots(figsize=(13, 6.6))
colors = {0: "#ededed", 1: "#9ecae1", 2: "#fdd49e", 3: "#e34a33"}
for t, c in colors.items():
    sub = world[world["tier"] == t]
    if len(sub): sub.plot(ax=ax, color=c, edgecolor="white", linewidth=0.2)
for name, (lo, la) in caps.items():
    ax.plot(lo, la, marker="*", ms=15, color="black", mec="white", mew=0.6)
for name, (lo, la) in transfer.items():
    ax.plot(lo, la, marker="D", ms=9, color="#08519c", mec="white", mew=0.6)
ax.set_xlim(-170, 185); ax.set_ylim(-58, 84); ax.axis("off")
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
leg = [Patch(facecolor="#e34a33", label=f"Immediate: low/middle-income with a reference anchor (n={len(imm)})"),
       Patch(facecolor="#fdd49e", label=f"Near-term: low/middle-income, deploy one anchor (n={len(near)})"),
       Patch(facecolor="#9ecae1", label=f"Adaptable: high-income, substitute wealth layer (n={len(adapt)})"),
       Line2D([0],[0], marker="*", color="w", markerfacecolor="black", markersize=13, label="Central Asian demonstration (6 capitals)"),
       Line2D([0],[0], marker="D", color="w", markerfacecolor="#08519c", markersize=9, label="Out-of-region transfer (Accra, Kathmandu, Lima)")]
ax.legend(handles=leg, loc="lower left", fontsize=8.5, frameon=False)
ax.set_title("Global applicability of the open school-air-pollution decision method\n"
             "(hazard, school and child layers global; equity layer immediate across all low/middle-income countries; one reference anchor required)",
             fontsize=11)
plt.tight_layout(); plt.savefig(os.path.join(FIG, "fig_global_applicability.png"), dpi=200); plt.close()
print("saved fig_global_applicability.png and global_applicability.csv")

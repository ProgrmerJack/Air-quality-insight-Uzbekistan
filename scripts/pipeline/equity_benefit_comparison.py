import csv
import os
from statistics import mean
from paths import pipeline_path

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
D = os.path.join(ROOT, "data", "pipeline")
CITIES = ["tashkent", "almaty", "astana", "bishkek", "ashgabat", "dushanbe"]


def summarize(group):
    return {
        "pm25": mean(r["indoor"] for r in group),
        "rwi": mean(r["rwi_f"] for r in group),
        "child": mean(r["child"] for r in group),
        "old": 100 * sum(r["infil"] >= 0.8 for r in group) / len(group),
    }


rows = []
for city in CITIES:
    with open(pipeline_path(f"regional_index_{city}.csv"), encoding="utf-8") as f:
        data = list(csv.DictReader(f))
    for r in data:
        r["indoor"] = float(r["indoor_pm25"])
        r["infil"] = float(r["infiltration"])
        r["rwi_f"] = float(r["rwi"])
        r["child"] = float(r["child_u20"])
        r["idx"] = float(r["injustice_index"])
    k = max(1, len(data) // 10)
    exp = summarize(sorted(data, key=lambda r: -r["indoor"])[:k])
    eq = summarize(sorted(data, key=lambda r: -r["idx"])[:k])
    rows.append({
        "capital": city.capitalize(),
        "k": k,
        "exp_pm25": round(exp["pm25"], 1),
        "eq_pm25": round(eq["pm25"], 1),
        "exp_rwi": round(exp["rwi"], 2),
        "eq_rwi": round(eq["rwi"], 2),
        "exp_child": round(exp["child"]),
        "eq_child": round(eq["child"]),
        "exp_old": round(exp["old"]),
        "eq_old": round(eq["old"]),
    })

out = pipeline_path("equity_benefit_comparison.csv")
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)

print(f"saved {out}")

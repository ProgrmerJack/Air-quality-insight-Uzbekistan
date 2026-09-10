"""
Named, ranked retrofit-priority list for the 434 GIGA schools in Tashkent — the ministry-facing
deliverable. Rejoins school names onto the canonical index (which stores lat/lon only) and reports
each school against Uzbekistan's OWN national PM2.5 limit (35 ug/m3 annual) rather than WHO 5,
because that is the comparator a national regulator acts on.

Index reproduces build_regional_index.py exactly (same 4 normalised dimensions, same top-decile cut),
so the headline stays 32/43 via equity.

Output: data/pipeline/indices/tashkent_school_priority_named.csv
Run from repo root:  python scripts/pipeline/tashkent_school_priority_list.py
"""
import csv, math, os, sys
import numpy as np
from paths import pipeline_path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UZ_MAC_ANNUAL = 35.0   # Uzbekistan MAC, Ministry of Health 2024 (= WHO Interim Target 1)
WHO_ANNUAL = 5.0       # WHO 2021 AQG
BG_ANNUAL, BG_WINTER = 37.9, 59.1   # Tashkent reference monitor 8881

# ponytail: winter scales the whole surface by one city-wide factor -- the manuscript's own
# finding (inversion acts as a broadly uniform multiplier, ranking is season-stable).
WINTER_FACTOR = BG_WINTER / BG_ANNUAL

ERA = {0.80: "pre-1992 (Soviet-era)", 0.65: "1992-2010", 0.50: "post-2010"}


def norm(x):
    x = np.asarray(x, float)
    return (x - x.min()) / (x.max() - x.min()) if x.max() > x.min() else x * 0


def load():
    rows = lambda p: list(csv.DictReader(open(p, encoding="utf-8")))
    sch = rows(pipeline_path("giga_schools_tashkent.csv"))
    exp = rows(pipeline_path("giga_exposure_tashkent.csv"))
    idx = rows(pipeline_path("regional_index_tashkent.csv"))
    assert len(sch) == len(exp) == len(idx) == 434, "input row counts drifted"
    for a, b in zip(sch, exp):
        assert abs(float(a["lat"]) - float(b["lat"])) < 1e-4, "school/exposure rows misaligned"
    return sch, exp, idx


def build():
    sch, exp, idx = load()
    indoor = np.array([float(r["indoor_pm25"]) for r in exp])
    infil = np.array([float(r["infiltration"]) for r in exp])
    dist = np.array([float(r["dist_m"]) for r in exp])
    rwi = np.array([float(r["rwi"]) for r in idx])
    child = np.array([float(r["child_u20"]) for r in idx])

    # ponytail: read the index rather than recompute it -- regional_index_tashkent.csv IS the
    # canonical output of build_regional_index.py. Recomputing from its rounded rwi column drifts
    # ~5e-4 and would risk quietly disagreeing with the manuscript.
    index = np.array([float(r["injustice_index"]) for r in idx])

    k = len(sch) // 10                       # 43 -- same top-decile cut as the manuscript
    by_index = np.argsort(-index)
    by_exposure = np.argsort(-indoor)
    top_idx, top_exp = set(by_index[:k].tolist()), set(by_exposure[:k].tolist())
    via_equity = top_idx - top_exp
    assert len(via_equity) == 32, f"expected 32/43 via equity, got {len(via_equity)}/{k}"

    exp_rank = {int(s): r + 1 for r, s in enumerate(by_exposure)}
    out = []
    for rank, i in enumerate(by_index, start=1):
        winter = indoor[i] * WINTER_FACTOR
        out.append({
            "priority_rank": rank,
            "school_name": sch[i]["name"],
            "lat": f"{float(sch[i]['lat']):.5f}",
            "lon": f"{float(sch[i]['lon']):.5f}",
            "dist_to_major_road_m": int(dist[i]),
            "building_era": ERA.get(round(infil[i], 2), "unknown"),
            "infiltration_factor": infil[i],
            "classroom_pm25_annual": round(indoor[i], 1),
            "classroom_pm25_winter": round(winter, 1),
            "exceeds_uz_national_mac_35_in_winter": "YES" if winter > UZ_MAC_ANNUAL else "no",
            "x_who_guideline": round(indoor[i] / WHO_ANNUAL, 1),
            "neighbourhood_rwi": round(rwi[i], 2),
            "children_under20_nearby": round(child[i], 1),
            "injustice_index": round(index[i], 3),
            "exposure_only_rank": exp_rank[int(i)],
            "in_top_43": "YES" if int(i) in top_idx else "no",
            "enters_top_43_via_equity_only": "YES" if int(i) in via_equity else "no",
        })

    dest = pipeline_path("tashkent_school_priority_named.csv")
    with open(dest, "w", newline="", encoding="utf-8-sig") as f:   # BOM so Excel reads Uzbek names
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader(); w.writerows(out)
    return out, k, len(via_equity), dest


if __name__ == "__main__":
    rows, k, n_equity, dest = build()
    top = rows[:k]
    winter_over = sum(r["exceeds_uz_national_mac_35_in_winter"] == "YES" for r in rows)
    print(f"\n434 Tashkent schools ranked. Top decile = {k}; {n_equity}/{k} enter via equity only.")
    print(f"{winter_over}/434 schools exceed Uzbekistan's national annual MAC (35 ug/m3) "
          f"inside the classroom in winter.\n")
    print(f"{'#':>3}  {'school':<52} {'era':<22} {'ann':>5} {'wint':>5}  equity")
    for r in top[:15]:
        print(f"{r['priority_rank']:>3}  {r['school_name'][:52]:<52} {r['building_era']:<22} "
              f"{r['classroom_pm25_annual']:>5} {r['classroom_pm25_winter']:>5}  "
              f"{'*' if r['enters_top_43_via_equity_only']=='YES' else ''}")
    print(f"\n(* = would be missed by exposure-only targeting)\nwrote {dest}")

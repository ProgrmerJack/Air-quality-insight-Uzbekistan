"""Comparative figure: annual vs school-hours PM2.5 across six Central Asian capitals (real embassy data)."""
import os
import pandas as pd, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
df = pd.read_csv(os.path.join(ROOT, "outputs", "multicity", "multicity_comparison.csv"))
df = df.sort_values("annual_mean")

fig, ax = plt.subplots(figsize=(8.5, 5))
y = np.arange(len(df)); h = 0.38
ax.barh(y + h/2, df["annual_mean"], h, color="#d7301f", label="Annual mean")
ax.barh(y - h/2, df["school_hours_mean"], h, color="#fdae61", label="School-hours mean (08:00-15:00)")
ax.axvline(5, color="#238b45", ls="--", lw=1.5, label="WHO 2021 annual guideline (5)")
ax.axvline(15, color="#737373", ls=":", lw=1.3, label="WHO 24-h guideline (15)")
ax.set_yticks(y)
labels = [f"{c}" + ("*" if n < 150 else "") for c, n in zip(df["City"], df["n_days"])]
ax.set_yticklabels(labels)
for i, (am, paf) in enumerate(zip(df["annual_mean"], df["PAF_resp_pct"])):
    ax.text(am + 1, i + h/2, f"{am:.0f}  (PAF {paf:.0f}%)", va="center", fontsize=8)
ax.set_xlabel("PM2.5 (ug/m3)")
ax.set_title("School-age PM2.5 exposure across six Central Asian capitals\n(U.S. Embassy reference monitors, Jan 2022-Jun 2023)")
ax.legend(loc="lower right", fontsize=8, framealpha=0.95)
ax.set_xlim(0, 90)
plt.tight_layout()
plt.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fig_multicity.png"), dpi=200)
print("saved fig_multicity.png")
print(df[["City","n_days","annual_mean","school_hours_mean","pct_days_gt15","PAF_resp_pct","classroom_typical"]].to_string(index=False))

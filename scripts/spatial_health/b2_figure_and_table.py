"""B2 figure: PAF for school-age children under conservative vs paediatric-asthma ERFs."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))

# medians and 95% CI from b2_pediatric_health_model.py (seed 42)
labels = ["All-respiratory\n(RR 1.08/10,\nconservative)",
          "Childhood asthma\n(Khreis 2017,\ncapped)",
          "Childhood asthma\n(Anenberg 2018,\ncapped)"]
med = [22.3, 57.6, 76.0]
lo  = [12.3, 25.5, 58.6]
hi  = [31.3, 75.9, 84.8]
err = [[m - l for m, l in zip(med, lo)], [h - m for h, m in zip(hi, med)]]
colors = ["#2c7fb8", "#fdae61", "#d7301f"]

fig, ax = plt.subplots(figsize=(7, 4.6))
x = np.arange(len(labels))
ax.bar(x, med, yerr=err, capsize=6, color=colors, edgecolor="white")
for i, m in enumerate(med):
    ax.text(i, m + (err[1][i]) + 2, f"{m:.0f}%", ha="center", fontweight="bold")
ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=9)
ax.set_ylabel("Population attributable fraction (%)")
ax.set_ylim(0, 100)
ax.set_title("Share of childhood disease attributable to PM2.5 in Tashkent\n"
             "(annual mean 37.9 µg/m³ vs WHO guideline 5 µg/m³)")
ax.axhspan(0, 0, color="none")
plt.tight_layout(); plt.savefig(f"{HERE}/fig_b2_paf_erfs.png", dpi=200)
print("saved fig_b2_paf_erfs.png")

"""Figure S4: data completeness / missingness for the Tashkent Station 8881 record."""
import os
import pandas as pd, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
NPJ = os.path.join(ROOT, "Research_paper", "npj_urban_sustainability")
df = pd.read_csv(os.path.join(ROOT, "outputs", "reference", "us_embassy_2022_2023.csv"))
df["dt"] = pd.to_datetime(df["datetime_local"], format="mixed", errors="coerce")
df = df.dropna(subset=["dt", "value"])
df["ym"] = df["dt"].dt.to_period("M")
df["hour"] = df["dt"].dt.hour

# Panel A: monthly completeness (valid hours / possible hours)
months = pd.period_range(df["ym"].min(), df["ym"].max(), freq="M")
poss = {m: pd.Period(m).days_in_month * 24 for m in months}
valid = df.groupby("ym").size()
comp = [100 * valid.get(m, 0) / poss[m] for m in months]
labels = [str(m) for m in months]

fig, ax = plt.subplots(1, 2, figsize=(11, 4))
ax[0].bar(range(len(months)), comp, color="#2c7fb8")
ax[0].axhline(75, color="#d7301f", ls="--", lw=1.3, label="75% daily-completeness basis")
ax[0].set_xticks(range(len(months)))
ax[0].set_xticklabels(labels, rotation=90, fontsize=7)
ax[0].set_ylabel("Monthly data completeness (%)"); ax[0].set_ylim(0, 100)
ax[0].set_title("(a) Monthly data completeness"); ax[0].legend(fontsize=8)

# Panel B: valid observations by hour-of-day (uniformity check)
hc = df.groupby("hour").size().reindex(range(24), fill_value=0)
ax[1].bar(hc.index, hc.values, color="#41ab5d")
ax[1].set_xlabel("Hour of day (local)"); ax[1].set_ylabel("Valid hourly observations")
ax[1].set_title("(b) Observations by hour of day"); ax[1].set_xticks(range(0, 24, 3))

plt.tight_layout()
out = os.path.join(NPJ, "fig_data_completeness.png")
plt.savefig(out, dpi=200)
print("saved", out)
print("monthly completeness range: %.0f-%.0f%%; mean %.0f%%" % (min(comp), max(comp), np.mean(comp)))
print("hour-of-day obs range: %d-%d (CV %.1f%%)" % (hc.min(), hc.max(), 100*hc.std()/hc.mean()))

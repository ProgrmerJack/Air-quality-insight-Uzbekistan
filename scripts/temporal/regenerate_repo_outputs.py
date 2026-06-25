"""
Regenerate the repository's temporal-analysis outputs from the MANUSCRIPT dataset
(us_embassy_2022_2023.csv, n=8,301, Station 8881) so the public repo reproduces the
paper. The existing outputs/pm25_period_summary.csv, pm25_diurnal_profile.csv and
seasonal_analysis.csv were computed on the multi-year 2018+ file and do NOT match
the manuscript; they are backed up to outputs/_superseded_multiyear/ first.
"""
import os, shutil, csv
import pandas as pd, numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "outputs")
TMP = os.path.join(OUT, "temporal"); os.makedirs(TMP, exist_ok=True)
BAK = os.path.join(OUT, "_superseded_multiyear")
os.makedirs(BAK, exist_ok=True)

df = pd.read_csv(os.path.join(OUT, "reference", "us_embassy_2022_2023.csv"))
df["dt"] = pd.to_datetime(df["datetime_local"], format="mixed")
df["hour"] = df["dt"].dt.hour
df["dow"] = df["dt"].dt.dayofweek
df["date"] = df["dt"].dt.date
df = df.dropna(subset=["value"])

def season(m):
    return {12:"Winter",1:"Winter",2:"Winter",3:"Spring",4:"Spring",5:"Spring",
            6:"Summer",7:"Summer",8:"Summer",9:"Fall",10:"Fall",11:"Fall"}[m]

for f in ["pm25_period_summary.csv","pm25_diurnal_profile.csv","seasonal_analysis.csv"]:
    p = os.path.join(TMP, f)
    if os.path.exists(p): shutil.copy2(p, os.path.join(BAK, f))

# 1) diurnal profile (hourly weekday/weekend means) -- matches the manuscript figure
prof = []
for h in range(24):
    wd = df[(df.hour==h)&(df.dow<5)]["value"]
    we = df[(df.hour==h)&(df.dow>=5)]["value"]
    prof.append([h, f"{h:02d}:00", round(wd.mean(),2), round(we.mean(),2)])
with open(os.path.join(TMP,"pm25_diurnal_profile.csv"),"w",newline="") as fh:
    w=csv.writer(fh); w.writerow(["hour","hour_label","weekday_mean","weekend_mean"]); w.writerows(prof)

# 2) period (day-part) summary -- all-days means, matching manuscript text
def win(h0,h1):
    s=df[df.hour.between(h0,h1)]["value"]; return round(s.mean(),2), int(s.size)
parts={"overnight":(2,5),"morning_commute":(7,9),"school_hours":(8,15),
       "evening_commute":(16,18),"late_evening":(19,22)}
row={}
for name,(a,b) in parts.items():
    m,n=win(a,b); row[f"mean_{name}"]=m; row[f"count_{name}"]=n
with open(os.path.join(TMP,"pm25_period_summary.csv"),"w",newline="") as fh:
    w=csv.writer(fh); keys=list(row.keys()); w.writerow(["parameter"]+keys); w.writerow(["pm25"]+[row[k] for k in keys])

# 3) seasonal analysis -- DAILY-based, matches Table S1 (>=18h days)
daily = df.groupby("date").agg(n=("value","size"), m=("value","mean"))
d18 = daily[daily.n>=18].copy()
d18["season"]=pd.to_datetime(d18.index).month.map(season)
srows=[]
for s in ["Winter","Spring","Summer","Fall"]:
    g=d18[d18.season==s]["m"]
    srows.append([s, round(g.mean(),2), round(g.median(),2), round(g.std(),2),
                  round(g.min(),2), round(g.max(),2), int(g.size)])
with open(os.path.join(TMP,"seasonal_analysis.csv"),"w",newline="") as fh:
    w=csv.writer(fh); w.writerow(["season","mean","median","std","min","max","count_days"]); w.writerows(srows)

print("Regenerated from manuscript dataset (n=%d). Backups in %s" % (len(df), BAK))
print("\nDiurnal (school 08-15 all-days):", round(df[df.hour.between(8,15)]['value'].mean(),1))
print("Period summary:", {k:row[k] for k in row if k.startswith('mean')})
print("Seasonal:")
for r in srows: print("  ",r[0],"mean",r[1],"median",r[2],"days",r[6])

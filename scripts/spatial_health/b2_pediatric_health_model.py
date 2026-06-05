"""
B2 — Paediatric health model upgrade for the npjUS reframe.
Computes population attributable fractions (PAF) for school-age children under
multiple exposure-response functions (ERFs), replacing the single mis-applied
mortality slope with childhood-asthma-specific ERFs.

PAF = 1 - RR^(-(C - C0)/10)   for ERFs expressed per 10 ug/m3
PAF = 1 - RR_per1^(-(C - C0)) for ERFs expressed per 1 ug/m3

All inputs are documented with sources. No data are invented.
"""
import numpy as np

rng = np.random.default_rng(42)
N = 100_000

C = 37.9      # annual mean PM2.5 (ug/m3), Station 8881, daily-mean basis
C0 = 5.0      # WHO 2021 annual guideline (counterfactual)
excess = C - C0

def paf_per10(rr, c=C, c0=C0):
    return 1.0 - rr ** (-(c - c0) / 10.0)

def paf_per1(rr1, c=C, c0=C0):
    return 1.0 - rr1 ** (-(c - c0))

def mc_ci(samples):
    return np.percentile(samples, [2.5, 50, 97.5])

print(f"Excess exposure above WHO guideline: {excess:.1f} ug/m3\n")

# --- ERF 1: all-cause respiratory (conservative, current paper) ---
# RR 1.08 per 10 (95% CI 1.04-1.12). Log-normal sampling.
rr_mean, lo, hi = 1.08, 1.04, 1.12
sigma = (np.log(hi) - np.log(lo)) / (2 * 1.96)
rr_s = np.exp(rng.normal(np.log(rr_mean), sigma, N))
paf1 = paf_per10(rr_s)
c1 = mc_ci(paf1 * 100)
print("ERF1 all-respiratory (RR 1.08/10, mortality-type, CONSERVATIVE):")
print(f"   PAF median {c1[1]:.1f}%  (95% CI {c1[0]:.1f}-{c1[2]:.1f}%)\n")

# --- ERF 2: childhood asthma incidence, Khreis et al. 2017 (TRAP meta-analysis) ---
# CRF 1.03 per 1 ug/m3 (95% CI 1.01-1.05). Applied to excess (UPPER-BOUND: extrapolates
# beyond within-city derivation range; reported as illustrative ceiling).
rr1_mean, lo1, hi1 = 1.03, 1.01, 1.05
sig1 = (np.log(hi1) - np.log(lo1)) / (2 * 1.96)
rr1_s = np.exp(rng.normal(np.log(rr1_mean), sig1, N))
paf2 = paf_per1(rr1_s)
c2 = mc_ci(paf2 * 100)
print("ERF2 childhood asthma, Khreis 2017 (1.03/1 ug/m3), applied to full excess (UPPER BOUND):")
print(f"   PAF median {c2[1]:.1f}%  (95% CI {c2[0]:.1f}-{c2[2]:.1f}%)\n")

# --- ERF 3: paediatric asthma incidence, Anenberg et al. 2018 (EHP) ---
# Central RR range 1.34-1.93 per 10 ug/m3. Use uniform over the reported range.
rr3_s = rng.uniform(1.34, 1.93, N)
paf3 = paf_per10(rr3_s)
c3 = mc_ci(paf3 * 100)
print("ERF3 paediatric asthma, Anenberg 2018 (RR 1.34-1.93/10):")
print(f"   PAF median {c3[1]:.1f}%  (95% CI {c3[0]:.1f}-{c3[2]:.1f}%)\n")

# --- ERF 2b/3b: capped increment to ~upper derivation range (Jacquemin/Anenberg ~34 ug/m3) ---
# To curb extrapolation, cap exposure increment at 29 ug/m3 (i.e., C capped ~34).
C_cap = 34.0
paf2b = mc_ci((1 - rr1_s ** (-(C_cap - C0))) * 100)
paf3b = mc_ci((1 - rr3_s ** (-(C_cap - C0) / 10.0)) * 100)
print("Sensitivity: increment capped at derivation ceiling (C=34 ug/m3):")
print(f"   Khreis-capped PAF median {paf2b[1]:.1f}% (95% CI {paf2b[0]:.1f}-{paf2b[2]:.1f}%)")
print(f"   Anenberg-capped PAF median {paf3b[1]:.1f}% (95% CI {paf3b[0]:.1f}-{paf3b[2]:.1f}%)\n")

# --- Counterfactual sensitivity for the conservative ERF1 (matches Table S3) ---
print("Counterfactual sensitivity (ERF1, RR 1.08/10):")
for c0 in (5, 10, 15):
    s = (1 - rr_s ** (-(C - c0) / 10.0)) * 100
    ci = mc_ci(s)
    print(f"   C0={c0:>2}: excess {C-c0:.1f}  PAF {ci[1]:.1f}% (95% CI {ci[0]:.1f}-{ci[2]:.1f}%)")

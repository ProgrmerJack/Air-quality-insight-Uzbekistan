# CANONICAL MANUSCRIPT NUMBERS
## Single Source of Truth for EMA Submission
Generated: 2026-01-07T10:46:09.201205

---

## CRITICAL: Use These Numbers Everywhere

### Temporal Coverage
- **Study period**: 2022-01-01 to 2023-06-29
- **Days in period**: 545
- **Total possible hours**: 13080
- **Valid hourly records**: 8301 (63.5% coverage)

### Daily Aggregation (≥18 hours/day threshold)
- **Valid days for analysis**: 346
- **Days with 24 hours**: 250

### Annual Statistics
- **Annual mean PM2.5**: 37.9 µg/m³
- **Standard deviation (hourly)**: 38.4 µg/m³
- **Standard error of mean**: 1.63 µg/m³ ← USE THIS FOR MONTE CARLO
- **Median**: 28.7 µg/m³
- **Maximum hourly**: 857.0 µg/m³

### WHO Guideline Exceedances
- **Days exceeding 24-hour guideline (>15 µg/m³)**: 322/346 (93.1%)
- **Ratio vs WHO 2021 annual (5 µg/m³)**: 7.6×

### Seasonal Breakdown (for Table S1)
| Season | N Days | Mean | Median | Days >15 | Exc% |
|--------|--------|------|--------|----------|------|
| Winter | 109 | 59.1 | 43.3 | 107 | 98.2% |
| Spring | 144 | 26.9 | 26.1 | 134 | 93.1% |
| Summer | 61 | 26.1 | 25.4 | 53 | 86.9% |
| Fall | 32 | 37.6 | 28.9 | 28 | 87.5% |
| **Annual** | **346** | **37.9** | **28.7** | **322** | **93.1%** |

### Health Impact Inputs
- **Exposure mean**: 37.9 µg/m³
- **Exposure SE**: 1.63 µg/m³
- **Excess vs WHO 2021 (5 µg/m³)**: 32.9 µg/m³
- **Counterfactual (primary)**: 5 µg/m³ (WHO 2021)
- **Counterfactual (sensitivity)**: 10, 15 µg/m³

### Monte Carlo Parameters
```
Distribution: Normal
Mean: 37.9 µg/m³
SE: 1.63 µg/m³
Note: Use SE (uncertainty on mean), NOT SD (population variability)
```

---

## Verification Checksums
- Valid days × 18 hours = 6228 (must be < 8301 total hours) ✓
- Sum of seasonal days = 346 (must equal 346) ✓

---

**DO NOT USE**: SD=38.4 for Monte Carlo (this is hourly variability, not mean uncertainty)
**DO NOT USE**: 518 days (mathematically impossible given 8,301 hours)
**DO NOT USE**: Station 4902926 (Sputnik-4) - use Station 8881 only


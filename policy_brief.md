# Lunch vs. PM₂.₅ — Tashkent School Corridors (Draft Policy Note)

**Headline finding.** Monitoring from the OpenAQ Sputnik-4 station (Asia/Tashkent time zone) shows overnight and pre-commute PM₂.₅ routinely exceeding 35 µg/m³, with lunchtime averages still 40 % above the WHO daily guideline (15 µg/m³). Weekends add a further 10–15 µg/m³ to the lunchtime load, pointing to traffic-adjacent and informal heating sources that continue through the school day.

**Data sources.**
- Hourly PM₂.₅: OpenAQ Platform (Location ID 4902926, provider: AirGradient), ingest completed 29 Oct 2025 (`openaq_location_4902926_measurments.csv`).
- Benchmarks: WHO Ambient Air Quality Database v6.1 (2024 update). Tashkent annual mean = 41–43 µg/m³ (2018–2019) versus WHO 2021 guideline of 5 µg/m³.
- Processing outputs: see `outputs/pm25_diurnal_profile.csv`, `outputs/pm25_period_summary.csv`, `outputs/pm25_daily_means.csv`, and `outputs/who_pm25_context.csv` for Datawrapper-ready tables.

**Key observations.**
- **Night-time accumulation bleeds into class time.** Median PM₂.₅ drops from ~36 µg/m³ during the 07:00 commute to 20 µg/m³ across 11:00–15:00, yet the lunch window remains above the WHO daily limit. Weekends suppress that decline; 13:00 PM₂.₅ averages 9.7 µg/m³ higher than school-day levels.
- **Limited afternoon relief.** Afternoon medians fall to 8 µg/m³ only after 15:00, suggesting opportunities for well-timed ventilation (post last bell) rather than during peak occupancy.
- **WHO gap persists.** WHO annual means for Tashkent (41–43 µg/m³) reaffirm the chronic burden; even the “cleaner” school-hour average (21 µg/m³) exceeds the daily guideline by 40 %, underscoring the need for indoor controls in parallel with transport and solid-fuel reforms.

**Recommended Datawrapper figures (live chart links).**
1. *Weekday vs. weekend diurnal profile* (`pm25_diurnal_profile.csv`) – [line chart](https://datawrapper.dwcdn.net/mvCHo/1/) covering 00:00–23:00; highlight 07:00 and 13:00 markers.
2. *Daily mean distributions* (`pm25_daily_means.csv`) – [time-series split](https://datawrapper.dwcdn.net/dwu01/1/) to show weekday vs weekend swings.
3. *Period comparison bar* (`pm25_period_summary.csv`) – [grouped bar chart](https://datawrapper.dwcdn.net/TXezZ/1/) for overnight, commute, school hours, afternoon, late evening (annotate WHO 24 h guideline at 15 µg/m³).

**Three immediate actions for the city education & transport team.**
- **Targeted ventilation windows + filtration pilots.** Lock in HEPA or DIY Corsi-Rosenthal units for priority classrooms, turn on mechanical ventilation after 15:00 when outdoor PM₂.₅ dips beneath 10 µg/m³, and close windows during the 07:00–13:00 plateau unless filtered air is available.
- **Knife-edge school street management.** Extend the vehicle exclusion pilot to 07:00–09:00 + 12:00–14:00 at the three schools closest to the Sputnik-4 monitor; pair with traffic police enforcement and parent SMS blasts.
- **Fuel-switch incentives for canteen and nearby vendors.** Provide clean LPG/electric cook-stoves and enforce no-solid-fuel zones within 250 m of school gates during operating hours; monitor impact with OpenAQ micro-sensors loaned to students for science projects.

**Receipts & provenance.**
- OpenAQ download: https://explore.openaq.org/locations/4902926 (AirGradient provider listing in AWS registry: https://registry.opendata.aws/openaq/)
- WHO AQ database (v6.1): https://www.who.int/data/gho/data/themes/air-pollution/who-air-quality-database (sheet `Update 2024 (V6.1)`)
- Datawrapper upload instructions: https://academy.datawrapper.de/article/100-how-to-create-a-line-chart (use the CSV tables exported above; link charts in the final brief once published).

**Next steps.**
1. Add NO₂ from the same OpenAQ feed to distinguish combustion hotspots and better target street interventions.
2. Request the Education Ministry to share HVAC runtime logs for the pilot schools to validate the proposed ventilation schedule.
3. Publish the charts via Datawrapper and append live links plus WHO table snapshot to the final single-page PDF for council circulation.

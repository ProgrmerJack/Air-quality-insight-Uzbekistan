"""
Verify every manuscript bibitem against the live Crossref record (catches fabricated
or mis-cited references before submission). Prints, per key: claimed year vs the
best Crossref match's title/year/container/DOI and a crude title-similarity score.
Manual review the LOW-similarity or year-mismatch rows.
"""
import sys, json, time, urllib.parse, urllib.request, difflib
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# (key, claimed title, claimed year)
REFS = [
 ("gauderman2015association","Association of improved air quality with lung development in children",2015),
 ("gehring2013air","Air pollution exposure and lung function in children the ESCAPE project",2013),
 ("schwartz2004air","Air pollution and children's health",2004),
 ("tursumbayeva2023","Cities of Central Asia new hotspots of air pollution in the world",2023),
 ("worldbank2024centralasia","Air Quality Management in Central Asia",2024),
 ("worldbank2024tashkent","Air Quality Assessment for Tashkent and the Roadmap for Air Quality Management Improvement in Uzbekistan",2024),
 ("crabb2026fairness","Holistic fairness considerations in facility placement decisions",2026),
 ("acag2020satpm25","Global estimates and long-term trends of fine particulate matter concentrations 1998-2018",2020),
 ("vandonkelaar2021","Monthly global estimates of fine particulate matter and their uncertainty",2021),
 ("s5p2018no2","TROPOMI on the ESA Sentinel-5 Precursor",2012),
 ("era5hersbach","The ERA5 global reanalysis",2020),
 ("barkjohn2021","Development and application of a United States-wide correction for PM2.5 data collected with the PurpleAir sensor",2021),
 ("karner2010nearroad","Near-roadway air quality synthesizing the findings from real-world data",2010),
 ("chen2012infiltration","Review of relationship between indoor and outdoor particles I/O ratio infiltration factor and penetration factor",2012),
 ("gbd2021","Global Burden of Disease Study 2021",2024),
 ("khreis2017exposure","Exposure to traffic-related air pollution and risk of development of childhood asthma",2017),
 ("anenberg2018global","Estimates of the global burden of ambient PM2.5 ozone and NO2 on asthma incidence and emergency room visits",2018),
 ("bharti2025classroom","Clean air in the classroom environmental inputs and human capital formation",2025),
 ("xu2024testscores","Reducing indoor particulate air pollution improves student test scores a randomized double-blind crossover study",2024),
 ("banholzer2024aircleaners","Air cleaners and respiratory infections in schools a modeling study",2024),
 ("mohai2011schools","Air pollution around schools is linked to poorer student health and academic performance",2011),
 ("grineski2018schools","Geographic and social disparities in exposure to air neurotoxicants at U.S. public schools",2018),
 ("cognitionreview","The relationship between air pollution and cognitive functions in children and adolescents a systematic review",2020),
 ("hepacognition","Cognitive benefits of air purification among schoolchildren a randomized double-blind crossover trial",2026),
]

def crossref(title):
    q = urllib.parse.urlencode({"query.bibliographic": title, "rows": 1})
    url = "https://api.crossref.org/works?" + q
    req = urllib.request.Request(url, headers={"User-Agent":"bib-verify/1.0 (mailto:research@example.org)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        items = json.load(r)["message"]["items"]
    if not items: return None
    it = items[0]
    return {"title": (it.get("title") or [""])[0],
            "year": (it.get("issued",{}).get("date-parts") or [[None]])[0][0],
            "container": (it.get("container-title") or [""])[0] if it.get("container-title") else "",
            "doi": it.get("DOI","")}

print(f"{'KEY':<26}{'claim':<6}{'cr_yr':<6}{'sim':<5} crossref title / DOI")
print("-"*120)
for key, title, yr in REFS:
    try:
        m = crossref(title)
    except Exception as e:
        print(f"{key:<26}{yr:<6}{'ERR':<6}{'':<5} {e}"); continue
    if not m:
        print(f"{key:<26}{yr:<6}{'NONE':<6}{'':<5} *** NO CROSSREF MATCH ***"); continue
    sim = difflib.SequenceMatcher(None, title.lower(), (m["title"] or "").lower()).ratio()
    flag = ""
    if sim < 0.6: flag += " <<LOW-SIM"
    if m["year"] and abs((m["year"] or 0) - yr) > 1: flag += " <<YEAR"
    print(f"{key:<26}{yr:<6}{str(m['year']):<6}{sim:<5.2f} {m['title'][:70]} | {m['container'][:28]} | {m['doi']}{flag}")
    time.sleep(0.5)

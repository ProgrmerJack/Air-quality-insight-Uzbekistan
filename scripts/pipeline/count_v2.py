import re, os
p = os.path.join(os.path.dirname(__file__), "..", "..", "Research_paper",
                 "npj_urban_sustainability", "paper_npjUS_v2_regional.tex")
t = open(p, encoding="utf-8").read()
m = re.search(r"begin\{abstract\}(.*?)end\{abstract\}", t, re.S).group(1)
m = re.sub(r"\\[a-zA-Z]+", " ", m)        # strip latex commands
m = re.sub(r"[${}\\]", " ", m)            # strip braces/dollar/backslash
words = [w for w in m.split() if any(c.isalpha() for c in w)]
print("Abstract words:", len(words), "(limit 150)")
title = ("An open environmental-justice method for prioritising protection of schoolchildren "
         "from air pollution in Central Asia")
print("Title words:", len(title.split()), "(limit 15)")
# count bibitems
print("Bibitems:", len(re.findall(r"\\bibitem", t)), "(limit 60)")
# count distinct \cite keys actually used
cited = set()
for grp in re.findall(r"\\cite\{([^}]*)\}", t):
    for k in grp.split(","):
        cited.add(k.strip())
defined = set(re.findall(r"\\bibitem\{([^}]*)\}", t))
print("Distinct cite keys used:", len(cited))
print("Cited-but-undefined:", sorted(cited - defined))
print("Defined-but-uncited:", sorted(defined - cited))

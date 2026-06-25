import re, sys
s = open(sys.argv[1], encoding="utf-8").read()
defined = set(re.findall(r"\\bibitem\[[^\]]*\]\{([^}]+)\}", s))
cited = set()
for m in re.findall(r"\\cite\{([^}]+)\}", s):
    for k in m.split(","):
        cited.add(k.strip())
print("defined:", len(defined), "cited:", len(cited))
print("ORPHANS (defined, never cited):", sorted(defined - cited))
print("MISSING (cited, not defined):", sorted(cited - defined))

import re, sys
s = open(sys.argv[1], encoding="utf-8").read()
for label, key in re.findall(r"\\bibitem\[([^\]]*)\]\{([^}]+)\}", s):
    ly = re.search(r"(19|20)\d\d", label)
    ky = re.search(r"(19|20)\d\d", key)
    if ly and ky and ly.group(0) != ky.group(0):
        print(f"{key:32} key_year={ky.group(0)}  label_year={ly.group(0)}")

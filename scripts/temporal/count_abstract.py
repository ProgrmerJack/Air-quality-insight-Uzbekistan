import re, sys
s = open(sys.argv[1], encoding="utf-8").read()
a = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", s, re.S).group(1)
a = re.sub(r"\\noindent", "", a)
a = re.sub(r"\\[a-zA-Z]+", " ", a)
a = re.sub(r"[{}$~]", " ", a)
print("abstract words:", len(a.split()))

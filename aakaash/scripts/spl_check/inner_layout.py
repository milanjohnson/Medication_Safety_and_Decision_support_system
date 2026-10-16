# SOURCE: NOT IN PAPERS (own diagnostic tooling). Read-only: opens the DailyMed zip, never extracts or modifies it.
# Run with the venv python in isolated mode (-I); see aakaash/scripts/spl_check/README.md
import io, os, sys, zipfile
from collections import Counter

p = sys.argv[1]
n = int(sys.argv[2])
zf = zipfile.ZipFile(p)
members = [i for i in zf.infolist() if not i.is_dir()][:n]
exts = Counter(); counts = Counter(); xml_per = Counter(); depth = Counter()
for k, info in enumerate(members):
    inner = zipfile.ZipFile(io.BytesIO(zf.read(info)))
    names = [i.filename for i in inner.infolist() if not i.is_dir()]
    xml_per[sum(x.lower().endswith(".xml") for x in names)] += 1
    for x in names:
        exts[os.path.splitext(x.lower())[1] or "(none)"] += 1
        depth[x.count("/")] += 1
    if k < 3:
        print("inner zip", info.filename)
        for i in inner.infolist():
            print("    ", repr(i.filename), i.file_size)
print(f"over first {len(members)} outer members:")
print("inner extensions:", exts.most_common())
print("xml files per inner zip:", sorted(xml_per.items()))
print("inner path depth:", dict(depth))

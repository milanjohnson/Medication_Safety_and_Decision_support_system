# SOURCE: NOT IN PAPERS (own diagnostic tooling). Read-only: opens the DailyMed zip, never extracts or modifies it.
# Run with the venv python in isolated mode (-I); see aakaash/scripts/spl_check/README.md
import os, sys, time, zipfile
from collections import Counter

p = sys.argv[1]
print("name:", os.path.basename(p))
print("size bytes:", os.path.getsize(p))
t = time.time()
zf = zipfile.ZipFile(p)
infos = zf.infolist()
print(f"opens as zip: yes (central directory read in {time.time()-t:.1f}s)")
print("total entries:", len(infos), " dirs:", sum(i.is_dir() for i in infos))
print("first 8 entries:")
for i in infos[:8]:
    print("  ", repr(i.filename), i.file_size, "bytes uncompressed")
files = [i for i in infos if not i.is_dir()]
print("extensions:", Counter(os.path.splitext(i.filename.lower())[1] or "(none)" for i in files).most_common())
print("top-level prefixes:", Counter(i.filename.split("/")[0] for i in infos).most_common(5))
print("depth of paths:", Counter(i.filename.count("/") for i in files).most_common(5))
sizes = sorted(i.file_size for i in files)
print("member size min/median/max bytes:", sizes[0], sizes[len(sizes)//2], sizes[-1])
print("total uncompressed bytes:", sum(sizes))
t = time.time()
bad = zf.testzip()
print(f"testzip (CRC of every member): first bad member = {bad!r}  ({time.time()-t:.0f}s)")

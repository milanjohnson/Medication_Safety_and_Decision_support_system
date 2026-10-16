# SOURCE: NOT IN PAPERS (own diagnostic tooling). Read-only: opens the DailyMed zip, never extracts or modifies it.
# Run with the venv python in isolated mode (-I); see aakaash/scripts/spl_check/README.md
import sys, unicodedata
from collections import Counter
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from medsafe.spl import iter_part
st = Counter(); only_fb = []; c = Counter(); n = 0
for r in iter_part(Path(sys.argv[2]), st, 200):
    di = r["sections"].get("drug_interactions", [])
    if di and all(p["method"] == "title_fallback" for p in di):
        only_fb.append([p["title"][:60] for p in di])
    for ps in r["sections"].values():
        for p in ps:
            for ch in p["text"]:
                if ord(ch) > 127: c[(hex(ord(ch)), unicodedata.name(ch, "?"))] += 1
print("labels whose ONLY drug_interactions came from title_fallback:", len(only_fb))
for t in only_fb: print("   ", t)
print("U+FFFD (real replacement char) count:", sum(v for (h, _), v in c.items() if h == "0xfffd"))
print("top non-ASCII chars in parsed text:", c.most_common(8))

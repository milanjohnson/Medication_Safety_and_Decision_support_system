# SOURCE: NOT IN PAPERS (own diagnostic tooling). Read-only: opens the DailyMed zip, never extracts or modifies it.
"""Where a section's TITLE says "drug interactions" but its LOINC CODE says otherwise (code wins in
spl.py), how much text is lost? A section counts as lost only if its text is not inside any section
spl.py captured for that label.
usage: title_code_conflicts.py <aakaash dir> <zip> <n labels, 0 = all>"""
import io
import re
import sys
import time
import zipfile
from collections import Counter
from pathlib import Path

from lxml import etree

sys.path.insert(0, sys.argv[1])
from medsafe import spl  # noqa: E402

zip_path, limit = Path(sys.argv[2]), int(sys.argv[3])
ANCHORED = re.compile(r"(clinically significant )?drug([ /-]+drug)? interactions?:?", re.I)
BROAD = re.compile(r"drug.{0,3}interaction", re.I)
NUMBERED = re.compile(r"\d+(\.\d+)*\.?\s+" + ANCHORED.pattern, re.I)  # e.g. "7 DRUG INTERACTIONS", "7.1 Drug Interactions"
DI_CODE = "34073-7"


def norm(t):
    return re.sub(r"\s+", " ", t).strip().lower()


def labels():
    with zipfile.ZipFile(zip_path) as zf:
        k = 0
        for info in zf.infolist():
            if info.is_dir():
                continue
            inner = zipfile.ZipFile(io.BytesIO(zf.read(info)))
            for ii in inner.infolist():
                if ii.filename.lower().endswith(".xml"):
                    yield inner.read(ii)
            k += 1
            if limit and k >= limit:
                return


t0 = time.perf_counter()
n = 0
cat = {k: Counter() for k in ("A_code_other_section", "A_code_unmapped", "B_other_code_mapped", "B_other_code_unmapped")}
lab = {k: set() for k in cat}
lost = {k: 0 for k in cat}; folded = {k: 0 for k in cat}
lost_labels_no_di = set(); a_no_di = set(); num = Counter(); num_lab = set(); num_lost = 0; num_lost_nodi = set(); num_parents = Counter(); codes_a = Counter(); titles_a = Counter(); with_title_di_labels = set()
total_labels_title_di = set()
for idx, data in enumerate(labels()):
    n += 1
    rec = spl.parse_label(data)
    captured = norm(" ".join(p["text"] for ps in rec["sections"].values() for p in ps))
    has_di = "drug_interactions" in rec["sections"]
    root = etree.fromstring(data)
    for sec in root.iter():
        if spl._ln(sec) != "section":
            continue
        code, title = spl._section_code_title(sec)
        t = re.sub(r"\s+", " ", title).strip()
        if not BROAD.search(t) or code == DI_CODE:
            continue
        mapped = spl.SECTION_CODES.get(code or "")
        anchored = bool(ANCHORED.fullmatch(t))
        key = ("A_" if anchored else "B_") + ("code_other_section" if anchored and mapped else
              "code_unmapped" if anchored else "other_code_mapped" if mapped else "other_code_unmapped")
        text = norm(spl._text_of(sec))
        probe = text[:160]
        is_in = bool(probe) and probe in captured
        cat[key][(code, t[:60])] += 1
        lab[key].add(idx)
        folded[key] += is_in
        lost[key] += not is_in
        total_labels_title_di.add(idx)
        if NUMBERED.fullmatch(t) and not mapped:
            num[(code, t[:40])] += 1; num_lab.add(idx)
            if not is_in:
                num_lost += 1
                par = sec.getparent()
                while par is not None and spl._ln(par) != "section":
                    par = par.getparent()
                num_parents[(spl._section_code_title(par)[0], spl._section_code_title(par)[1][:40]) if par is not None else "top-level"] += 1
                if not has_di:
                    num_lost_nodi.add(rec["set_id"])
        if key == "A_code_other_section":
            if not has_di:
                a_no_di.add(rec["set_id"])
            codes_a[(code, mapped)] += 1
            if not is_in and not has_di:
                lost_labels_no_di.add(rec["set_id"])

print(f"labels checked: {n} ({time.perf_counter() - t0:.1f}s)")
desc = {
    "A_code_other_section": "title is exactly a Drug Interactions title, code maps to ANOTHER section (code wins)",
    "A_code_unmapped": "title is exactly a Drug Interactions title, code unmapped (captured as drug_interactions by title)",
    "B_other_code_mapped": "title only mentions drug interactions (numbered/longer), code maps to another section",
    "B_other_code_unmapped": "title only mentions drug interactions (numbered/longer), code unmapped (not captured as DI)",
}
for k in cat:
    print(f"\n[{k}] {desc[k]}\n   sections {sum(cat[k].values())}, labels {len(lab[k])}; "
          f"text found inside a captured section: {folded[k]}; NOT inside any captured section: {lost[k]}")
    for (code, title), c in cat[k].most_common(6):
        print(f"      {c:4d} x code={code} title={title!r}")
print("\nA_code_other_section by (code, section it was assigned to):", dict(codes_a))
print(f"labels with an A_code_other_section section whose text is not captured anywhere AND that have no drug_interactions section: {len(lost_labels_no_di)}")
print(f"labels with any section whose title mentions drug interactions but code is not {DI_CODE}: {len(total_labels_title_di)}")
print(f"A_code_other_section labels that have no drug_interactions section at all: {len(a_no_di)}")
print(f"\nNUMBERED exact titles ('7 DRUG INTERACTIONS', '7.1 Drug Interactions', ...) with an unmapped code: sections {sum(num.values())}, labels {len(num_lab)}; "
      f"NOT inside any captured section: {num_lost} (in {len(num_lost_nodi)} labels that have no drug_interactions section)")
for (code, t), c in num.most_common(6):
    print(f"      {c:4d} x code={code} title={t!r}")
print("parents of the not-captured numbered sections:", dict(num_parents.most_common(6)))

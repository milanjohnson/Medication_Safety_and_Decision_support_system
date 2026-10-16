# SOURCE: NOT IN PAPERS (own diagnostic tooling). Read-only: opens the DailyMed zip, never extracts or modifies it.
"""Survey every <ingredient> classCode in a DailyMed zip, independent of spl.py.
usage: ingredient_classes.py <zip> <n labels, 0 = all>"""
import io
import sys
import time
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

from lxml import etree

zip_path, limit = Path(sys.argv[1]), int(sys.argv[2])


def ln(el):
    return el.tag.rsplit("}", 1)[-1] if isinstance(el.tag, str) else ""


def child(el, name):
    for c in el:
        if ln(c) == name:
            return c


def substance(ing):
    """(UNII code or None, name or None) of ingredient/ingredientSubstance."""
    sub = child(ing, "ingredientSubstance")
    if sub is None:
        return None, None
    code = child(sub, "code")
    name = child(sub, "name")
    return (code.get("code") if code is not None else None,
            name.text.strip() if name is not None and name.text and name.text.strip() else None)


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
classes = Counter(); parents = defaultdict(Counter); examples = defaultdict(list)
n_labels = 0; labels_with = defaultdict(set)
actir_dup = actir_new = 0
iact_overlap_labels = []
no_unii = Counter()
actir_labels = []
for idx, data in enumerate(labels()):
    root = etree.fromstring(data)
    n_labels += 1
    per = defaultdict(list)
    for el in root.iter():
        if ln(el) == "ingredient":
            cls = el.get("classCode")
            classes[cls] += 1
            labels_with[cls].add(idx)
            p = el.getparent()
            parents[cls][ln(p) + ("/" + ln(p.getparent()) if p.getparent() is not None else "")] += 1
            code, name = substance(el)
            if code is None:
                no_unii[cls] += 1
            per[cls].append((code, name))
            if cls not in ("ACTIB", "ACTIM", "IACT") and len(examples[cls]) < 3:
                examples[cls].append((idx, name))
    active = {c for cls in ("ACTIB", "ACTIM") for c, _ in per[cls] if c}
    active_names = {n.lower() for cls in ("ACTIB", "ACTIM") for _, n in per[cls] if n}
    for code, name in per["ACTIR"]:
        if (code and code in active) or (name and name.lower() in active_names):
            actir_dup += 1
        else:
            actir_new += 1
    if per["ACTIR"] and len(actir_labels) < 4:
        actir_labels.append((idx, per["ACTIB"], per["ACTIM"], per["ACTIR"]))
    inactive_codes = {c for c, _ in per["IACT"] if c}
    all_active = active | {c for c, _ in per["ACTIR"] if c}
    if inactive_codes & all_active:
        iact_overlap_labels.append(idx)

print(f"labels surveyed: {n_labels}  ({time.perf_counter() - t0:.1f}s)")
print("ingredient classCode counts (elements):", dict(classes.most_common()))
print("labels containing each:", {k: len(v) for k, v in labels_with.items()})
for cls in classes:
    print(f"  parent chain for {cls}: {dict(parents[cls].most_common(3))}; elements without a UNII code: {no_unii[cls]}")
print("examples for classes other than ACTIB/ACTIM/IACT:", dict(examples))
print(f"ACTIR elements whose substance is already an ACTIB/ACTIM substance in the same label: {actir_dup}; not already present: {actir_new}")
print("first ACTIR labels (idx, ACTIB, ACTIM, ACTIR as (UNII, name)):")
for t in actir_labels:
    print("  ", t)
print(f"labels where a substance is both IACT and active (ACTIB/ACTIM/ACTIR) by UNII: {len(iact_overlap_labels)}  idx: {iact_overlap_labels[:10]}")

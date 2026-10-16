# SOURCE: NOT IN PAPERS (own diagnostic tooling). Read-only: opens the DailyMed zip, never extracts or modifies it.
"""Check spl.parse_label's ingredient sets against the raw XML, independently of spl.py's logic.
usage: verify_ingredients.py <aakaash dir> <zip> <n labels, 0 = all>"""
import io
import sys
import time
import zipfile
from collections import Counter
from pathlib import Path

from lxml import etree

sys.path.insert(0, sys.argv[1])
from medsafe.spl import ACTIVE_CLASSES, normalize_ingredient, parse_label  # noqa: E402

zip_path, limit = Path(sys.argv[2]), int(sys.argv[3])


def ln(el):
    return el.tag.rsplit("}", 1)[-1] if isinstance(el.tag, str) else ""


def child(el, name):
    for c in el:
        if ln(c) == name:
            return c


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


def ingredients(root):
    out = {}  # class -> list of (unii, name, moiety)
    for el in root.iter():
        if ln(el) != "ingredient":
            continue
        sub = child(el, "ingredientSubstance")
        if sub is None:
            continue
        code, name = child(sub, "code"), child(sub, "name")
        inner = child(child(sub, "activeMoiety"), "activeMoiety") if child(sub, "activeMoiety") is not None else None
        mo = child(inner, "name") if inner is not None else None
        out.setdefault(el.get("classCode"), []).append((
            code.get("code") if code is not None else None,
            name.text.strip() if name is not None and name.text else None,
            mo.text.strip() if mo is not None and mo.text else None))
    return out


t0 = time.perf_counter()
n = bad_missing = bad_extra = bad_iact = reference_dup = 0
other_classes = Counter(); both_iact_active = []; tralement = None; classes_used = Counter()
for data in labels():
    n += 1
    root = etree.fromstring(data)
    rec = parse_label(data)
    raw = ingredients(root)
    for cls in raw:
        if cls not in ACTIVE_CLASSES and cls != "IACT":
            other_classes[cls] += len(raw[cls])
    active = [t for cls in ACTIVE_CLASSES for t in raw.get(cls, [])]
    active_names = {normalize_ingredient(nm) for _, nm, _ in active if nm}
    active_uniis = {u for u, _, _ in active if u}
    iact_names = {normalize_ingredient(nm) for _, nm, _ in raw.get("IACT", []) if nm}
    got = set(rec["ingredients"])
    if not active:
        continue
    # every active substance (by UNII) must be represented by a name in the record
    names_by_unii = {}
    for u, nm, _ in active:
        if nm:
            names_by_unii.setdefault(u or normalize_ingredient(nm), set()).add(normalize_ingredient(nm))
    for u, names in names_by_unii.items():  # one spelling per substance code is enough
        if not (names & got):
            bad_missing += 1
            print("MISSING from record:", rec["set_id"], u, names)
            break
    # nothing in the record may be a name that is not an active ingredient name
    extra = got - active_names
    if extra:
        bad_extra += 1
        print("EXTRA (not an active name):", rec["set_id"], extra)
    # an inactive ingredient name in the record is only acceptable if that name is also active
    leaked = (got & iact_names) - active_names
    if leaked:
        bad_iact += 1
        print("INACTIVE entered the set:", rec["set_id"], leaked)
    if iact_names & active_names:
        both_iact_active.append(rec["set_id"])
    classes_used[rec["ingredient_source"]] += 1
    # is any ACTIR substance just another form of an ACTIB/ACTIM moiety (a "reference" duplicate)?
    base_moieties = {m for cls in ("ACTIB", "ACTIM") for _, _, m in raw.get(cls, []) if m}
    if any(m in base_moieties for _, _, m in raw.get("ACTIR", []) if m):
        reference_dup += 1
        print("ACTIR moiety equals an ACTIB/ACTIM moiety:", rec["set_id"], rec["ingredients_raw"], rec["active_moieties_raw"])
    if "TRALEMENT" in rec["title"].upper() and tralement is None:
        tralement = rec

print(f"labels checked: {n} ({time.perf_counter() - t0:.1f}s)")
print(f"labels where an active substance is missing from the record: {bad_missing}")
print(f"labels where the record has a name that is not an active ingredient name: {bad_extra}")
print(f"labels where an INACTIVE-only ingredient entered the set: {bad_iact}")
print(f"labels where a substance name is both active and IACT (legitimately active): {len(both_iact_active)} {both_iact_active[:5]}")
print(f"labels with an ACTIR whose moiety equals an ACTIB/ACTIM moiety in the same label: {reference_dup}")
print("ingredient classes seen that are not ACTIB/ACTIM/ACTIR/IACT (elements):", dict(other_classes))
print("ingredient_source distribution:", dict(classes_used))
if tralement:
    print("TRALEMENT:", tralement["set_id"], "ingredients_raw =", tralement["ingredients_raw"],
          "| moieties =", tralement["active_moieties_raw"], "| source =", tralement["ingredient_source"])
else:
    print("TRALEMENT not found in the labels checked")

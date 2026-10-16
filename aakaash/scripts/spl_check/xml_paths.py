# SOURCE: NOT IN PAPERS (own diagnostic tooling). Read-only: opens the DailyMed zip, never extracts or modifies it.
# Prints the real element paths for fields spl.py needs, so no XML path is guessed.
# usage: xml_paths.py <zip> <n labels>
import io, sys, zipfile
from collections import Counter
from pathlib import Path

from lxml import etree

zip_path, n = Path(sys.argv[1]), int(sys.argv[2])


def ln(el):
    return el.tag.rsplit("}", 1)[-1] if isinstance(el.tag, str) else ""


def path_of(el):
    parts = []
    while el is not None:
        parts.append(ln(el))
        el = el.getparent()
    return "/".join(reversed(parts))


def labels(limit):
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
            if k >= limit:
                return


generic_paths, moiety_paths, org_paths = Counter(), Counter(), Counter()
no_moiety = 0; ing_total = 0; both_label = None
shown = {"ingredient": False, "generic": False, "author": False}
for idx, data in enumerate(labels(n)):
    root = etree.fromstring(data)
    classes = set()
    for el in root.iter():
        name = ln(el)
        if name == "genericMedicine":
            for c in el:
                if ln(c) == "name":
                    generic_paths[path_of(c)] += 1
            if not shown["generic"]:
                print("--- genericMedicine snippet:\n", etree.tostring(el, pretty_print=True).decode()[:500]); shown["generic"] = True
        elif name == "ingredient" and el.get("classCode") in ("ACTIB", "ACTIM", "ACTIR"):
            classes.add(el.get("classCode"))
            ing_total += 1
            found = [m for m in el.iter() if ln(m) == "name" and ln(m.getparent()) == "activeMoiety"]
            if not found:
                no_moiety += 1
            for m in found:
                moiety_paths[path_of(m).split("manufacturedProduct/")[-1]] += 1
            if not shown["ingredient"] and el.get("classCode") == "ACTIB":
                print("--- ACTIB ingredient snippet:\n", etree.tostring(el, pretty_print=True).decode()[:1200]); shown["ingredient"] = True
    if {"ACTIB", "ACTIM"} <= classes and both_label is None:
        both_label = idx
    for el in root.iter():
        if ln(el) == "representedOrganization":
            for c in el:
                if ln(c) == "name":
                    org_paths[path_of(c)] += 1
    if not shown["author"]:
        for el in root:
            if ln(el) == "author":
                print("--- author snippet:\n", etree.tostring(el, pretty_print=True).decode()[:700]); shown["author"] = True

print("\ngenericMedicine/name paths:", dict(generic_paths))
print("activeMoiety name paths (under manufacturedProduct/..):", dict(moiety_paths))
print("active ingredients (ACTIB/ACTIM/ACTIR) total:", ing_total, " without any activeMoiety name:", no_moiety)
print("representedOrganization/name paths:", dict(org_paths))
print("first label index with both ACTIB and ACTIM:", both_label)

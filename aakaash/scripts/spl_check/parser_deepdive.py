# SOURCE: NOT IN PAPERS (own diagnostic tooling). Read-only: opens the DailyMed zip, never extracts or modifies it.
# Run with the venv python in isolated mode (-I); see aakaash/scripts/spl_check/README.md
"""Read-only follow-up diagnostics on the same first N labels. usage: <aakaash_dir> <zip> <n>"""
import io, re, sys, zipfile
from collections import Counter
from pathlib import Path
from lxml import etree

aakaash_dir, zip_path, n = sys.argv[1], Path(sys.argv[2]), int(sys.argv[3])
sys.path.insert(0, aakaash_dir)
from medsafe.spl import parse_label, SECTION_CODES, TITLE_FALLBACK, normalize_ingredient

def ln(el): return el.tag.rsplit("}", 1)[-1] if isinstance(el.tag, str) else ""
def child(el, name):
    for c in el:
        if ln(c) == name: return c
def txt(el): return " ".join("".join(el.itertext()).split()) if el is not None else ""

def labels(limit):
    with zipfile.ZipFile(zip_path) as zf:
        k = 0
        for info in zf.infolist():
            if info.is_dir(): continue
            inner = zipfile.ZipFile(io.BytesIO(zf.read(info)))
            for ii in inner.infolist():
                if ii.filename.lower().endswith(".xml"):
                    yield inner.read(ii)
            k += 1
            if k >= limit: return

both = actir_labels = 0
class_combo = Counter(); name_diff = 0; moiety_equal = 0; ex_ing = []
fallback_titles = Counter(); fallback_in_code = {}
zero_secs = []; hl_titles = 0; nl_titles = 0
generic_present = 0; generic_ex = []
prod_counts = Counter(); multi_prod_ex = []
di_missing = []; di_missing_with_interaction_title = 0; di_missing_has_precautions = 0
di_empty = 0; di_text_ex = None
ing_blank_name = 0
for data in labels(n):
    root = etree.fromstring(data)
    rec = parse_label(data)
    # ingredient classes at ingredient level (real structure)
    ings = []
    for el in root.iter():
        if ln(el) == "ingredient" and el.get("classCode") in ("ACTIB", "ACTIM", "ACTIR"):
            sub = child(el, "ingredientSubstance")
            nm = txt(child(sub, "name")) if sub is not None else ""
            am = child(sub, "activeMoiety") if sub is not None else None
            amn = txt(child(am, "name")) if am is not None else ""
            if am is not None and not amn:
                inner = child(am, "activeMoiety"); amn = txt(child(inner, "name")) if inner is not None else ""
            ings.append((el.get("classCode"), nm, amn))
    classes = frozenset(c for c, _, _ in ings)
    class_combo[tuple(sorted(classes))] += 1
    if "ACTIB" in classes and "ACTIM" in classes: both += 1
    if "ACTIR" in classes: actir_labels += 1
    pairs = {(nm.lower(), amn.lower()) for c, nm, amn in ings if c in ("ACTIB", "ACTIM")}
    if any(nm != am for nm, am in pairs if am): name_diff += 1
    if len(ex_ing) < 8 and any(nm != am for nm, am in pairs if am):
        ex_ing.append({"title": rec["title"][:50].replace("\n", " "), "ingredient/name": sorted({p[0] for p in pairs}), "activeMoiety/name": sorted({p[1] for p in pairs})})
    # fallback section titles
    secs = rec["sections"]
    for name, parts in secs.items():
        for p in parts:
            if p["method"] == "title_fallback":
                fallback_titles[(p["code"], name, p["title"][:70])] += 1
    if not secs: zero_secs.append((rec["set_id"], rec["title"][:80], len(data)))
    t = rec["title"]
    if t.lower().startswith("these highlights"): hl_titles += 1
    if "\n" in t: nl_titles += 1
    # generic name
    g = [txt(el) for el in root.iter() if ln(el) == "genericMedicine"]
    g = [x for x in (txt(child(el, "name")) for el in root.iter() if ln(el) == "genericMedicine") if x]
    if g:
        generic_present += 1
        if len(generic_ex) < 4: generic_ex.append(g[:2])
    prod_counts[len(rec["product_names"])] += 1
    if len(rec["product_names"]) > 1 and len(multi_prod_ex) < 4: multi_prod_ex.append(rec["product_names"][:5])
    di = secs.get("drug_interactions")
    if di:
        if all(len(p["text"]) < 5 for p in di): di_empty += 1
        if di_text_ex is None and any(p["method"] == "loinc_code" and 300 < len(p["text"]) < 900 for p in di):
            di_text_ex = next(p["text"] for p in di if p["method"] == "loinc_code" and 300 < len(p["text"]) < 900)
    else:
        di_missing.append(rec["set_id"])
        titles = [txt(child(el, "title")) for el in root.iter() if ln(el) == "section"]
        if any(re.search(r"interaction", t or "", re.I) for t in titles): di_missing_with_interaction_title += 1
        codes = {child(el, "code").get("code") for el in root.iter() if ln(el) == "section" and child(el, "code") is not None}
        if "42232-9" in codes: di_missing_has_precautions += 1

print("ACTIB+ACTIM both present in same label:", both, "| ACTIR present:", actir_labels)
print("active-class combos per label:", dict(class_combo))
print("labels where ingredient/name != activeMoiety/name:", name_diff, "of", n)
print("examples:", *ex_ing, sep="\n   ")
print("\nspl.py title_fallback matches (code, assigned section, section title):")
for k, v in fallback_titles.most_common(): print("  ", v, k)
print("\nlabels with zero parsed sections:", zero_secs)
print("titles starting 'These highlights':", hl_titles, "| titles containing newline:", nl_titles)
print("genericMedicine/name present:", generic_present, "of", n, "e.g.", generic_ex)
print("product_names per label distribution:", dict(sorted(prod_counts.items())), "| multi examples:", multi_prod_ex)
print("\nlabels WITHOUT spl.py drug_interactions:", len(di_missing))
print("   of those, with some section titled *interaction*:", di_missing_with_interaction_title)
print("   of those, having a PRECAUTIONS (42232-9) section:", di_missing_has_precautions)
print("drug_interactions present but empty text:", di_empty)
print("\nSample real Drug Interactions text (loinc_code match):\n", di_text_ex)

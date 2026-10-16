# SOURCE: NOT IN PAPERS (own diagnostic tooling). Read-only: opens the DailyMed zip, never extracts or modifies it.
# Run with the venv python in isolated mode (-I); see aakaash/scripts/spl_check/README.md
"""Phase-0b parser check on the first N labels of one DailyMed zip. Read-only.
usage: parser_check.py <repo_aakaash_dir> <zip> <n> <parser|survey> <out_json>
"""
import ctypes, ctypes.wintypes as wt, io, json, re, statistics, sys, time, zipfile
from collections import Counter
from pathlib import Path

aakaash_dir, zip_path, n, mode, out_json = sys.argv[1], Path(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5]
sys.path.insert(0, aakaash_dir)  # our own code under review

class PMC(ctypes.Structure):
    _fields_ = [("cb", wt.DWORD), ("PageFaultCount", wt.DWORD), ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t), ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t), ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t), ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t)]

def peak_mb():
    c = PMC(); c.cb = ctypes.sizeof(PMC)
    k = ctypes.WinDLL("kernel32", use_last_error=True); p = ctypes.WinDLL("psapi", use_last_error=True)
    k.GetCurrentProcess.restype = wt.HANDLE
    p.GetProcessMemoryInfo.argtypes = [wt.HANDLE, ctypes.POINTER(PMC), wt.DWORD]
    p.GetProcessMemoryInfo(k.GetCurrentProcess(), ctypes.byref(c), c.cb)
    return c.PeakWorkingSetSize / 1e6, c.WorkingSetSize / 1e6

def labels_raw(limit):
    """First `limit` XML members, same order spl._walk_zip uses (outer order, one XML per inner zip)."""
    with zipfile.ZipFile(zip_path) as zf:
        k = 0
        for info in zf.infolist():
            if info.is_dir() or not info.filename.lower().endswith(".zip"):
                continue
            inner = zipfile.ZipFile(io.BytesIO(zf.read(info)))
            for ii in inner.infolist():
                if ii.filename.lower().endswith(".xml"):
                    yield info.filename, ii.filename, inner.read(ii)
            k += 1
            if k >= limit:
                return

if mode == "parser":
    from medsafe.spl import iter_part, SECTION_CODES
    from medsafe.chunking import chunk_label
    stats = Counter(); recs = []
    t0 = time.perf_counter()
    for rec in iter_part(zip_path, stats, max_labels=n):
        recs.append(rec)
    t_parse = time.perf_counter() - t0
    t1 = time.perf_counter()
    chunks = Counter(); chunk_tot = 0; per_label = []
    for rec in recs:
        c = 0
        for ch in chunk_label(rec):
            chunks[ch["section"]] += 1; c += 1
        per_label.append(c); chunk_tot += c
    t_chunk = time.perf_counter() - t1
    pk, cur = peak_mb()
    sec_present = Counter(); code_counts = Counter(); sec_chars = {}
    for r in recs:
        for name, parts in r["sections"].items():
            sec_present[name] += 1
            sec_chars.setdefault(name, []).extend(len(p["text"]) for p in parts)
            for p in parts:
                code_counts[(p["code"], name, p["method"])] += 1
    out = {
        "stats": dict(stats), "labels": len(recs), "t_parse_s": t_parse, "t_chunk_s": t_chunk,
        "peak_ws_mb": pk, "end_ws_mb": cur, "chunks_total": chunk_tot, "chunks_by_section": dict(chunks),
        "chunks_per_label_median": statistics.median(per_label), "chunks_per_label_max": max(per_label),
        "labels_with_section": dict(sec_present),
        "code_method_counts": [[list(k), v] for k, v in code_counts.most_common()],
        "section_chars_median": {k: statistics.median(v) for k, v in sec_chars.items()},
        "ingredient_source": dict(Counter(r["ingredient_source"] for r in recs)),
        "n_ingredients_dist": dict(Counter(len(r["ingredients"]) for r in recs)),
        "empty_product_names": sum(1 for r in recs if not r["product_names"]),
        "missing_set_id": sum(1 for r in recs if not r["set_id"]),
        "labels_with_zero_sections": sum(1 for r in recs if not r["sections"]),
        "section_methods_total": dict(sum((Counter(r["section_methods"]) for r in recs), Counter())),
        "samples": [{k: (v if k != "sections" else {s: [len(p["text"]) for p in ps] for s, ps in v.items()})
                     for k, v in r.items() if k not in ("source", "member")} for r in recs[:4]],
    }
else:
    from lxml import etree
    def ln(el): return el.tag.rsplit("}", 1)[-1] if isinstance(el.tag, str) else ""
    def child(el, name):
        for c in el:
            if ln(c) == name: return c
    fails = 0; n_lab = 0
    sec_label_count = Counter(); sec_total = Counter(); sec_names = {}; top_level = Counter()
    doc_codes = Counter(); ing_class = Counter(); ing_paths = Counter(); manuf = Counter(); manuf_missing = 0
    name_paths = Counter(); active_moiety_present = 0; root_tags = Counter(); ns = Counter()
    ndc_missing = 0; ex_manuf = []; ex_prodname = []; di_titles = Counter(); di_codes_by_name = Counter()
    nested_sec_depth = Counter(); sample_ing = []
    t0 = time.perf_counter()
    for outer, member, data in labels_raw(n):
        try:
            root = etree.fromstring(data)
        except Exception:
            fails += 1; continue
        n_lab += 1; root_tags[ln(root)] += 1
        ns[etree.QName(root).namespace] += 1
        dc = child(root, "code"); doc_codes[(dc.get("code"), dc.get("displayName")) if dc is not None else None] += 1
        seen = set()
        def walk(el, depth):
            for c in el:
                if not isinstance(c.tag, str): continue
                if ln(c) == "section":
                    code_el = child(c, "code"); title_el = child(c, "title")
                    code = code_el.get("code") if code_el is not None else None
                    disp = code_el.get("displayName") if code_el is not None else None
                    title = " ".join("".join(title_el.itertext()).split()) if title_el is not None else ""
                    sec_total[code] += 1; seen.add(code)
                    sec_names.setdefault(code, Counter())[disp] += 1
                    if depth == 0: top_level[code] += 1
                    nested_sec_depth[depth] += 1
                    if disp and "INTERACTION" in disp.upper():
                        di_codes_by_name[(code, disp, depth)] += 1; di_titles[title] += 1
                    walk(c, depth + 1)
                else:
                    walk(c, depth)
        sb = None
        for el in root.iter():
            if ln(el) == "structuredBody": sb = el; break
        if sb is not None: walk(sb, 0)
        for code in seen: sec_label_count[code] += 1
        # ingredients and product names, with their real paths
        for el in root.iter():
            nm = ln(el)
            if nm == "ingredient":
                ing_class[el.get("classCode")] += 1
                sub = child(el, "ingredientSubstance")
                if sub is not None:
                    path = "ingredient/ingredientSubstance"
                    if child(sub, "activeMoiety") is not None: path += "/activeMoiety"; active_moiety_present += 1
                    ing_paths[(el.get("classCode"), path)] += 1
            elif nm == "manufacturedProduct":
                nme = child(el, "name")
                mm = child(el, "manufacturedMedicine")
                name_paths[("manufacturedProduct/name", nme is not None and bool(nme.text and nme.text.strip()))] += 1
                if mm is not None:
                    n2 = child(mm, "name")
                    name_paths[("manufacturedProduct/manufacturedMedicine/name", n2 is not None and bool(n2.text and n2.text.strip()))] += 1
                    if n2 is not None and n2.text and len(ex_prodname) < 3: ex_prodname.append(n2.text.strip())
        # manufacturer: author/assignedEntity/representedOrganization/name
        org = None
        a = child(root, "author")
        if a is not None:
            ae = child(a, "assignedEntity")
            if ae is not None:
                ro = child(ae, "representedOrganization")
                if ro is not None: org = child(ro, "name")
        if org is not None and org.text and org.text.strip():
            manuf[org.text.strip()] += 1
            if len(ex_manuf) < 3: ex_manuf.append(org.text.strip())
        else:
            manuf_missing += 1
    t_survey = time.perf_counter() - t0
    pk, cur = peak_mb()
    out = {
        "labels_survey": n_lab, "survey_failures": fails, "t_survey_s": t_survey, "peak_ws_mb": pk,
        "root_tags": dict(root_tags), "namespaces": dict(ns),
        "doc_type_codes": [[list(k) if k else None, v] for k, v in doc_codes.most_common()],
        "sections_all_depths": [{"code": c, "labels_with": sec_label_count[c], "occurrences": sec_total[c],
                                 "top_level_occurrences": top_level.get(c, 0),
                                 "displayNames": dict(sec_names[c])} for c, _ in sec_label_count.most_common()],
        "section_depth_counts": dict(nested_sec_depth),
        "ingredient_classCodes": dict(ing_class), "ingredient_paths": [[list(k), v] for k, v in ing_paths.most_common()],
        "product_name_paths": [[list(k), v] for k, v in name_paths.items()],
        "manufacturer_found": sum(manuf.values()), "manufacturer_missing": manuf_missing,
        "manufacturer_distinct": len(manuf), "manufacturer_examples": ex_manuf, "product_name_examples": ex_prodname,
        "interaction_sections": [[list(k), v] for k, v in di_codes_by_name.most_common()],
        "interaction_titles": dict(di_titles.most_common(10)),
    }
Path(out_json).write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
print(json.dumps(out, indent=1, default=str)[:20000])

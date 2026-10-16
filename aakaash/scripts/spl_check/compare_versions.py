# SOURCE: NOT IN PAPERS (own diagnostic tooling). Read-only: opens the DailyMed zip, never extracts or modifies it.
"""Run two versions of spl.py on the same first N labels and print before/after counts.
usage: compare_versions.py <old_spl.py> <new_spl.py> <zip> <n>
(<new_spl.py> must live in <aakaash>/medsafe/ so medsafe.chunking can be imported.)"""
import importlib.util
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

old_path, new_path, zip_path, n = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), int(sys.argv[4])
sys.path.insert(0, str(new_path.resolve().parents[1]))
from medsafe.chunking import chunk_text  # noqa: E402


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(mod):
    stats, recs = Counter(), []
    t = time.perf_counter()
    for rec in mod.iter_part(zip_path, stats, max_labels=n):
        recs.append(rec)
    return recs, stats, time.perf_counter() - t


old_mod, new_mod = load(old_path, "spl_old"), load(new_path, "spl_new")
old_recs, old_stats, t_old = run(old_mod)
new_recs, new_stats, t_new = run(new_mod)
assert [r["set_id"] for r in old_recs] == [r["set_id"] for r in new_recs], "different labels"
print(f"labels: before {len(old_recs)}, after {len(new_recs)}; parse time before {t_old:.2f}s, after {t_new:.2f}s")
print("stats before:", dict(old_stats))
print("stats after: ", dict(new_stats))


def section_table(recs):
    labels, chunks, chars = Counter(), Counter(), defaultdict(list)
    for r in recs:
        for sec, parts in r["sections"].items():
            labels[sec] += 1
            chars[sec].append(sum(len(p["text"]) for p in parts))
            for p in parts:
                chunks[sec] += len(chunk_text(p["text"]))
    return labels, chunks, chars


ol, oc, _ = section_table(old_recs)
nl, nc, nchars = section_table(new_recs)
print("\nsection | labels before -> after | chunks before -> after")
for sec in sorted(set(ol) | set(nl)):
    print(f"  {sec:22s} {ol[sec]:4d} -> {nl[sec]:4d}   {oc[sec]:5d} -> {nc[sec]:5d}")
print(f"  {'TOTAL chunks':22s} {'':>11s}   {sum(oc.values()):5d} -> {sum(nc.values()):5d}")


def parts(recs, how=None):
    out = []
    for r in recs:
        for sec, ps in r["sections"].items():
            for p in ps:
                if how is None or p["method"] == how:
                    out.append((r["set_id"], sec, p["code"], p["title"][:70], p["method"], p["text"]))
    return out


for label, recs in (("BEFORE", old_recs), ("AFTER", new_recs)):
    fb = parts(recs, "title_fallback")
    print(f"\ntitle_fallback sections {label}: {len(fb)}")
    for k, c in Counter((a[1], a[2], a[3]) for a in fb).most_common():
        print(f"   {c} x  -> {k[0]:22s} code={k[1]}  title={k[2]!r}")

old_keys = Counter((a[0], a[1], a[5]) for a in parts(old_recs))
new_keys = Counter((a[0], a[1], a[5]) for a in parts(new_recs))
removed = old_keys - new_keys
added = new_keys - old_keys
meta = {(a[0], a[1], a[5]): a for a in parts(old_recs) + parts(new_recs)}
print(f"\nsection blocks REMOVED by the fixes: {sum(removed.values())}")
for k in removed:
    a = meta[k]; print(f"   {a[1]:22s} code={a[2]} method={a[4]} title={a[3]!r}")
print(f"section blocks ADDED by the fixes: {sum(added.values())} (by section: "
      f"{dict(Counter(k[1] for k in added.elements()))})")

# regression guard: every block that was loinc_code-matched before must still be there unchanged
lost = [a for a in parts(old_recs, "loinc_code") if (a[0], a[1], a[5]) not in new_keys]
print(f"\nREGRESSION CHECK: code-matched blocks before that are missing or changed after: {len(lost)}")
for a in lost[:5]:
    print("   ", a[:5])

di_old = {r["set_id"] for r in old_recs if "drug_interactions" in r["sections"]}
di_new = {r["set_id"] for r in new_recs if "drug_interactions" in r["sections"]}
print(f"\nlabels with drug_interactions: before {len(di_old)}, after {len(di_new)}; lost {len(di_old - di_new)}, gained {len(di_new - di_old)}")
code_di = {r["set_id"] for r in new_recs if any(p["method"] == "loinc_code" for p in r["sections"].get("drug_interactions", []))}
print(f"   of the {len(di_new)} after: {len(code_di)} by LOINC code 34073-7, {len(di_new - code_di)} only by (anchored) title")

prec = [r for r in new_recs if "precautions" in r["sections"]]
pchars = [sum(len(p["text"]) for p in r["sections"]["precautions"]) for r in prec]
print(f"\nprecautions (42232-9): labels {len(prec)}, blocks {sum(len(r['sections']['precautions']) for r in prec)}, "
      f"median chars {int(statistics.median(pchars)) if pchars else '-'}, chunks {nc['precautions']}; "
      f"sections with only captured subsections (not recorded): {new_stats.get('note_precautions_only_subsections', 0)}")
dup = 0
for r in prec:
    ptxt = " ".join(p["text"] for p in r["sections"]["precautions"])
    for sec in ("drug_interactions", "specific_populations"):
        for p in r["sections"].get(sec, []):
            if p["code"] and p["code"] != "43684-0" and len(p["text"]) > 80 and p["text"] in ptxt:
                dup += 1
print(f"   duplication check: captured subsection texts (>80 chars) found verbatim inside precautions text: {dup}")

ing_diff = sum(1 for r in new_recs if r["ingredients"] != r["active_moieties"])
ing_set = {i for r in new_recs for i in r["ingredients"]}
moi_set = {i for r in new_recs for i in r["active_moieties"]}
print(f"\nlabels where ingredient strings != active moiety strings: {ing_diff} of {len(new_recs)}")
print(f"distinct ingredient strings {len(ing_set)} -> distinct active moiety strings {len(moi_set)}")
print(f"labels with an ingredient lacking a moiety name: {new_stats.get('labels_with_ingredient_without_moiety', 0)}")
merge = defaultdict(set)
for r in new_recs:
    if len(r["ingredients"]) == 1 and len(r["active_moieties"]) == 1:
        merge[r["active_moieties"][0]].add(r["ingredients"][0])
ex = [(m, sorted(v)) for m, v in merge.items() if len(v) > 1]
print(f"single-ingredient moieties reached by more than one ingredient string: {len(ex)}; examples:")
for m, v in ex[:6]:
    print(f"   {m!r}  <-  {v}")


def shared(key):
    groups = defaultdict(list)
    for r in new_recs:
        if r[key]:
            groups[tuple(r[key])].append(r["set_id"])
    return sum(len(v) for v in groups.values() if len(v) > 1), sum(1 for v in groups.values() if len(v) > 1)


a, b = shared("ingredients"), shared("active_moieties")
print(f"labels that share their full ingredient set with at least one other label (within these {len(new_recs)}): "
      f"by ingredient string {a[0]} (in {a[1]} groups) -> by active moiety {b[0]} (in {b[1]} groups)")
changed = [(o, nw) for o, nw in zip(old_recs, new_recs) if o["ingredients"] != nw["ingredients"]]
print(f"\nlabels whose ingredient set changed between the two versions: {len(changed)} of {len(new_recs)}")
for o, nw in changed:
    print(f"   {nw['set_id']} | {(nw['product_names'] or ['?'])[0]} | {o['title'][:45]!r}")
    print(f"        old set ({o['ingredient_source']}): {o['ingredients']}")
    print(f"        new set ({nw['ingredient_source']}): {nw['ingredients']}")
print("old ingredient_source:", dict(Counter(r["ingredient_source"] for r in old_recs)))
print("ingredient_source:", dict(Counter(r["ingredient_source"] for r in new_recs)))
if len(new_recs) > 76:
    r = new_recs[76]
    print(f"label #76 (has both ACTIB and ACTIM per xml_paths.py): source={r['ingredient_source']}, "
          f"ingredients={r['ingredients_raw']}, moieties={r['active_moieties_raw']}")

gn = [r for r in new_recs if r["generic_names"]]
mf = Counter(r["manufacturer"] for r in new_recs if r["manufacturer"])
print(f"\ngeneric_names: labels with >=1: {len(gn)} of {len(new_recs)}; examples: {[r['generic_names'] for r in gn[:4]]}")
print(f"labels with more than one distinct generic name: {sum(1 for r in new_recs if len(r['generic_names']) > 1)}")
print(f"manufacturer: labels with one: {sum(mf.values())} of {len(new_recs)}; distinct {len(mf)}; top: {mf.most_common(3)}")

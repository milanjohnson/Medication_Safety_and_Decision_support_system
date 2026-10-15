# SOURCE: UNTESTED on real files. Element names (<Label drug>, <Text><Section name id>,
# <Mentions>, <Relations>, <Reactions>) are from the user's description of TAC 2017, a guess
# until real files arrive. FROM PAPERS: P1 describes the TAC 2017 data (101 train, 99 test,
# 2,208 unannotated labels) and the sections Adverse Reactions, Warnings and Precautions,
# Boxed Warnings. The parser itself is NOT IN PAPERS.
"""TAC 2017 ADR label parser. Keeps every attribute so format differences are visible."""
from __future__ import annotations

from collections import Counter
from pathlib import Path

from lxml import etree

SPLIT_DIR_NAMES = ("train_xml", "gold_xml", "unannotated_xml")


def parse_tac_label(path: Path) -> dict:
    root = etree.parse(str(path), etree.XMLParser(recover=True)).getroot()
    rec = {
        "file": path.name, "root_tag": root.tag, "attrs": dict(root.attrib),
        "sections": [], "mentions": [], "relations": [], "reactions": [],
    }
    text_el = root.find("Text")
    if text_el is not None:
        for sec in text_el.findall("Section"):
            rec["sections"].append({
                "id": sec.get("id"), "name": (sec.get("name") or "").strip().lower(),
                "attrs": dict(sec.attrib), "text": sec.text or "",
            })
    for m in root.iterfind(".//Mentions/Mention"):
        rec["mentions"].append(dict(m.attrib))
    for r in root.iterfind(".//Relations/Relation"):
        rec["relations"].append(dict(r.attrib))
    for r in root.iterfind(".//Reactions/Reaction"):
        item = dict(r.attrib)
        item["normalizations"] = [dict(n.attrib) for n in r.findall("Normalization")]
        rec["reactions"].append(item)
    return rec


def split_name(path: Path, root: Path) -> str:
    for part in path.relative_to(root).parts[:-1]:
        if part.lower() in SPLIT_DIR_NAMES:
            return part.lower()
    return "unclassified"


def iter_tac(root: Path, stats: Counter | None = None):
    """Yield (split, record) for every XML under root."""
    stats = stats if stats is not None else Counter()
    for path in sorted(root.rglob("*.xml")):
        split = split_name(path, root)
        try:
            rec = parse_tac_label(path)
        except (etree.XMLSyntaxError, OSError):
            stats["parse_failures"] += 1
            continue
        rec["split"] = split
        yield split, rec


def summarize(root: Path) -> dict:
    """Real counts only: labels per split, section names, mention/relation types, and any
    attribute or tag names we did not expect (format differences vs. the guess)."""
    out = {"splits": Counter(), "section_names": Counter(), "mention_types": Counter(),
           "relation_types": Counter(), "root_attrs": Counter(), "root_tags": Counter(),
           "mention_attr_keys": Counter(), "labels_without_text": 0, "parse_failures": 0,
           "reactions": 0, "mentions": 0, "relations": 0, "sections": 0}
    stats: Counter = Counter()
    for split, rec in iter_tac(root, stats):
        out["splits"][split] += 1
        out["root_tags"][rec["root_tag"]] += 1
        out["root_attrs"].update(rec["attrs"].keys())
        if not rec["sections"]:
            out["labels_without_text"] += 1
        for s in rec["sections"]:
            out["section_names"][s["name"]] += 1
            out["sections"] += 1
        for m in rec["mentions"]:
            out["mention_types"][m.get("type", "?")] += 1
            out["mention_attr_keys"].update(m.keys())
            out["mentions"] += 1
        for r in rec["relations"]:
            out["relation_types"][r.get("type", "?")] += 1
            out["relations"] += 1
        out["reactions"] += len(rec["reactions"])
    out["parse_failures"] = stats["parse_failures"]
    return {k: (dict(v) if isinstance(v, Counter) else v) for k, v in out.items()}

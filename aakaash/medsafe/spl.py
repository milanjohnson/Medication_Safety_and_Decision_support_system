# SOURCE: UNTESTED on real files. SPL structure (HL7 v3 namespace, <section><code code=LOINC>,
# <manufacturedProduct>/<ingredient classCode=ACTIB|ACTIM>) and the LOINC section codes below are
# from general knowledge, NOT verified: UNVERIFIED, check against real DailyMed files.
# FROM PAPERS: P1 uses DailyMed SPL XML and the sections Adverse Reactions, Warnings and
# Precautions, Boxed Warnings, Drug Interactions. Indications, Contraindications and
# Use in Specific Populations come from the task spec (NOT IN PAPERS). Parser is NOT IN PAPERS.
"""DailyMed SPL parser that reads straight from (possibly nested) zips."""
from __future__ import annotations

import io
import re
import zipfile
from collections import Counter
from pathlib import Path

from lxml import etree

SECTION_CODES = {  # UNVERIFIED LOINC codes
    "34067-9": "indications",
    "34070-3": "contraindications",
    "34071-1": "warnings_precautions",  # legacy "Warnings"; merged with W&P (own choice)
    "43685-7": "warnings_precautions",
    "34066-1": "boxed_warning",
    "34084-4": "adverse_reactions",
    "34073-7": "drug_interactions",
    "43684-0": "specific_populations",
    "42228-7": "specific_populations",  # pregnancy
    "34081-0": "specific_populations",  # pediatric use
    "34082-8": "specific_populations",  # geriatric use
}
TITLE_FALLBACK = [  # used only when the code is missing or unmapped (heuristic)
    (re.compile(r"\bboxed warning", re.I), "boxed_warning"),
    (re.compile(r"\bcontraindications?\b", re.I), "contraindications"),
    (re.compile(r"\badverse reactions?\b", re.I), "adverse_reactions"),
    (re.compile(r"\bdrug interactions?\b", re.I), "drug_interactions"),
    (re.compile(r"\bwarnings?( and precautions)?\b", re.I), "warnings_precautions"),
    (re.compile(r"\bindications?\b", re.I), "indications"),
    (re.compile(r"\buse in specific populations\b", re.I), "specific_populations"),
]
CANONICAL_SECTIONS = ("indications", "contraindications", "warnings_precautions",
                      "boxed_warning", "adverse_reactions", "drug_interactions",
                      "specific_populations")
_NEWLINE_AFTER = {"paragraph", "item", "tr", "br", "list", "caption", "title"}
MAX_ZIP_DEPTH = 3


def _ln(el) -> str:
    tag = el.tag
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def _text_of(el) -> str:
    """Text of an element subtree; newline after block tags, space after table cells."""
    parts = []

    def walk(node):
        if node.text:
            parts.append(node.text)
        for child in node:
            if isinstance(child.tag, str):
                walk(child)
            if child.tail:
                parts.append(child.tail)
        name = _ln(node)
        if name in _NEWLINE_AFTER:
            parts.append("\n")
        elif name in ("td", "th"):
            parts.append(" ")

    walk(el)
    return re.sub(r"[ \t\r\f\v]+", " ", re.sub(r"\n\s*\n+", "\n", "".join(parts))).strip()


def _first_child(el, name):
    for c in el:
        if _ln(c) == name:
            return c
    return None


def normalize_ingredient(name: str) -> str:
    """Basic normalisation only (lowercase, drop parentheticals, collapse spaces).
    Salt-stripping is NOT done here (Phase 2 decision)."""
    name = re.sub(r"\(.*?\)", " ", name.lower())
    return re.sub(r"\s+", " ", name).strip()


def _collect_sections(el, out, methods):
    """DFS over <section>. A matched section is taken whole (subsections folded in)."""
    for child in el:
        if not isinstance(child.tag, str):
            continue
        if _ln(child) == "section":
            code_el = _first_child(child, "code")
            code = code_el.get("code") if code_el is not None else None
            title_el = _first_child(child, "title")
            title = _text_of(title_el) if title_el is not None else ""
            canon, how = SECTION_CODES.get(code or ""), "loinc_code"
            if canon is None and title:
                for rx, name in TITLE_FALLBACK:
                    if rx.search(title):
                        canon, how = name, "title_fallback"
                        break
            if canon is not None:
                out.setdefault(canon, []).append(
                    {"code": code, "title": title, "text": _text_of(child), "method": how})
                methods[how] += 1
                continue  # do not descend into a matched section
        _collect_sections(child, out, methods)


def parse_label(data: bytes, source: str = "", member: str = "") -> dict:
    """Parse one SPL XML. Raises on malformed XML or missing structure."""
    root = etree.fromstring(data)
    set_id_el = _first_child(root, "setId")
    set_id = set_id_el.get("root") if set_id_el is not None else None
    title_el = _first_child(root, "title")
    ver_el = _first_child(root, "versionNumber")
    eff_el = _first_child(root, "effectiveTime")
    actib, actim, moieties, names = [], [], [], []
    for el in root.iter():
        n = _ln(el)
        if n == "ingredient":
            sub = _first_child(el, "ingredientSubstance")
            nm = _first_child(sub, "name") if sub is not None else None
            if nm is not None and nm.text:
                cls = el.get("classCode", "")
                if cls == "ACTIB":
                    actib.append(nm.text.strip())
                elif cls == "ACTIM":
                    actim.append(nm.text.strip())
        elif n == "activeMoiety":
            nm = _first_child(el, "name")
            if nm is not None and nm.text:
                moieties.append(nm.text.strip())
        elif n == "manufacturedProduct":
            nm = _first_child(el, "name")
            if nm is not None and nm.text:
                names.append(nm.text.strip())
    ingredients = actib or actim or moieties
    sections: dict = {}
    methods: Counter = Counter()
    body = None
    for el in root.iter():
        if _ln(el) == "structuredBody":
            body = el
            break
    if body is not None:
        _collect_sections(body, sections, methods)
    return {
        "set_id": set_id,
        "title": _text_of(title_el) if title_el is not None else "",
        "version": ver_el.get("value") if ver_el is not None else None,
        "effective_time": eff_el.get("value") if eff_el is not None else None,
        "product_names": sorted(set(names)),
        "ingredients": sorted({normalize_ingredient(i) for i in ingredients if i}),
        "ingredients_raw": sorted(set(ingredients)),
        "ingredient_source": "ACTIB" if actib else ("ACTIM" if actim else
                                                     ("activeMoiety" if moieties else "none")),
        "sections": sections,
        "section_methods": dict(methods),
        "source": source, "member": member,
    }


def _walk_zip(zf: zipfile.ZipFile, source: str, depth: int, stats: Counter):
    for info in zf.infolist():
        if info.is_dir():
            continue
        name, low = info.filename, info.filename.lower()
        if low.endswith(".xml"):
            yield source, name, zf.read(info)
        elif low.endswith(".zip"):
            if depth >= MAX_ZIP_DEPTH:
                stats["nested_zip_too_deep"] += 1
                continue
            try:
                inner = zipfile.ZipFile(io.BytesIO(zf.read(info)))
            except zipfile.BadZipFile:
                stats["bad_nested_zip"] += 1
                continue
            yield from _walk_zip(inner, f"{source}!{name}", depth + 1, stats)
        else:
            stats["other_member_" + (Path(low).suffix or "noext")] += 1


def iter_part(zip_path: Path, stats: Counter, max_labels: int | None = None):
    """Yield parsed label dicts for one DailyMed zip. Failures are counted, never silent."""
    n = 0
    with zipfile.ZipFile(zip_path) as zf:
        for source, member, data in _walk_zip(zf, zip_path.name, 1, stats):
            try:
                rec = parse_label(data, source, member)
            except Exception as exc:  # noqa: BLE001 - counted and reported
                stats["parse_failures"] += 1
                stats["parse_failure_" + type(exc).__name__] += 1
                continue
            if not rec["set_id"]:
                stats["missing_set_id"] += 1
            stats["labels_parsed"] += 1
            yield rec
            n += 1
            if max_labels is not None and n >= max_labels:
                return


def iter_parts(data_dir: Path, stats_by_part: dict | None = None,
               max_labels_per_part: int | None = None):
    """Loop over whichever dm_spl_release_human_rx_part*.zip files exist (sorted)."""
    for zp in sorted(data_dir.glob("*.zip")):
        st = Counter()
        if stats_by_part is not None:
            stats_by_part[zp.name] = st
        yield from iter_part(zp, st, max_labels_per_part)

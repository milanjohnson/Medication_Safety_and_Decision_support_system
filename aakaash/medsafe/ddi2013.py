# SOURCE: UNTESTED on real files. XML layout (<sentence>/<entity>/<pair ddi type>) is from the
# user's description of the DDI Extraction 2013 corpus, treated as a guess until real files arrive.
# FROM PAPERS: P6 (Jia et al.) uses DDI Extraction 2013 with entity markers and four positive
# classes. The marker strings, the dev-split method and the group-aware stratification are
# NOT IN PAPERS (UNVERIFIED: check 3.pdf for Jia's exact marker format).
"""DDI Extraction 2013 parser: one instance per drug pair per sentence."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from lxml import etree

POSITIVE_CLASSES = ("effect", "mechanism", "advise", "int")
NEGATIVE = "false"
ALL_LABELS = POSITIVE_CLASSES + (NEGATIVE,)
DEFAULT_MARKERS = (("<e1>", "</e1>"), ("<e2>", "</e2>"))  # NOT IN PAPERS


def parse_offsets(value: str) -> list[tuple[int, int]]:
    """'0-9' -> [(0, 10)]; '3-8;12-15' -> [(3, 9), (12, 16)]. End is exclusive."""
    spans = []
    for part in value.split(";"):
        start, end = part.strip().split("-")
        spans.append((int(start), int(end) + 1))
    return spans


def mark_pair(text, span1, span2, markers=DEFAULT_MARKERS):
    """Wrap the two spans in entity markers. Spans must not overlap."""
    items = [(span1, markers[0]), (span2, markers[1])]
    items.sort(key=lambda x: x[0][0], reverse=True)  # insert right to left
    for (start, end), (open_m, close_m) in items:
        text = text[:start] + open_m + text[start:end] + close_m + text[end:]
    return text


def _source_of(doc_id: str, path: Path) -> str:
    probe = (doc_id + str(path)).lower()
    if "drugbank" in probe:
        return "drugbank"
    if "medline" in probe:
        return "medline"
    return "unknown"


def parse_ddi_file(path: Path, stats: Counter, markers=DEFAULT_MARKERS):
    """Yield one dict per drug pair. Counts every skip reason in `stats`."""
    try:
        root = etree.parse(str(path)).getroot()
    except (etree.XMLSyntaxError, OSError):
        stats["file_parse_failures"] += 1
        return
    doc_id = root.get("id", path.stem)
    stats["documents"] += 1
    source = _source_of(doc_id, path)
    doc_pairs = 0
    for sent in root.iter("sentence"):
        stats["sentences"] += 1
        text = sent.get("text", "")
        ents = {}
        for ent in sent.findall("entity"):
            stats["entities"] += 1
            try:
                spans = parse_offsets(ent.get("charOffset", ""))
            except ValueError:
                stats["bad_char_offset"] += 1
                continue
            if len(spans) > 1:
                stats["discontiguous_entities"] += 1
            span = spans[0]  # first fragment only
            if text[span[0]:span[1]] != ent.get("text", ""):
                stats["entity_text_mismatch"] += 1
            ents[ent.get("id")] = (ent.get("text", ""), span, ent.get("type", ""))
        for pair in sent.findall("pair"):
            stats["pairs"] += 1
            doc_pairs += 1
            e1, e2 = ents.get(pair.get("e1")), ents.get(pair.get("e2"))
            if e1 is None or e2 is None:
                stats["skipped_unknown_entity"] += 1
                continue
            ddi = (pair.get("ddi") or "").lower()
            if ddi == "false":
                label = NEGATIVE
            elif ddi == "true":
                label = (pair.get("type") or "").lower()
                if label not in POSITIVE_CLASSES:
                    # real corpus has one ddi="true" pair with no type (d236.s29.p0): count it
                    # in the skip counter and treat it as false (user decision)
                    stats["true_without_valid_type_treated_false"] += 1
                    label = NEGATIVE
            else:
                stats["skipped_bad_ddi_attr"] += 1
                continue
            (s1, s2) = e1[1], e2[1]
            if s1[0] < s2[1] and s2[0] < s1[1]:
                stats["skipped_overlapping_entities"] += 1
                continue
            stats["instances"] += 1
            yield {
                "doc_id": doc_id, "sent_id": sent.get("id"), "pair_id": pair.get("id"),
                "source": source, "e1_id": pair.get("e1"), "e2_id": pair.get("e2"),
                "e1_text": e1[0], "e2_text": e2[0], "e1_type": e1[2], "e2_type": e2[2],
                "text": text, "marked_text": mark_pair(text, s1, s2, markers),
                "label": label,
            }
    if doc_pairs == 0:
        stats["documents_without_pairs"] += 1


def classify_files(root: Path) -> dict[str, list[Path]]:
    """Assign each XML under root to 'train' or 'test' by folder names. Never guesses:
    files matching neither (or both) go to 'unclassified' and are reported."""
    out = {"train": [], "test": [], "excluded_ner": [], "unclassified": []}
    for path in sorted(root.rglob("*.xml")):
        parts = [p.lower() for p in path.relative_to(root).parts[:-1]]
        if any("drugner" in p for p in parts):  # DrugNER task test: all pairs false, not used
            out["excluded_ner"].append(path)
            continue
        is_train = any("train" in p for p in parts)
        is_test = any("test" in p for p in parts)
        if is_train and not is_test:
            out["train"].append(path)
        elif is_test and not is_train:
            out["test"].append(path)
        else:
            out["unclassified"].append(path)
    return out


def load_split(files: list[Path], markers=DEFAULT_MARKERS):
    stats: Counter = Counter()
    rows = []
    for f in files:
        rows.extend(parse_ddi_file(f, stats, markers))
    return rows, stats


def make_dev_split(rows, dev_frac=0.1, seed=13):
    """Stratified-by-label dev set carved from train, grouped by document so sentences of one
    document never straddle train/dev. NOT IN PAPERS (own design)."""
    from sklearn.model_selection import StratifiedGroupKFold

    n_splits = max(2, round(1 / dev_frac))
    labels = [r["label"] for r in rows]
    groups = [r["doc_id"] for r in rows]
    skf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    _, dev_idx = next(iter(skf.split(rows, labels, groups)))
    dev_set = set(dev_idx.tolist())
    train = [r for i, r in enumerate(rows) if i not in dev_set]
    dev = [r for i, r in enumerate(rows) if i in dev_set]
    return train, dev


def write_jsonl(rows, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def build_dataset(root: Path, out_dir: Path, dev_frac=0.1, seed=13, markers=DEFAULT_MARKERS):
    """Parse train/test under `root`, carve dev from train, write jsonl, return stats dict."""
    files = classify_files(root)
    train_all, train_stats = load_split(files["train"], markers)
    test, test_stats = load_split(files["test"], markers)
    train, dev = make_dev_split(train_all, dev_frac, seed) if train_all else ([], [])
    for name, rows in (("train", train), ("dev", dev), ("test", test)):
        write_jsonl(rows, out_dir / f"{name}.jsonl")
    return {
        "files": {k: len(v) for k, v in files.items()},
        "unclassified_examples": [str(p.relative_to(root)) for p in files["unclassified"][:5]],
        "parse_stats": {"train": dict(train_stats), "test": dict(test_stats)},
        "label_counts": {
            "train": dict(Counter(r["label"] for r in train)),
            "dev": dict(Counter(r["label"] for r in dev)),
            "test": dict(Counter(r["label"] for r in test)),
        },
        "source_counts": {
            "train": dict(Counter(r["source"] for r in train)),
            "dev": dict(Counter(r["source"] for r in dev)),
            "test": dict(Counter(r["source"] for r in test)),
        },
        "dev_frac": dev_frac, "seed": seed, "markers": [list(m) for m in markers],
    }


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    print(json.dumps(build_dataset(a.root, a.out), indent=2))

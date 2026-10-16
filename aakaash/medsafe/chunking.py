# SOURCE: chunk size 512 is the task spec default; P3 (DrugGPT) reports retriever chunk size 512
# (unit not stated in the facts list: UNVERIFIED: check 7.pdf). P2 uses 1,100 / 140 characters
# and P4 up to ~1,000 tokens with no overlap, so overlap=64 and the whitespace-word token unit
# are NOT IN PAPERS (own defaults, configurable). Section-first chunking is the task spec.
"""Section-aware chunker: split by section first, then window within a section."""
from __future__ import annotations

from typing import Callable, Iterable, Iterator

DEFAULT_SIZE = 512
DEFAULT_OVERLAP = 64


def chunk_text(text: str, size: int = DEFAULT_SIZE, overlap: int = DEFAULT_OVERLAP,
               tokenize: Callable[[str], list[str]] = str.split) -> list[str]:
    """Sliding window over tokens. Default token = whitespace word (approximation)."""
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError("need size > 0 and 0 <= overlap < size")
    tokens = tokenize(text)
    if not tokens:
        return []
    step = size - overlap
    chunks = []
    for start in range(0, len(tokens), step):
        chunks.append(" ".join(tokens[start:start + size]))
        if start + size >= len(tokens):
            break
    return chunks


def chunk_label(rec: dict, size: int = DEFAULT_SIZE, overlap: int = DEFAULT_OVERLAP,
                sections: Iterable[str] | None = None,
                tokenize: Callable[[str], list[str]] = str.split) -> Iterator[dict]:
    """Yield chunk dicts with the metadata Phase 2 needs. Never crosses section boundaries."""
    wanted = set(sections) if sections is not None else None
    for sec_name, parts in rec["sections"].items():
        if wanted is not None and sec_name not in wanted:
            continue
        idx = 0
        for part in parts:
            for ch in chunk_text(part["text"], size, overlap, tokenize):
                yield {
                    "chunk_id": f"{rec['set_id']}:{sec_name}:{idx}",
                    "set_id": rec["set_id"], "section": sec_name,
                    "ingredients": rec["ingredients"], "title": rec["title"],
                    "active_moieties": rec.get("active_moieties", []),
                    "product_names": rec.get("product_names", []),
                    "generic_names": rec.get("generic_names", []),
                    "manufacturer": rec.get("manufacturer"),
                    "text": ch,
                }
                idx += 1


if __name__ == "__main__":
    import argparse
    import json
    from collections import Counter
    from pathlib import Path

    from medsafe.spl import iter_parts

    ap = argparse.ArgumentParser(description="Write chunks.jsonl from whichever parts exist")
    ap.add_argument("--data-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--size", type=int, default=DEFAULT_SIZE)
    ap.add_argument("--overlap", type=int, default=DEFAULT_OVERLAP)
    ap.add_argument("--max-labels-per-part", type=int, default=None)
    a = ap.parse_args()
    a.out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    stats_by_part: dict = {}
    with open(a.out, "w", encoding="utf-8") as fh:
        for rec in iter_parts(a.data_dir, stats_by_part, a.max_labels_per_part):
            for ch in chunk_label(rec, a.size, a.overlap):
                fh.write(json.dumps(ch, ensure_ascii=False) + "\n")
                n += 1
    print(f"wrote {n} chunks to {a.out}")
    print({k: dict(v) for k, v in stats_by_part.items()})

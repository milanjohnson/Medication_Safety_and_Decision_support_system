# SOURCE: NOT IN PAPERS (own tooling). Every number written comes from running medsafe.spl and
# medsafe.chunking on the real zips in data/dailymed_rx. A capped run is marked as a SAMPLE in
# the file's own fields, so the dashboard cannot present it as a full count.
"""Write artifacts/dailymed_stats.json, read by GET /api/datasets/dailymed/stats.

From the aakaash folder (sample of the first 200 labels per part):
    .venv\\Scripts\\python.exe scripts\\dailymed_stats.py --max-labels-per-part 200
Full run over every zip present (slow, reads all labels):
    .venv\\Scripts\\python.exe scripts\\dailymed_stats.py
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
AAKAASH = HERE.parent
sys.path.insert(0, str(AAKAASH))

from medsafe.chunking import DEFAULT_OVERLAP, DEFAULT_SIZE, chunk_label  # noqa: E402
from medsafe.spl import CANONICAL_SECTIONS, iter_parts  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--data-dir", type=Path, default=AAKAASH.parent / "data" / "dailymed_rx")
    ap.add_argument("--out", type=Path, default=AAKAASH / "artifacts" / "dailymed_stats.json")
    ap.add_argument("--max-labels-per-part", type=int, default=None,
                    help="cap per zip; the output is then marked as a sample")
    ap.add_argument("--size", type=int, default=DEFAULT_SIZE)
    ap.add_argument("--overlap", type=int, default=DEFAULT_OVERLAP)
    a = ap.parse_args()

    zips = sorted(a.data_dir.glob("*.zip"))
    if not zips:
        sys.exit(f"No .zip files in {a.data_dir}; nothing to summarise.")
    zip_entries = {}
    for z in zips:
        with zipfile.ZipFile(z) as zf:
            zip_entries[z.name] = sum(1 for i in zf.infolist() if not i.is_dir())

    t0 = time.perf_counter()
    by_part: dict[str, Counter] = {}
    sec_labels, sec_chunks = Counter(), Counter()
    ingredients, moieties = set(), set()
    labels = 0
    for rec in iter_parts(a.data_dir, by_part, a.max_labels_per_part):
        labels += 1
        ingredients.update(rec["ingredients"])
        moieties.update(rec["active_moieties"])
        for sec in rec["sections"]:
            sec_labels[sec] += 1
        for ch in chunk_label(rec, a.size, a.overlap):
            sec_chunks[ch["section"]] += 1
    elapsed = time.perf_counter() - t0

    parse_stats: Counter = Counter()
    for st in by_part.values():
        parse_stats.update(st)
    sample = a.max_labels_per_part is not None
    out = {
        "is_sample": sample,
        "sample_limit_per_part": a.max_labels_per_part,
        "scope": (f"SAMPLE: the first {a.max_labels_per_part} labels of each loaded part, not the full set"
                  if sample else "All labels in the loaded parts"),
        "parts_loaded": list(by_part),
        "zip_entries": zip_entries,
        "labels_parsed": parse_stats["labels_parsed"],
        "parse_failures": parse_stats["parse_failures"],
        "labels_per_section": {s: sec_labels[s] for s in CANONICAL_SECTIONS},
        "chunks": sum(sec_chunks.values()),
        "chunks_per_section": {s: sec_chunks[s] for s in CANONICAL_SECTIONS},
        "distinct_ingredients": len(ingredients),
        "distinct_active_moieties": len(moieties),
        "parse_stats": dict(parse_stats),
        "chunk_size": a.size, "chunk_overlap": a.overlap,
        "elapsed_seconds": round(elapsed, 2),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    assert out["labels_parsed"] == labels
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()

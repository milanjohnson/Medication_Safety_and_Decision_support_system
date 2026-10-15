# Paper trace

Paper labels follow the mapping in CLAUDE.md (P-numbers, not file numbers).
Status column: UNTESTED means the code has not run on real data files.

| component | file | source | note | status |
|---|---|---|---|---|
| DDI 2013 as the interaction dataset | medsafe/ddi2013.py | FROM PAPERS: P6 (DDI Extraction 2013 with entity markers) | Section/table not checked in the PDF: UNVERIFIED: check 3.pdf | UNTESTED (fixtures only) |
| Four positive classes + `false` | medsafe/ddi2013.py | FROM PAPERS: P6 (micro P/R/F1 over four positive classes; Table 1 class table) | Class names effect/mechanism/advise/int come from the task spec | UNTESTED |
| Entity marker strings `<e1>..</e1>`, `<e2>..</e2>` | medsafe/ddi2013.py | NOT IN PAPERS | UNVERIFIED: check 3.pdf for Jia's marker format | UNTESTED |
| One instance per pair per sentence; overlap/discontiguous handling (first fragment only) | medsafe/ddi2013.py | NOT IN PAPERS | Own choice; skips are counted in parse stats | UNTESTED |
| Train/test split kept as shipped | medsafe/ddi2013.py | NOT IN PAPERS | Split detected from folder names; unmatched files are reported, not guessed | UNTESTED |
| Stratified dev split (10%, grouped by document, seed 13) | medsafe/ddi2013.py | NOT IN PAPERS | StratifiedGroupKFold from scikit-learn | UNTESTED |
| TAC 2017 data description | medsafe/tac2017.py | FROM PAPERS: P1 (TAC 2017: 101 train, 99 test, 2,208 unannotated; sections AR, W&P, BW) | Counts are the paper's, not ours | UNTESTED |
| TAC 2017 XML parser | medsafe/tac2017.py | NOT IN PAPERS | Element names are from the user's memory (a guess) | UNTESTED |
| DailyMed SPL XML as source | medsafe/spl.py | FROM PAPERS: P1 (DailyMed SPL XML) | | UNTESTED |
| Sections AR, W&P, BW, DI | medsafe/spl.py | FROM PAPERS: P1 | | UNTESTED |
| Sections Indications, Contraindications, Use in Specific Populations | medsafe/spl.py | NOT IN PAPERS (task spec) | | UNTESTED |
| LOINC section codes | medsafe/spl.py | NOT IN PAPERS | UNVERIFIED: from general knowledge, check on real files | UNTESTED |
| Title-regex fallback for sections | medsafe/spl.py | NOT IN PAPERS | Heuristic; method counts are reported | UNTESTED |
| Legacy "Warnings" merged into warnings_precautions | medsafe/spl.py | NOT IN PAPERS | Own choice | UNTESTED |
| Ingredient extraction (ACTIB, then ACTIM, then activeMoiety) | medsafe/spl.py | NOT IN PAPERS | Structure guessed from memory | UNTESTED |
| Nested-zip reading, loop over whatever parts exist | medsafe/spl.py | NOT IN PAPERS | Per task spec | UNTESTED |
| Section-first chunking, size 512 | medsafe/chunking.py | FROM PAPERS: P3 (retriever chunk size 512; unit UNVERIFIED: check 7.pdf) | Also the task-spec default | UNTESTED (fixtures only) |
| Overlap 64, whitespace-word token unit | medsafe/chunking.py | NOT IN PAPERS | Configurable. P2 uses 1,100/140 chars, P4 ~1,000 tokens with no overlap | UNTESTED (fixtures only) |
| Dataset report generator | data_report.py | NOT IN PAPERS | Real counts only | UNTESTED |

Fixtures in `tests/test_parsers.py` are hand-written strings, not data. They check code paths only.

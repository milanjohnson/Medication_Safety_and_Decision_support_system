# Paper trace

Paper labels follow the mapping in CLAUDE.md (P-numbers, not file numbers).
Status column: UNTESTED means the code has not run on real data files.

| component | file | source | note | status |
|---|---|---|---|---|
| DDI 2013 as the interaction dataset | medsafe/ddi2013.py | FROM PAPERS: P6 (DDI Extraction 2013 with entity markers) | Section/table not checked in the PDF: UNVERIFIED: check 3.pdf | RAN on real corpus (DATASET_REPORT.md) |
| Four positive classes + `false` | medsafe/ddi2013.py | FROM PAPERS: P6 (micro P/R/F1 over four positive classes; Table 1 class table) | Class names effect/mechanism/advise/int come from the task spec | RAN on real corpus (DATASET_REPORT.md) |
| Entity marker strings `<e1>..</e1>`, `<e2>..</e2>` | medsafe/ddi2013.py | NOT IN PAPERS | UNVERIFIED: check 3.pdf for Jia's marker format | RAN on real corpus (DATASET_REPORT.md) |
| One instance per pair per sentence; overlap/discontiguous handling (first fragment only) | medsafe/ddi2013.py | NOT IN PAPERS | Own choice; skips are counted in parse stats | RAN on real corpus (DATASET_REPORT.md) |
| Train/test split kept as shipped | medsafe/ddi2013.py | NOT IN PAPERS | Split detected from folder names; unmatched files are reported, not guessed | RAN on real corpus (DATASET_REPORT.md) |
| Stratified dev split (10%, grouped by document, seed 13) | medsafe/ddi2013.py | NOT IN PAPERS | StratifiedGroupKFold from scikit-learn | RAN on real corpus (DATASET_REPORT.md) |
| TAC 2017 data description | medsafe/tac2017.py | FROM PAPERS: P1 (TAC 2017: 101 train, 99 test, 2,208 unannotated; sections AR, W&P, BW) | Counts are the paper's, not ours | UNTESTED |
| TAC 2017 XML parser | medsafe/tac2017.py | NOT IN PAPERS | Element names are from the user's memory (a guess) | UNTESTED |
| DailyMed SPL XML as source | medsafe/spl.py | FROM PAPERS: P1 (DailyMed SPL XML) | Real file layout checked: one SPL XML per inner zip | RAN (first 200 labels of part6, 0 parse failures) |
| Sections AR, W&P, BW, DI | medsafe/spl.py | FROM PAPERS: P1 | Present in real labels; see scripts/spl_check | RAN (first 200 labels of part6) |
| Sections Indications, Contraindications, Use in Specific Populations | medsafe/spl.py | NOT IN PAPERS (task spec) |  | RAN (first 200 labels of part6) |
| LOINC section codes | medsafe/spl.py | NOT IN PAPERS | The mapped codes and their displayNames were found in real labels; check with scripts/spl_check/parser_check.py (survey mode) | VERIFIED against first 200 labels of part6 (codes and displayNames seen in the data) |
| Title fallback, whole title only | medsafe/spl.py | NOT IN PAPERS | Matches only when the whole title is the section name (optional colon); numbered or longer titles never match. First 200 labels: 21 matched sections before, 7 after (compare_versions.py). Section text of the 7 not read, judged by title | RAN (first 200 labels of part6) |
| Legacy "Warnings" merged into warnings_precautions | medsafe/spl.py | NOT IN PAPERS | Own choice | RAN (first 200 labels of part6) |
| Ingredient extraction (ACTIB, then ACTIM, then activeMoiety) | medsafe/spl.py | NOT IN PAPERS | ACTIB, else ACTIM, else activeMoiety (unchanged). Names keep salts for display. Open issue: ACTIM ingredients are dropped when ACTIB is present; in the first 200 labels one label (TRALEMENT) loses 3 of 4 active ingredients. Not fixed (not approved) | RAN (first 200 labels of part6); one known gap |
| Nested-zip reading, loop over whatever parts exist | medsafe/spl.py | NOT IN PAPERS | Per task spec | RAN (first 200 labels of part6, 0 failures) |
| Section-first chunking, size 512 | medsafe/chunking.py | FROM PAPERS: P3 (retriever chunk size 512; unit UNVERIFIED: check 7.pdf) | Also the task-spec default | RAN (first 200 labels of part6) |
| Overlap 64, whitespace-word token unit | medsafe/chunking.py | NOT IN PAPERS | Configurable. P2 uses 1,100/140 chars, P4 ~1,000 tokens with no overlap | RAN (first 200 labels of part6) |
| Dataset report generator | data_report.py | NOT IN PAPERS | Real counts only | RAN (DDI section real; DailyMed and TAC sections NOT RUN at the last report, no data then) |
| API router and endpoints under /api | api/router.py | NOT IN PAPERS | One APIRouter (prefix /api) so the team can include_router it. Endpoints follow the web-app prompt | RAN (7 endpoints called on a live server) |
| not_ready convention (no placeholder data) | api/schemas.py | NOT IN PAPERS | Every response carries status, reason and fix; missing data never returns numbers | RAN (tests with fixtures; real server with missing DailyMed, TAC, index and model) |
| Component status from files on disk | api/services/status.py | NOT IN PAPERS | A component is ready only when its files exist | RAN (real server) |
| DDI statistics and examples service | api/services/datasets.py | NOT IN PAPERS | Parses the corpus live with medsafe.ddi2013 (cached) and the same dev split as data_report.py; checks the API plumbing, not parser correctness | VERIFIED against DATASET_REPORT.md (per-class counts for train, dev and test identical) |
| DailyMed and TAC statistics endpoints | api/services/datasets.py | NOT IN PAPERS | not_ready path run on real folders; ready path exercised only by fixtures. DailyMed statistics need a stats script that does not exist yet | RAN (not_ready path real; ready path fixtures only) |
| Trace endpoint (this file as JSON) | api/services/trace.py | NOT IN PAPERS | Category comes from the text of the source cell; rows that do not fit are reported as malformed | RAN (real PAPER_TRACE.md) |
| Coming-soon module list | api/modules.py | NOT IN PAPERS | Names from the web-app prompt; stages as stated by the user from the architecture diagram. api/modules.py is the single source: the web app fetches the list from /api/status | RAN (tests, real server) |
| API tests | tests/test_api.py | NOT IN PAPERS | Fixtures only; never shown in the UI | RAN |
| SPL parser check scripts | scripts/spl_check/ | NOT IN PAPERS | Read-only diagnostics on a DailyMed zip, including xml_paths.py (real XML paths) and compare_versions.py (before/after) | RAN (part6, first 200 labels) |
| Precautions (42232-9) as its own section | medsafe/spl.py | NOT IN PAPERS (user decision) | Not merged into warnings and precautions. Its text leaves out subsections captured on their own (drug interactions, pregnancy, pediatric, geriatric); those are still found inside it. If TAC 2017 needs a merge it must be an explicit labelled mapping; none exists | RAN (first 200 labels of part6: 72 labels; no verbatim duplication found by the script check) |
| Active moiety for same-ingredient matching | medsafe/spl.py | NOT IN PAPERS (user decision) | Read from ingredient/ingredientSubstance/activeMoiety/activeMoiety/name (path confirmed on real files). Raw ingredient name kept for display. Describe as same active ingredient matched on its active moiety, not same drug: in the first 200 labels it groups products that are not interchangeable (mycophenolate mofetil with mycophenolate sodium) | RAN (first 200 labels of part6) |
| Generic name and manufacturer fields | medsafe/spl.py | NOT IN PAPERS | genericMedicine/name and document/author/assignedEntity/representedOrganization/name (direct child), both paths confirmed on real files. Manufacturer can be a repackager | RAN (first 200 labels of part6) |
| DailyMed statistics script | scripts/dailymed_stats.py | NOT IN PAPERS | Writes artifacts/dailymed_stats.json from a real parser run; a capped run is marked as a sample inside the file | RAN (200-label sample, part6) |

Fixtures in `tests/test_parsers.py` are hand-written strings, not data. They check code paths only.

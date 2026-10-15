# Dataset report

Generated 2026-10-15 23:27 by `aakaash/data_report.py` (default arguments). Every count below was produced by running the parsers on the real files; sections marked NOT RUN had no data present.

## DailyMed Rx labels (Subarea A source)

NOT RUN: no `.zip` files found in `C:\Users\aakaa\Documents\RM\Medication_Safety_and_Decision_support_system\data\dailymed_rx`.

## DailyMed mapping files

NOT PRESENT: `C:\Users\aakaa\Documents\RM\Medication_Safety_and_Decision_support_system\data\mappings` is empty. Not parsed yet.

## DDI Extraction 2013 (Subarea B source)

XML files by split (classified by folder name): {'train': 714, 'test': 191, 'excluded_ner': 112, 'unclassified': 0}

Dev split: 10% of train, stratified by label and grouped by document, seed 13. Entity markers: [['<e1>', '</e1>'], ['<e2>', '</e2>']]

| class | train | dev | test |
|---|---|---|---|
| effect | 1518 | 169 | 360 |
| mechanism | 1187 | 132 | 302 |
| advise | 743 | 83 | 221 |
| int | 171 | 17 | 96 |
| false | 21418 | 2353 | 4736 |
| **total** | 25037 | 2754 | 5715 |

Imbalance ratio = (count of `false`) / (count of class):

| split | class | false : class |
|---|---|---|
| train | effect | 14.11 |
| train | mechanism | 18.04 |
| train | advise | 28.83 |
| train | int | 125.25 |
| dev | effect | 13.92 |
| dev | mechanism | 17.83 |
| dev | advise | 28.35 |
| dev | int | 138.41 |
| test | effect | 13.16 |
| test | mechanism | 15.68 |
| test | advise | 21.43 |
| test | int | 49.33 |

By source: {"train": {"drugbank": 23392, "medline": 1645}, "dev": {"drugbank": 2613, "medline": 141}, "test": {"drugbank": 5265, "medline": 450}}

Parser statistics (skips and anomalies): {"train": {"documents": 714, "sentences": 6976, "documents_without_pairs": 90, "entities": 14765, "pairs": 27792, "instances": 27791, "discontiguous_entities": 38, "entity_text_mismatch": 38, "true_without_valid_type_treated_false": 1, "skipped_overlapping_entities": 1}, "test": {"documents": 191, "sentences": 1299, "entities": 3040, "pairs": 5716, "instances": 5715, "discontiguous_entities": 9, "entity_text_mismatch": 9, "skipped_overlapping_entities": 1}}

## TAC 2017 ADR labels (parser sanity-check set)

NOT RUN: no `.xml` files found in `C:\Users\aakaa\Documents\RM\Medication_Safety_and_Decision_support_system\data\tac2017`.

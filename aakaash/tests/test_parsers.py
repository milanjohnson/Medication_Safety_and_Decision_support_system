# SOURCE: NOT IN PAPERS. FIXTURES: every XML string below is hand-written to exercise the code
# paths. It is NOT real DDI 2013 / TAC 2017 / DailyMed data and proves nothing about real files.
import io
import sys
import tempfile
import unittest
import zipfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from medsafe import ddi2013, spl, tac2017  # noqa: E402
from medsafe.chunking import chunk_label, chunk_text  # noqa: E402

FIXTURE_DDI = """<document id="DDI-DrugBank.dFIX">
<sentence id="DDI-DrugBank.dFIX.s0" text="Aspirin increases the effect of warfarin.">
<entity id="e0" charOffset="0-6" type="drug" text="Aspirin"/>
<entity id="e1" charOffset="32-39" type="drug" text="warfarin"/>
<pair id="p0" e1="e0" e2="e1" ddi="true" type="effect"/>
</sentence>
<sentence id="DDI-DrugBank.dFIX.s1" text="Do not mix aspirin and ibuprofen.">
<entity id="e0" charOffset="11-17" type="drug" text="aspirin"/>
<entity id="e1" charOffset="23-31" type="drug" text="ibuprofen"/>
<pair id="p0" e1="e0" e2="e1" ddi="false"/>
</sentence></document>"""

FIXTURE_TAC = """<Label drug="FixDrug" setid="x">
<Text><Section name="adverse reactions" id="S1">Nausea was common.</Section>
<Section name="boxed warnings" id="S2">Risk of harm.</Section></Text>
<Mentions><Mention id="M1" section="S1" type="AdverseReaction" start="0" len="6" str="Nausea"/></Mentions>
<Relations/><Reactions><Reaction id="R1" str="Nausea"><Normalization id="N1" meddra_pt="Nausea"/></Reaction></Reactions>
</Label>"""

FIXTURE_SPL = """<document xmlns="urn:hl7-org:v3"><id root="d"/><setId root="SET-FIX-1"/>
<title>FixDrug tablets</title><versionNumber value="3"/><effectiveTime value="20250101"/>
<component><structuredBody>
<component><section><code code="34067-9"/><title>INDICATIONS</title><text><paragraph>For headache.</paragraph></text></section></component>
<component><section><code code="43684-0"/><title>USE IN SPECIFIC POPULATIONS</title>
  <component><section><code code="42228-7"/><title>Pregnancy</title><text>Avoid in pregnancy.</text></section></component></section></component>
<component><section><code code="99999-9"/><title>Boxed Warning</title><text>Fallback by title.</text></section></component>
</structuredBody></component>
<author><manufacturedProduct><manufacturedProduct><name>FixBrand</name>
<ingredient classCode="ACTIB"><ingredientSubstance><name>FIXAMIDE HYDROCHLORIDE</name></ingredientSubstance></ingredient>
</manufacturedProduct></manufacturedProduct></author></document>"""


class DDI(unittest.TestCase):
    def test_pairs_markers_and_labels(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.xml"
            p.write_text(FIXTURE_DDI, encoding="utf-8")
            stats = Counter()
            rows = list(ddi2013.parse_ddi_file(p, stats))
        self.assertEqual([r["label"] for r in rows], ["effect", "false"])
        self.assertIn("<e1>Aspirin</e1>", rows[0]["marked_text"])
        self.assertIn("<e2>warfarin</e2>", rows[0]["marked_text"])
        self.assertEqual(stats["entity_text_mismatch"], 0)

    def test_split_classification(self):
        with tempfile.TemporaryDirectory() as d:
            for sub in ("Train/DrugBank", "Test/DrugBank", "other"):
                (Path(d) / sub).mkdir(parents=True)
                (Path(d) / sub / "a.xml").write_text(FIXTURE_DDI, encoding="utf-8")
            c = ddi2013.classify_files(Path(d))
        self.assertEqual({k: len(v) for k, v in c.items()},
                         {"train": 1, "test": 1, "excluded_ner": 0, "unclassified": 1})


class TAC(unittest.TestCase):
    def test_label(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "train_xml").mkdir()
            (Path(d) / "train_xml" / "x.xml").write_text(FIXTURE_TAC, encoding="utf-8")
            s = tac2017.summarize(Path(d))
        self.assertEqual(s["splits"], {"train_xml": 1})
        self.assertEqual(s["sections"], 2)
        self.assertEqual(s["mentions"], 1)


class SPL(unittest.TestCase):
    def test_parse_nested_zip_and_sections(self):
        inner = io.BytesIO()
        with zipfile.ZipFile(inner, "w") as z:
            z.writestr("fix.xml", FIXTURE_SPL)
        outer_path = None
        with tempfile.TemporaryDirectory() as d:
            outer_path = Path(d) / "part_fixture.zip"
            with zipfile.ZipFile(outer_path, "w") as z:
                z.writestr("prescription/fix.zip", inner.getvalue())
                z.writestr("broken.xml", "<not xml")
            stats = Counter()
            recs = list(spl.iter_part(outer_path, stats))
        self.assertEqual(len(recs), 1)
        self.assertEqual(stats["parse_failures"], 1)
        r = recs[0]
        self.assertEqual(r["set_id"], "SET-FIX-1")
        self.assertEqual(r["ingredients"], ["fixamide hydrochloride"])
        self.assertEqual(set(r["sections"]),
                         {"indications", "specific_populations", "boxed_warning"})
        self.assertIn("Avoid in pregnancy", r["sections"]["specific_populations"][0]["text"])
        self.assertEqual(r["sections"]["boxed_warning"][0]["method"], "title_fallback")


class Chunking(unittest.TestCase):
    def test_overlap_and_no_cross_section(self):
        words = " ".join(f"w{i}" for i in range(10))
        ch = chunk_text(words, size=4, overlap=1)
        self.assertEqual(ch[0], "w0 w1 w2 w3")
        self.assertEqual(ch[1], "w3 w4 w5 w6")
        rec = {"set_id": "s", "title": "t", "ingredients": ["x"],
               "sections": {"indications": [{"text": "a b c"}],
                            "adverse_reactions": [{"text": "d e"}]}}
        out = list(chunk_label(rec, size=512, overlap=64))
        self.assertEqual([c["section"] for c in out], ["indications", "adverse_reactions"])
        self.assertEqual(out[0]["text"], "a b c")

    def test_bad_args(self):
        with self.assertRaises(ValueError):
            chunk_text("a b", size=4, overlap=4)


if __name__ == "__main__":
    unittest.main()

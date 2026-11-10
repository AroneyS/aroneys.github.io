#!/usr/bin/env python3

import unittest
from add_doi import pipeline, make_key
from bib_to_cv import parse_bib

RAW = """@article{Aroney_2025,
 title={CoverM: read alignment statistics for metagenomics},
 volume={41}, ISSN={1367-4811}, DOI={10.1093/bioinformatics/btaf147},
 number={4}, journal={Bioinformatics}, publisher={Oxford University Press (OUP)},
 author={Aroney, Samuel T N and Newell, Rhys},
 year={2025}, month=apr }
"""


class Tests(unittest.TestCase):
    def test_make_key(self):
        self.assertEqual(make_key("Aroney", "2025", "The CoverM tool"), "aroney2025coverm")
        self.assertEqual(make_key("O'Neil", "2020", ""), "oneil2020")

    def test_pipeline(self):
        out = pipeline(RAW, "10.1093/bioinformatics/btaf147", abbr="Bioinformatics", role="first")
        self.assertTrue(out.startswith("@article{aroney2025coverm,"))
        entry = parse_bib(out).to_dicts()[0]
        self.assertEqual(entry["role"], "first")
        self.assertEqual(entry["abbr"], "Bioinformatics")
        self.assertEqual(entry["doi"], "10.1093/bioinformatics/btaf147")
        self.assertNotIn("issn", entry)
        self.assertNotIn("selected", out)

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            pipeline("", "10.1/x")


if __name__ == "__main__":
    unittest.main()

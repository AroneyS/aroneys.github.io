#!/usr/bin/env python3

import unittest
import polars as pl
from polars.testing import assert_frame_equal
from bib_to_cv import pipeline, parse_bib, format_authors

BIB = """
@string{x = {y}}
@article{a2025,
  title = {Tool: {CoverM} (v1)},
  author = {Aroney, Samuel T. N. and Newell, Robert and Tyson, Gene and Woodcroft, Ben},
  journal = {Bioinformatics},
  volume = {41},
  pages = {1--5},
  year = {2025},
  doi = {10.1/x},
  role = {first}
}
@article{b2025,
  title = {Hidden},
  author = {Smith, J.},
  year = {2025},
  cv = {false}
}
@misc{c2025, title = {Preprint}, author = {Cronin*, D. and Aroney*, S.}, journal = {bioRxiv}, year = {2025}, preprint = {true}}
"""


class Tests(unittest.TestCase):
    def assertDataFrameEqual(self, a, b):
        assert_frame_equal(a, b, check_dtype=False, check_row_order=False)

    def test_parse_skips_strings_and_reads_nested_braces(self):
        bib = parse_bib(BIB)
        self.assertEqual(bib["key"].to_list(), ["a2025", "b2025", "c2025"])
        self.assertEqual(bib.filter(pl.col("key") == "a2025")["title"][0], "Tool: {CoverM} (v1)")

    def test_pipeline_rows(self):
        out = pipeline(parse_bib(BIB)).sort("end")
        self.assertEqual(out.height, 2)  # cv = false dropped
        a = out.filter(pl.col("title").str.contains("Tool")).to_dicts()[0]
        self.assertEqual(a["title"], "[Tool: CoverM &#40;v1&#41;](https://doi.org/10.1/x)")
        self.assertEqual(a["loc"], "Bioinformatics (2025) 41:1-5")
        self.assertEqual(a["description_1"], "**Samuel T. N. Aroney**, Robert Newell, Gene Tyson, et al.")
        self.assertEqual(a["description_2"], "Role: first")
        c = out.filter(pl.col("title") == "Preprint").to_dicts()[0]
        self.assertTrue(c["loc"].endswith("[preprint]"))

    def test_own_name_kept_when_beyond_leading_authors(self):
        s = format_authors("A, A. and B, B. and C, C. and D, D. and Aroney, S. and E, E.")
        self.assertEqual(s, "A. A, B. B, C. C, ..., **S. Aroney**, et al.")

    def test_empty(self):
        self.assertTrue(pipeline(pl.DataFrame()).is_empty())


if __name__ == "__main__":
    unittest.main()

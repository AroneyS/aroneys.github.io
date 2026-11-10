#!/usr/bin/env python3

import unittest
from update_scholar_metrics import pipeline

PREV = {"citations_all": 1800, "hindex_all": 14, "i10index_all": 15, "retrieved": "2026-11-10", "source": "seed"}


class Tests(unittest.TestCase):
    def test_update(self):
        out = pipeline({"citedby": 1850, "hindex": 15, "i10index": 16}, PREV, "2026-12-01")
        self.assertEqual((out["citations_all"], out["hindex_all"], out["i10index_all"]), (1850, 15, 16))
        self.assertEqual(out["retrieved"], "2026-12-01")

    def test_blocked_profile_keeps_cache(self):
        self.assertEqual(pipeline({"citedby": None, "hindex": None, "i10index": None}, PREV, "x"), PREV)
        self.assertEqual(pipeline({}, PREV, "x"), PREV)

    def test_regression_keeps_cache(self):
        self.assertEqual(pipeline({"citedby": 0, "hindex": 0, "i10index": 0}, PREV, "x"), PREV)


if __name__ == "__main__":
    unittest.main()

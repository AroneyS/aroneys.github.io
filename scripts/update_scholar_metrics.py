#!/usr/bin/env python3

"""
Author: Samuel Aroney
Refresh _data/scholar_metrics.json (total citations, h-index, i10-index) from Google Scholar.

Google Scholar often blocks automated requests (especially from CI). On any failure or
implausible result the existing JSON is left untouched and the script exits 0, so the
site keeps showing the last cached values. Totals include Scholar's merged records.
Requires the `scholarly` package (requirements.txt); imported lazily.
"""

import sys
import json
import argparse
import logging
from datetime import date

SCHOLAR_ID = "qBVdjY8AAAAJ"
KEYS = ("citedby", "hindex", "i10index")
OUT_KEYS = {"citedby": "citations_all", "hindex": "hindex_all", "i10index": "i10index_all"}


def pipeline(profile: dict, previous: dict, today: str) -> dict:
    """Merge scholarly profile indices into the cached metrics.

    Returns `previous` unchanged if the profile is incomplete or any value is
    non-numeric/negative or the citation count falls (a blocked or partial scrape).
    """
    try:
        new = {OUT_KEYS[k]: int(profile[k]) for k in KEYS}
    except (KeyError, TypeError, ValueError):
        return previous
    if any(v < 0 for v in new.values()):
        return previous
    if previous and new["citations_all"] < previous.get("citations_all", 0):
        return previous
    return {**previous, **new, "retrieved": today, "source": "Google Scholar via scholarly"}


def fetch_profile(scholar_id: str) -> dict:
    from scholarly import scholarly
    author = scholarly.fill(scholarly.search_author_id(scholar_id), sections=["indices"])
    return {k: author.get(k) for k in KEYS}


def main(arguments):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--debug", help="output debug information", action="store_true")
    parser.add_argument("--quiet", help="only output errors", action="store_true")
    parser.add_argument("--json", default="_data/scholar_metrics.json", help="Cached metrics file")
    parser.add_argument("--scholar-id", default=SCHOLAR_ID)
    args = parser.parse_args(arguments)

    loglevel = logging.DEBUG if args.debug else logging.ERROR if args.quiet else logging.INFO
    logging.basicConfig(level=loglevel, format="%(asctime)s %(levelname)s: %(message)s", datefmt="%Y/%m/%d %I:%M:%S %p")

    with open(args.json) as f:
        previous = json.load(f)
    try:
        profile = fetch_profile(args.scholar_id)
    except Exception as e:  # network errors, captcha blocks, missing package
        logging.warning(f"Scholar fetch failed ({type(e).__name__}: {e}); keeping cached {args.json}")
        return 0
    updated = pipeline(profile, previous, date.today().isoformat())
    if updated == previous:
        logging.warning("No usable update; keeping cached values")
        return 0
    with open(args.json, "w") as f:
        json.dump(updated, f, indent=2)
        f.write("\n")
    logging.info(f"Updated {args.json}: {updated}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3

"""
Author: Samuel Aroney
Append publications to _bibliography/papers.bib from DOIs (BibTeX via doi.org content
negotiation). DOIs already in the .bib are skipped. Afterwards, hand-edit the new entry
for al-folio extras (abbr, selected, role, preprint, equal-contribution asterisks) and
run scripts/bib_to_cv.py to refresh the CV.

Example:
  python scripts/add_doi.py 10.1038/s41592-025-02901-1 --abbr "Nat Methods" --selected --role first
"""

import re
import sys
import argparse
import logging
import subprocess
from bib_to_cv import parse_bib

KEEP_FIELDS = ["title", "author", "journal", "booktitle", "volume", "number", "pages", "year", "publisher", "doi", "url"]
STOPWORDS = {"a", "an", "the", "of", "on", "in", "and", "for", "to", "with"}


def make_key(family: str, year: str, title: str) -> str:
    family = re.sub(r"[^a-z]", "", family.lower())
    words = [w for w in re.findall(r"[a-z0-9]+", title.lower()) if w not in STOPWORDS]
    return f"{family}{year}{words[0] if words else ''}"


def pipeline(raw_bibtex: str, doi: str, abbr: str | None = None, selected: bool = False,
             role: str | None = None, preprint: bool = False) -> str:
    """Normalise a doi.org BibTeX record into an al-folio style entry."""
    bib = parse_bib(raw_bibtex)
    if bib.is_empty():
        raise ValueError(f"No BibTeX entry found for {doi}")
    r = {k: v for k, v in bib.to_dicts()[0].items() if v is not None}
    r["doi"] = doi
    for k in ("title", "author", "journal"):
        if k in r:
            r[k] = r[k].replace("&amp;", "&")
    family = r["author"].split(",")[0].split(" and ")[0] if "author" in r else "anon"
    key = make_key(family, r.get("year", ""), r.get("title", ""))
    fields = [("abbr", abbr), ("bibtex_show", "true"), ("selected", "true" if selected else None),
              ("preprint", "true" if preprint else None), ("role", role)]
    # doi.org returns a redundant dx.doi.org url; the doi field is enough
    fields += [(k, r.get(k)) for k in KEEP_FIELDS if k != "url"]
    fields = [(k, v) for k, v in fields if v]
    typ = "article" if "journal" in r else r["type"]
    body = ",\n".join(f"  {k:<12}= {{{v}}}" for k, v in fields)
    return f"@{typ}{{{key},\n{body}\n}}\n"


def fetch_bibtex(doi: str) -> str:
    # curl follows the doi.org redirect and uses the system CA bundle
    res = subprocess.run(["curl", "-sLf", "-H", "Accept: application/x-bibtex", f"https://doi.org/{doi}"],
                         capture_output=True, text=True, timeout=60)
    if res.returncode != 0:
        raise RuntimeError(f"Could not fetch {doi}: curl exit {res.returncode}")
    return res.stdout


def main(arguments):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--debug", help="output debug information", action="store_true")
    parser.add_argument("--quiet", help="only output errors", action="store_true")
    parser.add_argument("dois", nargs="+", help="DOIs to add")
    parser.add_argument("--bib", default="_bibliography/papers.bib")
    parser.add_argument("--abbr", help="Venue badge (applies to all given DOIs)")
    parser.add_argument("--selected", action="store_true", help="Show on the about page")
    parser.add_argument("--role", help="e.g. first, co-first, contributing")
    parser.add_argument("--preprint", action="store_true")
    args = parser.parse_args(arguments)

    loglevel = logging.DEBUG if args.debug else logging.ERROR if args.quiet else logging.INFO
    logging.basicConfig(level=loglevel, format="%(asctime)s %(levelname)s: %(message)s", datefmt="%Y/%m/%d %I:%M:%S %p")

    with open(args.bib, encoding="utf-8") as f:
        existing = f.read().lower()
    new = []
    for doi in args.dois:
        if doi.lower() in existing:
            logging.info(f"Skipping {doi}: already present")
            continue
        new.append(pipeline(fetch_bibtex(doi), doi, args.abbr, args.selected, args.role, args.preprint))
    if new:
        with open(args.bib, "a", encoding="utf-8") as f:
            f.write("\n" + "\n".join(new))
        logging.info(f"Appended {len(new)} entries to {args.bib}")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

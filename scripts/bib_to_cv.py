#!/usr/bin/env python3

"""
Author: Samuel Aroney
Convert _bibliography/papers.bib into the article rows used by the CV
(cv/data/articles.tsv), so the website publication list and the CV share one source.

Optional BibTeX fields read here (all ignored by the website renderer):
  role      = {first | co-first | senior | contributing}   free text shown in the CV
  cv        = {false}                                      leave the entry out of the CV
  preprint  = {true}                                       mark as preprint
"""

import re
import sys
import argparse
import logging
import polars as pl

OWN_FAMILY_NAME = "Aroney"
MAX_LEADING_AUTHORS = 3

OUTPUT_COLUMNS = {
    "section": str,
    "title": str,
    "loc": str,
    "institution": str,
    "start": str,
    "end": str,
    "description_1": str,
    "description_2": str,
    "description_3": str,
    "in_resume": str,
}


def parse_bib(text: str) -> pl.DataFrame:
    """Minimal BibTeX parser (brace-delimited or quoted values; no @string expansion)."""
    rows = []
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", text):
        entry_type, key = m.group(1).lower(), m.group(2)
        if entry_type in ("string", "comment", "preamble"):
            continue
        i, fields = m.end(), {}
        while i < len(text):
            fm = re.compile(r"\s*([\w\-]+)\s*=\s*").match(text, i)
            if not fm:
                break
            name, i = fm.group(1).lower(), fm.end()
            if text[i] == "{":
                depth, j = 1, i + 1
                while depth:
                    depth += {"{": 1, "}": -1}.get(text[j], 0)
                    j += 1
                value, i = text[i + 1 : j - 1], j
            elif text[i] == '"':
                j = text.index('"', i + 1)
                value, i = text[i + 1 : j], j + 1
            else:
                vm = re.compile(r"[^,}\s]+").match(text, i)
                value, i = vm.group(0), vm.end()
            fields[name] = re.sub(r"\s+", " ", value).strip()
            cm = re.compile(r"\s*,?").match(text, i)
            i = cm.end()
        rows.append({"type": entry_type, "key": key, **fields})
    return pl.DataFrame(rows, infer_schema_length=None) if rows else pl.DataFrame()


def format_authors(author_field: str) -> str:
    """'Aroney, S. and Smith, J.' -> 'S. Aroney, J. Smith' with own name bolded, truncated with et al."""
    names = []
    for a in re.split(r"\s+and\s+", author_field):
        a = a.replace("*", "").replace("†", "").strip()
        if "," in a:
            family, given = [p.strip() for p in a.split(",", 1)]
            a = f"{given} {family}"
        names.append(a)
    own = [i for i, n in enumerate(names) if n.split()[-1] == OWN_FAMILY_NAME]
    shown = sorted(set(range(min(MAX_LEADING_AUTHORS, len(names)))) | set(own))
    out, prev = [], -1
    for i in shown:
        if i > prev + 1:
            out.append("...")
        out.append(f"**{names[i]}**" if i in own else names[i])
        prev = i
    if names and prev < len(names) - 1:
        out.append("et al.")
    return ", ".join(out)


def venue(row: dict) -> str:
    journal = row.get("journal") or row.get("howpublished") or row.get("publisher") or ""
    year = row.get("year") or ""
    vol = row.get("volume") or ""
    pages = (row.get("pages") or "").replace("--", "-")
    tail = f" {vol}" if vol else ""
    tail += f":{pages}" if vol and pages else ""
    return f"{journal} ({year}){tail}".strip()


def pipeline(bib: pl.DataFrame) -> pl.DataFrame:
    """One CV 'academic_articles' row per bib entry (unless cv = {false})."""
    if bib.is_empty():
        return pl.DataFrame(schema=OUTPUT_COLUMNS)
    for col in ("title", "doi", "url", "year", "author", "role", "cv", "preprint"):
        if col not in bib.columns:
            bib = bib.with_columns(pl.lit(None, dtype=pl.Utf8).alias(col))
    rows = []
    for r in bib.to_dicts():
        if (r.get("cv") or "").lower() == "false":
            continue
        title = re.sub(r"[{}]", "", r["title"] or "").replace("(", "&#40;").replace(")", "&#41;")
        link = f"https://doi.org/{r['doi']}" if r.get("doi") else r.get("url")
        title = f"[{title}]({link})" if link else title
        loc = venue(r)
        if (r.get("preprint") or "").lower() == "true":
            loc += " [preprint]"
        notes = [format_authors(r["author"])] if r.get("author") else []
        if r.get("role"):
            notes.append(f"Role: {r['role']}")
        notes += [None] * (3 - len(notes))
        rows.append({
            "section": "academic_articles", "title": title, "loc": loc, "institution": None,
            "start": None, "end": r["year"], "description_1": notes[0], "description_2": notes[1],
            "description_3": notes[2], "in_resume": "TRUE",
        })
    return pl.DataFrame(rows, schema=OUTPUT_COLUMNS)


def main(arguments):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--debug", help="output debug information", action="store_true")
    parser.add_argument("--quiet", help="only output errors", action="store_true")
    parser.add_argument("--bib", default="_bibliography/papers.bib", help="Input BibTeX file")
    parser.add_argument("--output", default="cv/data/articles.tsv", help="Output TSV")
    args = parser.parse_args(arguments)

    loglevel = logging.DEBUG if args.debug else logging.ERROR if args.quiet else logging.INFO
    logging.basicConfig(level=loglevel, format="%(asctime)s %(levelname)s: %(message)s", datefmt="%Y/%m/%d %I:%M:%S %p")
    logging.info(args)

    with open(args.bib, encoding="utf-8") as f:
        bib = parse_bib(f.read())
    out = pipeline(bib)
    out.write_csv(args.output, separator="\t")
    logging.info(f"Wrote {out.height} articles to {args.output}")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

# aroneys.github.io

Personal site (Jekyll, [al-folio](https://github.com/alshedivat/al-folio) v1.2 starter) with the CV built from `cv/`.
The built site is deployed by GitHub Actions; `master` holds source only.

## Updating

| What | Edit | Then |
| --- | --- | --- |
| Publications (site and CV) | `_bibliography/papers.bib`, or `python scripts/add_doi.py <doi> [--abbr ... --role ... --selected --preprint]` | commit |
| CV entries | `cv/data/entries.csv`, `text_blocks.csv`, `contact_info.csv` | commit |
| News | add a file to `_news/` | commit |
| Software cards | `_projects/` | commit |
| Scholar totals | `_data/scholar_metrics.json` (refreshed weekly by CI; cached values are kept if Scholar blocks the request) | |

Optional `.bib` fields (not rendered on the site): `role`, `preprint = {true}`, `cv = {false}` (omit from CV).
Equal contribution: asterisks on the author names plus `additional_info = {* Equal contribution}`.

CI (`.github/workflows/deploy.yml`) runs the script tests, regenerates `cv/data/articles.tsv` from the `.bib`,
renders `assets/cv/{cv.html,cv.pdf,resume.pdf}` (resume = rows with `in_resume = TRUE`), builds and deploys.
These outputs are not tracked in git.

## Local use (pixi)

```bash
pixi run test                          # script unit tests
pixi run python scripts/bib_to_cv.py   # bib -> cv/data/articles.tsv
pixi run -e cv cv                      # CV HTML + PDFs into assets/cv/ (PDFs need Chrome; set PAGEDOWN_CHROME)
pixi run -e site gems && pixi run -e site build   # Jekyll build into _site/
```

## One-off GitHub setup

1. Settings > Pages > Source: **GitHub Actions**.
2. Custom domain (optional): set in Pages settings, add a `CNAME` file, and update `url:` in `_config.yml`.
3. Analytics (optional): set a provider ID under `analytics:` in `_config.yml`.

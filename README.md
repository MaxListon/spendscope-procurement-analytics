# SpendScope

**Public procurement and supplier concentration analytics, built with SQL, Python and R.**

SpendScope answers a procurement manager's question: *where is recorded award value concentrated, and how much evidence supports that comparison?*

This research portfolio uses real UK Contracts Finder records compiled by the Open Contracting Partnership. It is a local, reproducible analytics system with a static dashboard; it is not connected to a purchasing organization's live systems.

![Dashboard preview](docs/dashboard-preview.png)

## What it delivers

- Three pinned annual process-snapshot files with verified SHA-256 fingerprints.
- A DuckDB warehouse with separate award and supplier-link grains, plus inspectable SQL marts.
- Buyer concentration (HHI, largest supplier and top-five shares) with attribution coverage and minimum-support filters.
- Conservative supplier identity normalization. Conflicting registered IDs are excluded from attribution; joint awards remain in headline totals without value fan-out.
- Executed R analysis: category median bootstrap intervals, large-award sensitivity, and independently recomputed buyer concentration.
- A responsive dashboard with filters, CSV export, original notice links, a quality report and a standalone R research note.
- Automated tests, runtime conservation checks, a single-writer build lock, fingerprint verification, and CI configuration.

## Run it

Requirements: Python 3.12+, R 4.5+, and internet access for the first source download. Commands run from the checkout root.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-lock.txt
pip install -e '.[dev]'
mkdir -p .Rlibrary
export R_LIBS_USER="$PWD/.Rlibrary"
Rscript -e 'install.packages(c("ggplot2", "jsonlite", "svglite"), repos="https://cloud.r-project.org")'
python -m spendscope.pipeline --root .
pytest -q
Rscript R/test_concentration.R
python scripts/verify.py
python -m http.server 8080 --directory docs
```

Open http://localhost:8080. Cached sources can be rebuilt with `python -m spendscope.pipeline --root . --offline`. Keep the source checkout: SQL and R files are required at runtime. The R report and chart are built by R itself, not substituted with Python calculations.

Source archives total about 135 MB compressed; allow several GB of working memory. The first build may take several minutes. `docs/` can be hosted on GitHub Pages after review; this checkout has not yet been published.

## Read the analysis responsibly

**Award value is not actual spending, annual expenditure or realized supplier revenue.** Framework ceilings and overlapping economic commitments can dominate totals. Source revisions and incomplete publication affect year comparisons.

Concentration is measured only on positive, active GBP awards dated 2022–2024 with exactly one named, non-colliding supplier. Headline totals retain eligible joint and unidentified awards. Buyers need at least 30 attributed awards and 80% attributable value coverage for the default comparison view. These are transparent screening thresholds, not official regulatory cutoffs.

Name-only supplier matches are provisional. Exact normalized names can still merge unrelated organizations, and aliases can split a company. No fuzzy matches are applied automatically; no corporate-parent consolidation is claimed.

## Project map

| Path | Purpose |
|---|---|
| `src/spendscope/normalize.py` | Award normalization, exclusion reasons and identity rules |
| `src/spendscope/pipeline.py` | Verified ingestion, warehouse, checks, R execution and output publication |
| `sql/marts.sql` | Analytics tables with explicit attribution grain |
| `R/` | Statistical analysis, independent HHI checks and regression tests |
| `reports/` | Machine-readable evidence, exclusions and build fingerprints |
| `docs/` | Deployable dashboard and rendered research note |
| `tests/` | Analytical counterexamples and pipeline failure cases |
| `METHODOLOGY.md` | Definitions, assumptions and limits |
| `RUNBOOK.md` | Rebuild, recovery and release process |
| `PROJECT_PLAN.md` | Twelve-to-sixteen-week development and validation roadmap |
| `INTERVIEW_GUIDE.md` | How to explain the decisions and limitations |

See [the executive memo](EXECUTIVE_MEMO.md) for evidence-linked findings and [verification](VERIFICATION.md) for completed checks and remaining validation.

## Source and license

Source: [Contracts Finder / OCP registry](https://data.open-contracting.org/en/publication/128). Contains public sector information licensed under the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/). OCP compiles the process snapshots; `data/sources.json` records exact source URLs, retrieval date and hashes. Data authorship remains with the original publishers.

Project code: MIT. Maintainer: MaxListon.

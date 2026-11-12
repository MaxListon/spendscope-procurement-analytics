# Runbook

## Build and inspect

Run the README commands from the source checkout. The build verifies all compressed archives against `data/sources.json`, resolves compiled snapshots, builds a fresh DuckDB database, executes SQL contracts, runs R and renders the dashboard. The build lock rejects a second concurrent writer. All analysis must succeed before output replacement begins.

Outputs are replaced one file at a time, not as an atomic multi-file website transaction. Serve a reviewed copy or deploy a completed Git commit; do not serve a directory actively rebuilding. A failed computation leaves the prior published output untouched. A crash during the replacement phase may require a full rebuild and fingerprint verification.

`python scripts/verify.py` detects changed analysis code, missing outputs, stale report copies and artifact corruption against the build manifest. This is consistency checking, not cryptographic authentication by an independent party. Source archive checksums are independently checked by the pipeline.

## Failure recovery

- Source fingerprint mismatch: do not bypass it. Inspect the publisher revision, compare coverage and metrics, document the change, and deliberately update the source specification only after review.
- `.build.lock` already exists: confirm the previous build has ended before removing a stale lock. A live build must retain its lock.
- R package or graphics error: install the README packages in your R library; confirm `svglite` is installed for SVG output. No Python substitute should silently replace the R analysis.
- HHI disagreement: inspect the exact buyer group and values in R inputs and SQL. Do not loosen tolerances without explaining the numerical cause.
- Missing source: restore the exact cached archive or run an online build. Never substitute sample data under the same report labels.
- Missing data.json in browser: start an HTTP server rather than opening index.html as a local file.

## Release checklist

1. Run Python tests and R regression tests.
2. Run a full pinned-source build and artifact verification.
3. Check desktop/mobile layouts, filters, downloads and original notice links.
4. Review exclusion counts, attribution coverage and unusually large values.
5. Inspect the Git diff, source attribution and actual commit author settings.
6. Publish only reviewed tracked files. Do not upload the warehouse, raw source cache or environment directories.

CI runs unit tests, artifact verification and JavaScript syntax checks on pushes and pull requests. The manually dispatched real-data job downloads pinned sources and executes the R-inclusive rebuild. CI configuration is provided; no remote run is claimed until the project is uploaded and the run succeeds.

No secrets, authenticated data access, hosted database, telemetry service or scoring API are required. Static hosting has no background refresh: updated data require a reviewed rebuild and deployment.

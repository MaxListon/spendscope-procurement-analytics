# Runbook

## Build

Follow the README from the source checkout. The pipeline verifies archive fingerprints, builds a fresh warehouse, applies versioned evidence gates, executes ten SQL contracts, runs R and writes reports/dashboard assets. All computations must finish before publication begins. A single-writer lock prevents concurrent builds.

Outputs are replaced per file, not as a multi-file transaction. Do not serve the directory during a rebuild; deploy a completed, verified Git commit. A crash during replacement requires a rebuild and artifact verification. Failed computations preserve the prior published files; a regression test exercises that failure case.

`python scripts/verify.py` checks analysis inputs, generated artifacts and published manifest equality. It detects stale/corrupt artifacts; it is not independent cryptographic authentication. R SVG files and session metadata may differ by platform; cross-platform analytical agreement is checked separately.

## Evidence changes

Review decisions must cite the same registration number and explicitly approve an exact normalized name. Never broaden approval to all aliases under an ID. Retain original supplier names, rejected/unresolved cases and rationale. Notice holdbacks require an observed issue, source URL and original snapshot match. An unavailable page supports no validation claim.

A new evidence decision changes attribution and therefore requires a full rebuild, comparison review and release note. It never authorizes changing eligible award amounts. If a source revision is desired, investigate the changed archive, repin deliberately and retire or revalidate the v0.1 comparison baseline.

## Failure recovery

- Source checksum mismatch: stop, investigate and deliberately repin only after review; do not disable verification.
- Existing `.build.lock`: verify the original build has ended before removing a stale lock.
- R package/graphics failure: install README dependencies in `.Rlibrary`; no silent Python replacement.
- SQL/R HHI disagreement: inspect group/identity/amount inputs; do not loosen tolerances merely to pass.
- Missing or mismatched evidence record: compare the reviewed award key, source URL and amount before changing the decision file.
- Static load failure: serve `docs/` over HTTP; inspect `data.json` and the reported error state.

## CI and publication

Checks runs Python tests on 3.12 and 3.14, artifact verification and JavaScript syntax checks. A separate real-data job runs on every push, pull request and manual dispatch: install the built wheel, fetch pinned originals, run R regression cases, rebuild, compare full analytical JSON with committed results, then run tests and integrity verification.

Dashboard deployment runs only after Checks succeeds on a main-branch push from the same repository. It checks out the exact verified head SHA, verifies artifacts again and deploys `docs/` through GitHub Pages. Failed checks and pull requests do not publish. Read the actual run status before claiming remote validation.

A static deployment has no background updates. Source refreshes require reviewed rebuilds. No secrets, authenticated source feeds, hosted database or customer upload flow are required.

## Release

Run Python/R tests, full-source rebuild, result comparison and artifact verification; check mobile/desktop filters, downloads, evidence tables and R report; inspect attribution/coverage changes; review tracked files and Git author; then commit, publish and verify the remote checks, deployed content and listed contributors. Source publishers retain their data attribution separately from Git authorship.

## Source-refresh review gate

A same-source rebuild and a source update answer different questions. Strict `compare_results.py` remains mandatory for reproducibility on the same pinned archives. For a deliberately acquired candidate snapshot, preserve the released `reports/analysis.json` and compare:

```sh
python scripts/review_refresh.py /path/to/released-analysis.json /path/to/candidate-analysis.json --output /tmp/refresh-review.json
```

Exit 0 means no configured material change was detected; it never grants approval. Exit 2 means manual review is required; exit 1 means the comparison failed. Fingerprint changes always require revalidating the old baseline and audit frame. Operational flags include >5% changes in awards/value, >2 percentage points in attribution coverage, buyer population/support transitions and >500-point buyer HHI changes. These are review heuristics, not statistical tests. The report includes the largest HHI changes and before/after metrics even when a flag is not triggered.

Do not overwrite production source files to experiment with a candidate. Use a separate checkout; preserve prior sources and evidence. A newer procurement snapshot has not been acquired for v0.4. The shipped analysis still uses the three original pinned files.

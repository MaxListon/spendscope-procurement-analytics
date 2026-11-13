# Analytical contract — v0.2

## Universe and revision handling

Inputs are OCP snapshot 4370's 2022/2023/2024 Contracts Finder compiled-process archives, retrieved 12 November 2026. File year is a source partition, not a complete award-year register. Latest parsed release timestamp wins for repeated OCIDs across the selected files; conflicting same-timestamp snapshots fail. The current data has no repeated process snapshots. This is a latest-available snapshot analysis, not an as-known-at-the-time reconstruction.

Eligible awards have explicit active status, finite positive numeric GBP amounts and valid award dates in 2022–2024. Exclusions are evaluated in order: status, amount, currency, date. Every excluded record remains in the local warehouse. No currency or inflation conversion occurs.

`awards` has one row per process + award ID. Missing/repeated award IDs within a process fail. `suppliers` is an award/identity/name bridge with no allocated amount. Exact duplicate links are removed. Totals are never summed after a multi-supplier fan-out.

## Supplier identities and evidence decisions

Names use Unicode NFKC, case folding, punctuation-to-space and collapsed whitespace; legal suffixes remain. Empty names become unknown. Explicit generic labels and attachment instructions become placeholders, even when an identifier is present. Registered GB-COH/GB-CHC/GB-SC identifiers are format-checked; zero identifiers and malformed formats are held back. Format validation is not proof a registration belongs to the published company.

Nonempty, non-placeholder names without a recognized registration use exact normalized-name keys. These are provisional; unrelated organizations with the same name can merge, and aliases can split an entity. No automatic fuzzy matching or parent-company consolidation occurs.

Registered IDs with multiple normalized names are collision candidates. The versioned `identity_decisions.csv` approves only an exact `(registration key, normalized name)` pair when documented registration/name evidence supports it. These links become `registered-reviewed`, with a canonical display name; the source supplier name is retained. Rejected names become `review-rejected`; unresolved cases stay held back. Approved pairs do not rescue other aliases, typos or subsidiaries under the same ID.

The current evidence review contains 31 pairs across five selected Companies House records, with 11 approvals, two rejections and 18 unresolved cases. Accepted legal names include transparent Ltd/ Limited forms and a documented previous Softcat name. Short brands, typos and unclear subsidiary wording remain unresolved. This is a targeted, development-time evidence review, not a random labeled test set, independent human audit, or estimate of population precision/recall.

A deterministic name-only review queue is exported for further adjudication. It is not silently applied as matching ground truth.

Buyer keys combine published buyer ID and normalized buyer name. This avoids trusting source-system IDs alone but may split aliases or registered name changes. Buyers are publication identities, not fully consolidated organizations.

## Original notice review

The top 20 eligible award records by amount and award key were selected for live notice-page review on 12 November 2026. All 20 linked pages were observed after retrying initially incomplete page loads. `notice_checks.json` records the snapshot amount/title/count, page fields, observation status, interpretation, source URL and excerpt fingerprint.

Eleven observed discrepancies/stage ambiguities or attachment-list placeholders are held back from supplier attribution: superseded links, inconsistent supplier cardinality, missing award sections or title/context mismatch. These are unresolved evidence cases, not automatic corrections or proof the publisher is wrong. Live pages can differ from historical snapshots. Unavailable pages make no verification claim and do not alone cause attribution holdback. Eligible totals retain all source amounts.

Published framework values are not payments or guaranteed call-offs. Review confirms the £150 billion EEM0056 amount is displayed on its notice as a multi-supplier potential framework value; this does not validate it as distinct economic spending. Some source supplier fields explicitly refer readers to attachment lists, so a source supplier_count of one is not sufficient identity evidence.

## Concentration and coverage

Attribution requires exactly one supplier, a usable nonempty name, basis `registered`, `registered-reviewed` or `name-only`, and no notice holdback. HHI = 10,000 × sum of squared supplier shares of attributable award value. Top-one and top-five use that same denominator. These describe an observed buyer portfolio, not a legally defined market.

Coverage = attributable value / total eligible value. Default support is at least 30 attributable awards and 80% value coverage; nine scenarios cross award minima 10/30/50 with coverage minima 50%/80%/95%. These are screening choices, not official standards or completeness guarantees.

`buyer_evidence` recalculates HHI from registered and reviewed-registered links only; display requires at least 10 registered awards. It also shows the fraction of attributable value with registration evidence. The dashboard's optional registration-majority filter requires that fraction >=50% and at least 10 registered awards. This changes the selected comparison group, not the underlying source.

## R resampling and sensitivity

Within each category-year, resample complete OCIDs with replacement, keeping all of a selected process's awards with its sampled multiplicity. Compute an exactly equivalent weighted median; report 2.5th/97.5th percentile endpoints from 500 draws (R quantile type 7). Independent-award bootstrap endpoints remain in the output for comparison.

For the 30 supported buyer identities with greatest attributable value, R independently reproduces SQL HHI (relative tolerance 1e-8), then runs 300 process-clustered draws. It publishes independent-award endpoints, HHI without the largest award, HHI after buyer-specific 99th-percentile capping, process counts and registration-value shares.

Random generator: Mersenne-Twister / Inversion / Rejection; deterministic per-group seeds are exported. Awards are ordered by award key, process IDs sorted explicitly. Procurement processes are treated as independent within each stratum. Shared buyers, linked but differently identified call-offs, reporting selection and missing processes are not modeled. These are descriptive sensitivity intervals, not population confidence guarantees, forecasts or causal inference.

Capping/removal scenarios change assumptions and never rewrite the source. Year comparisons do not adjust inflation, policy changes or procurement mix.

## Reproducibility and limits

Pinned source fingerprints, versioned evidence decisions, code and generated artifacts are recorded in the build manifest. DuckDB uses a single aggregation thread for stable ordering. CI independently downloads the pinned files, installs a built Python wheel, runs R, and compares full analytical JSON with relative tolerance 1e-10 and absolute tolerance 1e-7; counts, schemas and labels must agree. Environment-specific manifests/charts are checked within each build rather than required to be byte-identical across platforms.

No payment dataset, realized savings, fraud model, verified supplier performance, comprehensive market coverage or external stakeholder validation is claimed. Bidder-count analysis and operational renewal recommendations remain deferred until coverage supports them.

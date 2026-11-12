# Methodology and analytical contract

## Universe and time

The input consists of the OCP 2022, 2023 and 2024 Contracts Finder compiled-process files from registry snapshot 4370, retrieved 12 November 2026. The file year is a source partition, not proof that every award in that year is covered. We resolve repeated OCIDs across selected partitions by latest parsed release timestamp. Conflicting snapshots at the same timestamp fail the build. This is a latest-available snapshot analysis, not an as-known-at-the-time reconstruction.

Within those processes, eligible awards have explicit active status, a finite positive numeric GBP amount and a valid award date in calendar years 2022–2024. There is no currency conversion or inflation adjustment. Each record is keyed by process ID plus award ID; missing or repeated award IDs within a compiled process fail rather than silently deduplicate.

Eligibility reasons are evaluated in order: non-active/missing status, invalid amount, non-GBP currency, invalid/out-of-scope award date. The quality report gives mutually exclusive counts using the first matching reason. Excluded records remain in the local warehouse.

## Grains and denominators

`awards`: one row per process + award ID. `suppliers`: one row per award + identity + normalized supplier name. Exact duplicate supplier links are removed. A bridge holds no allocated value. Eligible totals are computed from the award grain, never by summing after joining a multi-supplier bridge.

Supplier attribution requires one supplier identity/name pair and a nonempty normalized name. Registered GB-COH, GB-CHC and GB-SC identifiers are preferred when present. Numeric Companies House identifiers are zero-padded to eight characters. Other local publication identifiers are not treated as verified company identifiers. Name-only keys use Unicode NFKC, case folding, punctuation-to-space and collapsed whitespace; legal suffixes are retained. No fuzzy or probabilistic entity merges occur.

Registered IDs associated with more than one normalized name are marked `collision` across the selected data and excluded from attribution. This conservative rule can also exclude legitimate company renames. Missing-name supplier links are excluded regardless of registration evidence. Original publisher errors that already discarded a supplier cannot be reconstructed.

Buyer keys combine publication buyer ID with normalized buyer name. This avoids blindly trusting known source-system IDs but can split aliases/renames. No claim of complete organizational entity resolution is made.

## Concentration

For each buyer, aggregate attributable award values by supplier. Let s_j be each supplier's fraction of attributable value. HHI = 10,000 × sum(s_j²); top-one and top-five shares use the same denominator. Ties use stable supplier-key ordering. These metrics describe the observed buyer portfolio, not market concentration in a legal or economic market definition.

Value coverage = attributable value / total eligible value. A supported comparison has at least 30 attributable awards and 80% value coverage. Thresholds are analyst-selected screens, not evidence that remaining selection bias is absent. All buyers remain downloadable.

Awards attributed to a supplier are not supplier revenue. No group ownership consolidation, supplier performance, quality, fraud detection or measured savings is claimed.

## R statistical work

Category-year medians use 500 whole-award bootstrap resamples with replacement and seed 20261112. Displayed endpoints are 2.5th/97.5th percentile quantiles (R type 7). Category-year sums are recalculated after capping each award at that group's empirical 99th percentile and after excluding its largest award. These are sensitivity scenarios, not adjustments to reported data.

The top 30 supported buyers by attributable value receive 300 whole-award resamples with seed 20261113. R independently computes the original HHI and fails if it disagrees with SQL beyond relative tolerance 1e-8. It also reports HHI after removing the largest award and after a buyer-specific 99th percentile cap, and the fraction of value carrying registered-identifier evidence.

Independent award resampling does not model shared buyers, procurement-process dependence, reporting selection or unknown missing records. Intervals are descriptive resampling sensitivity, not guaranteed population confidence intervals or forecasts. Macro conditions, procurement rules, inflation and category mix confound year comparisons. No causal inference is performed.

## Source issues and deferred features

The publisher documents missing supplier names, shared supplier IDs and unrealistic dates. We retain disclosure of those limits. A source field can be syntactically valid and still wrong. We do not automatically label extreme but valid values as errors.

Bidder-count analysis, contract renewal recommendations, fuzzy aliases and Companies House enrichment are deferred pending coverage checks and manual validation. Contract periods are parsed and marked valid only when ordered and within 2000–2100, but they are not promoted to an operational renewal calendar.

A notice record is an economic commitment representation. Related lots, framework ceilings and overlapping awards can mean adding notice amounts overstates distinct economic expenditure. The dashboard says recorded award value throughout.

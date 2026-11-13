# Data dictionary

All monetary fields are nominal GBP recorded award commitments. No field represents an observed payment.

| Table / field | Definition |
|---|---|
| awards.award_key | Stable hash of OCID + award ID; unique accounting row |
| awards.ocid | Procurement-process identifier; R resampling cluster |
| awards.eligible | Active, finite positive GBP award dated 2022–2024 |
| awards.exclusion_reason | First matching status/amount/currency/date exclusion |
| awards.amount | Recorded award amount; retained through identity review |
| awards.supplier_count | Distinct published identity/name pairs, not guaranteed ultimate supplier count |
| awards.notice_review_status | not_reviewed, observed, unresolved, or not_observed |
| awards.notice_review_block | Evidence ambiguity prevents supplier attribution, not headline inclusion |
| suppliers.supplier_key | Registration key or provisional exact-name key |
| suppliers.source_supplier_name | Original published name before approved canonical display replacement |
| suppliers.identity_basis | registered, registered-reviewed, name-only, collision, review-rejected, placeholder, invalid-registration, unknown |
| buyer_concentration.attributed_value | Sum of eligible sole-supplier values after identity/evidence gates |
| buyer_concentration.total_value | All eligible award value for the buyer publication identity |
| buyer_concentration.value_coverage | attributed_value / total_value |
| buyer_concentration.hhi | 10,000 × sum(supplier value share²), using attributable subset |
| buyer_concentration.top1_share / top5_share | Largest/top-five supplier shares of attributable value |
| buyer_concentration.supported | >=30 attributable awards and >=80% value coverage |
| buyer_evidence.registered_value_share | Registered/reviewed-registered value / attributable value |
| buyer_evidence.registered_hhi | HHI on registration subset; null below 10 registered awards |
| comparison_thresholds | Supported buyer counts/value under nine threshold combinations |
| category_sensitivity.median_low/high | 500 process-clustered bootstrap percentile endpoints |
| buyer_sensitivity.hhi_low/high | 300 process-clustered HHI percentile endpoints |
| *_sensitivity.award_bootstrap_low/high | Independent-award alternative endpoints, not the main interval |
| *_sensitivity.processes / seed | Number of unique OCIDs and deterministic group seed |
| buyer_sensitivity.hhi_without_largest / hhi_capped | Removal/capping sensitivity scenarios |

`reports/` holds machine-readable outputs; `docs/reports/` holds published copies. Raw archives and the local DuckDB warehouse are excluded from Git. Evidence decisions under `data/review/` are tracked analysis inputs, not mutable dashboard user data.


Version 0.3 additions:

| Field / artifact | Meaning |
|---|---|
| suppliers.identity_basis = registry-audit-conflict | Observed registry-name disagreement held back from attribution |
| registry_audit.summary.confirmed_agreement_rate | Compatible records / all 40 sampled registration identities |
| confirmed_agreement_wilson | Wilson sampling interval with unobserved records not counted as confirmed |
| observed_only_agreement_rate | Compatible / observed records, presented with its different denominator |
| missing_evidence_bounds | Lowest/highest compatibility proportion under unknown registry outcomes; not a confidence interval |
| process_cluster | Connected component using only explicit, observed in-universe OCID links |
| process_linkage.json | Declaration, missing-identifier and resolvable-link coverage |
| category_sensitivity.buyer_bootstrap_low/high | Buyer-publication-identity resampling alternative |
| buyer_sensitivity.quarter_bootstrap_low/high | Calendar-quarter resampling alternative; null below four quarters |
| *_sensitivity.linked_bootstrap_low/high | Declared-component alternative; equals process assumption if partitions coincide |

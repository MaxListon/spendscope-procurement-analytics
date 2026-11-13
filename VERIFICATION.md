# Verification record — v0.2, 12 November 2026

## Completed locally

- Verified the three original source archives against pinned SHA-256 fingerprints and byte sizes.
- Rebuilt all 219,121 processes, 173,551 award records and 155,350 eligible awards; headline value/counts remain unchanged by identity review.
- Reviewed the linked notice pages for the 20 largest selected award records, retrying incomplete observations. Recorded 20 observed pages and 11 attribution holdbacks, including attachment-list placeholders and unresolved stage/context/cardinality discrepancies. This is targeted evidence review, not a population quality estimate.
- Checked five Companies House registrations and recorded 31 exact registration/name decisions: 11 accepted, two rejected and 18 unresolved. Original names remain in the warehouse; no unapproved alias is rescued by a shared ID.
- Added placeholder and registration-format validation. The current normalization identifies 193 placeholder links and 1,093 malformed registration links; 1,357 links carry exact reviewed name approvals.
- Nine SQL runtime contracts passed: uniqueness, linkage, attribution grain, count/value conservation, bounds, placeholder exclusion, notice holdbacks and no joint-award attribution.
- 59 Python tests passed, including targeted review counterexamples, known-answer concentration, invalid registrations, failed-build preservation, static dependencies, artifact integrity and analytical comparison failures.
- Executed R regression checks passed for HHI, weighted medians, literal-expansion equivalence and preservation of whole-process award multiplicities.
- Executed 500 procurement-process resamples per category-year and 300 per top supported buyer; independently reproduced SQL HHI and published independent-award alternatives.
- Installed the built v0.2 wheel in a separate fresh Python environment and completed another full offline data/R rebuild. The complete analytical JSON matched the committed baseline at relative tolerance 1e-10 / absolute tolerance 1e-7; all 59 tests and R regression checks passed again.
- Verified 22 analysis inputs and 47 generated artifacts, including versioned evidence and generated case studies. Published manifest copies agree.

## Remote and user review

GitHub checks and deployment are to be verified against the published release commit before completion is reported. External stakeholder/usability review and an independent labeled supplier validation have not been obtained; neither is simulated or claimed.

The system remains a reproducible research portfolio and static dashboard, not a live purchasing integration. Current limitations and the proposed development schedule are documented separately.

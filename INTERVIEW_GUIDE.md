# Explain SpendScope

## Problem

A manager wants to understand supplier dependency. Raw awards contain joint suppliers, placeholders and inconsistent registrations. A naive supplier join can multiply amounts or treat an attachment instruction as a real company. SpendScope keeps accounting grain separate from identity evidence and exposes the supported denominator.

## Three demonstrations

1. Open the Evidence review tab and show the real attachment-list placeholder finding. Explain why the amount stays in totals while its supplier attribution is removed.
2. Show the exact Softcat registration/name approvals, alongside a US-entity rejection and unresolved typos. Approval applies to an exact ID/name pair; it never validates every name sharing an ID.
3. Open the R note. Explain the OCID as resampling unit, reproduce HHI from supplier totals, compare process-clustered and independent-award intervals, then inspect largest-award removal sensitivity.

## Explain the engineering

Python ingests and normalizes; SQL owns business metric definitions; R independently cross-checks and quantifies sensitivity. Pinned source hashes, a build lock, staged computation, data contracts, failed-build preservation, artifact verification and gated deployment make the work reproducible. Per-file output replacement is not an atomic live-serving system.

## Explain limitations

Award commitments are not payments or supplier revenue. Framework ceilings and overlapping call-offs can dominate totals. Name-only matches remain provisional; registration formats are checked but not all company assignments independently verified. Buyer identities can split organizations. Process resampling does not recover unknown links or missing records. No misconduct, causal effects, operational savings or external stakeholder validation is claimed.

The evidence sample was selected for useful high-impact review, not random accuracy estimation. Do not quote a precision/recall percentage from it. The proposed multi-month roadmap is not elapsed development time. Finalize resume bullets using results you have reproduced and can defend.

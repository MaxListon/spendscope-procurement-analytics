# Random registration-evidence validation

The earlier 31 cases deliberately targeted useful identity problems. They are not used to claim matching accuracy. The v0.3 audit adds a separate frozen, reproducibly sampled frame.

## Sampling

- Unit: a distinct attributable, previously unreviewed GB-COH registration identity under v0.2 rules.
- Frame: 11,517 identities, deduplicated before selection; name-only identities are outside this frame.
- Sample: the 40 lowest SHA-256 values of `20261113-registration-audit-v1|supplier_key`, without replacement. The arbitrary seed does not denote a future observation date.
- Freeze: commit a5c5bd0, with a fingerprint of sorted identity/name/award-count facts. No replacement of inconvenient or unavailable cases.
- Evidence: Companies House legal-name and observed former-name fields, checked 12 November 2026. Public registry records may change over time. No personal director or contact information is published in the sample.

## Findings and uncertainty

| Outcome | Count |
|---|---:|
| Compatible current/former name evidence or transparent abbreviation | 36 |
| Observed name conflict | 2 |
| Registry record not observed | 2 |
| Total sampled | 40 |

Confirmed agreement is **36/40 = 90.0%**, with a Wilson 95% interval of **76.9%–96.0%**. Observed-only agreement is **36/38 = 94.7%**; this omits nonresponse and must not replace the full-denominator result. Missing-evidence bounds are **90%–95%**, which reflect unknown outcomes rather than sampling uncertainty.

A published Judy McDonald Consultancy record references a registration displaying DOOLING ELECTRICAL SERVICES LTD. An Insight Direct (UK) record references INSIGHT (UK) LIMITED, without observed former-name evidence explaining the difference. These discrepancies cause attribution holdbacks; they are not allegations of wrongdoing. Original records remain available.

## What the result does not prove

Legal-name consistency does not prove the published registration was the intended supplier, or that name-only identity matching is accurate. This is not a random sample of every source supplier link, an independent reviewer audit, or measured precision/recall of the full entity-resolution system. Labels were documented during project development. Subsequent remediation is not reported as independently measured post-remediation accuracy.

## Reproduction

`src/spendscope/validation.py` reconstructs and fingerprints the pre-remediation frame, reproduces the selected keys, checks evidence/rationale consistency, reports both denominators and applies only documented conflict holdbacks. `data/review/random_registry_audit.json` contains the frozen selection and observations. `reports/registry_audit.json` contains executed summary metrics and the sample. Future registry checks should be a new dated evidence version, not silent edits that hide missing or conflicting cases.
